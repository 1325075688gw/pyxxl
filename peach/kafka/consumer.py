from collections import defaultdict
from dataclasses import dataclass
from functools import wraps
import json
import logging
import os
import signal
from threading import Barrier, Thread
import time
import typing

from django import db
from confluent_kafka import Consumer

from peach.kafka import producer


_LOGGER = logging.getLogger(__name__)

# The maximum number of event processing failures, beyond this number events go to `DEAD_TOPIC`.
MAX_FAILURES = 3
# The topic is used for retry processing of failured events.
FAILURE_TOPIC = os.getenv("APP_NAME", "Kafka") + "_failure_topic"
# The group_id is specially used to process retry failure event.
FAILURE_GROUP_ID = os.getenv("APP_NAME", "Kafka") + "_failure_consumer"
# The topic is used to receive the finalize failed events.
DEAD_TOPIC = os.getenv("APP_NAME", "Kafka") + "_dead_topic"
# Exit flag for each sub process
SHUTDOWN_SIGN = False
# The maximum sleep time(second) when encountering a failure to process an event.
MAX_DELAY_SECONDS = 10


@dataclass
class ListenerItem:
    topics: typing.List[str]
    func: typing.Callable
    namespaces: typing.List[str]


listener_container: typing.Dict[str, typing.List[ListenerItem]] = defaultdict(list)


def listener(
    topics: typing.List[str], group_id: str, namespaces: typing.List[str] = None
):
    assert len(topics) > 0
    assert group_id

    def decorator(func):
        _LOGGER.info(
            f"kafka consumer registered the func: {func.__name__} associated to topics: {topics}"
        )
        listener_container[group_id].append(ListenerItem(topics, func, namespaces))

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class ProcessorThread(Thread):
    def __init__(
        self, group_id: str, bootstrap_servers: typing.List[str], counter: Barrier
    ):
        super().__init__()
        self._failure_count = 0  # consecutive failures count
        self._counter = counter
        self._group_id = group_id
        self._is_failure_processor = self._group_id == FAILURE_GROUP_ID
        self._config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "on_commit": self._on_committed,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        self._topics = (
            [FAILURE_TOPIC] if self._is_failure_processor else self._merge_topics()
        )
        self._consumer = Consumer(self._config)
        self._consumer.subscribe(self._topics, on_assign=self._on_assigned)
        _LOGGER.info(
            "kafka consumer {} subscribe topic {}".format(self._consumer, self._topics)
        )

    def _merge_topics(self) -> typing.List[str]:
        topics = []
        for item in listener_container[self._group_id]:
            topics.extend(item.topics)
        return list(set(topics))

    def run(self):
        try:
            _LOGGER.info(f"starting kafka processor, group_id: {self._group_id}")
            self._process()
        except Exception:
            _LOGGER.exception(
                f"kafka consumer process was failed, group_id: {self._group_id}"
            )
        finally:
            _LOGGER.info(
                f"kafka consumer process had exited, group_id: {self._group_id}"
            )
            self._counter.wait()

    def _process(self):
        while True:
            if SHUTDOWN_SIGN:
                _LOGGER.info(
                    f"kafka consumer will exit gracefully, group_id: {self._group_id}"
                )
                self._consumer.close()
                break

            msg = self._consumer.poll(5)
            if msg is None:
                # _LOGGER.debug("kafka partition drained out")
                continue
            error = msg.error()
            if error:
                _LOGGER.error(
                    f"kafka get msg fail, topic: {msg.topic()}, {error.code()}, {msg.partition()}, {msg.offset()}"
                )
                continue

            payload = msg.value()
            topic = msg.topic()
            key = msg.key()
            if not payload:
                _LOGGER.info("kafka get msg without data")
                self._consumer.commit(msg)
                continue

            try:
                payload = payload.decode()
                event = json.loads(payload)
            except Exception:
                _LOGGER.error(f"kafka invalid json format: {payload}")
                self._consumer.commit(msg)
                continue

            try:
                db.close_old_connections()
                for listener in self._route_listeners(event, topic):
                    listener.func(event)
                self._on_successed()
            except Exception as ex:
                self._process_exception(ex, event, topic, key)
                self._on_failured()
            finally:
                self._consumer.commit(msg)

    def _route_listeners(
        self, event: typing.Dict, topic: str
    ) -> typing.Iterator[ListenerItem]:
        no_listener = True
        group_id = event.get("original_group_id", self._group_id)
        topic = event.get("original_topic", topic)

        if group_id not in listener_container:
            _LOGGER.error(f"kafka process has no group_id to match event: {event}")
            return

        for listener in listener_container[group_id]:
            if topic in listener.topics and (
                not listener.namespaces or event["np"] in listener.namespaces
            ):
                no_listener = False
                yield listener
        if no_listener:
            _LOGGER.debug(
                f"kafka not process event, func: {listener.func.__name__}, event: {event}"
            )

    def _process_exception(
        self, ex: Exception, event: typing.Dict, topic: str, key: str
    ):
        _LOGGER.exception(
            f"kafka process event failed: {event} on topic: {topic} by group_id: {self._group_id}"
        )

        retries = event.get("retries", 0)
        original_topic = event.get("original_topic", topic)
        assert original_topic not in [DEAD_TOPIC, FAILURE_TOPIC]
        original_group_id = event.get("original_group_id", self._group_id)
        assert original_group_id != FAILURE_GROUP_ID

        if retries > MAX_FAILURES:
            producer.producer_client.send_filled_data(DEAD_TOPIC, event, key)
            return

        event["retries"] = retries + 1
        event["original_topic"] = original_topic
        event["original_group_id"] = original_group_id
        producer.producer_client.send_filled_data(FAILURE_TOPIC, event, key)

    def _on_successed(self):
        self._failure_count = 0

    def _on_failured(self):
        self._failure_count += 1
        delay = min(self._failure_count, MAX_DELAY_SECONDS)
        time.sleep(delay)

    def _on_assigned(self, consumer, partitions):
        for p in partitions:
            _LOGGER.info("on assigned, partition {} to consumer {}".format(p, consumer))

    def _on_committed(self, error, partitions):
        if error is None:
            _LOGGER.debug("commit succeeded")
            for p in partitions:
                _LOGGER.debug(
                    "topic: {}, partition: {}, current committed offset: {}".format(
                        p.topic, p, p.offset
                    )
                )
        else:
            _LOGGER.error("commit failed, reason: {}".format(error))
            for p in partitions:
                _LOGGER.error(
                    "topic: {}, partition: {}, commit error: {}".format(
                        p.topic, p.partition, p.error
                    )
                )


def start_consumer(bootstrap_servers: typing.List[str]):

    _LOGGER.info("kafka is starting main processor ... ")
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Total = Size of worker processor + One for failure processor + One for main processor
    counter = Barrier(len(listener_container) + 2)

    # worker processors
    for group_id, _ in listener_container.items():
        procesor = ProcessorThread(group_id, bootstrap_servers, counter)
        procesor.start()

    # failure processor
    procesor = ProcessorThread(FAILURE_GROUP_ID, bootstrap_servers, counter)
    procesor.start()

    counter.wait()
    _LOGGER.info("kafka exited in main processor")


def handle_signal(signalnum, frame):
    pid = os.getpid()
    _LOGGER.info(
        "consumer process {} receives signal {}, sets exit flag".format(pid, signalnum)
    )
    global SHUTDOWN_SIGN
    SHUTDOWN_SIGN = True
