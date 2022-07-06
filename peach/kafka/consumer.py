from collections import defaultdict
from dataclasses import dataclass
from functools import wraps
import json
import logging
from threading import Barrier, Thread
import typing

from confluent_kafka import Consumer


_LOGGER = logging.getLogger(__name__)

shutdown = False  # exit flag for each sub process


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
        listener_container[group_id].append(ListenerItem(topics, func, namespaces))

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class ProcessorThread(Thread):
    def __init__(self, group_id: str, bootstrap_servers: str, counter: Barrier):
        super().__init__()
        self._counter = counter
        self._group_id = group_id
        self._listener_item_list = listener_container[group_id]
        self._config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "on_commit": self._on_committed,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        self._topics = self._merge_topics()
        self._consumer = Consumer(self._config)
        self._consumer.subscribe(self._topics, on_assign=self._on_assigned)
        _LOGGER.info(
            "kafka consumer {} subscribe topic {}".format(self._consumer, self._topics)
        )

    def _merge_topics(self) -> typing.List[str]:
        topics = []
        for item in self._listener_item_list:
            topics.extend(item.topics)
        return list(set(topics))

    def run(self):
        try:
            self._process()
        except Exception:
            global shutdown
            shutdown = True
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
            if shutdown:
                _LOGGER.info(
                    f"kafka consumer will exit gracefully, group_id: {self._group_id}"
                )
                self._consumer.close()
                break

            msg = self._consumer.poll(5)
            if msg is None:
                _LOGGER.debug("kafka partition drained out")
                continue
            error = msg.error()
            if error:
                _LOGGER.error(
                    f"kafka get msg fail, topic: {msg.topic()}, {error.code()}, {msg.partition()}, {msg.offset()}"
                )
                continue

            payload = msg.value()
            topic = msg.topic()
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
                not_processed = True
                for listener in self._listener_item_list:
                    if topic in listener.topics and (
                        not listener.namespaces or event["np"] in listener.namespaces
                    ):
                        not_processed = False
                        listener.func(event)
                if not_processed:
                    _LOGGER.debug(
                        f"kafka not process event, func: {listener.func.__name__}, event: {event}"
                    )
            except Exception:
                _LOGGER.exception(f"kafka process event failed: {event}")
                raise
            self._consumer.commit(msg)

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
