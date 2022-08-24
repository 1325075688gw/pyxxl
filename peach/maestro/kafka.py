import json
import logging
import time
import typing
import uuid

from confluent_kafka import Producer

_LOGGER = logging.getLogger(__name__)

_p: Producer = None
_enable: bool = False

_TOPIC = "maestro"
_FIELD_EVENT_ID = "event_id"
_FIELD_EVENT_TIME = "event_time"
_FIELD_EVENT_TYPE = "event_type"


class MaestroException(Exception):
    pass


def init(broker_servers: str, enable: bool):
    global _p, _enable
    _enable = enable
    if _enable:
        _p = Producer({"bootstrap.servers": broker_servers})


def close():
    if _p:
        _p.flush()


def log(event: typing.Dict[str, typing.Any]):
    _check_and_fill_base_fields(event)

    if _p is None:
        _LOGGER.info(json.dumps(event))
    else:
        _p.produce(_TOPIC, json.dumps(event), callback=_delivery_report)
        _p.poll(0)


def _check_and_fill_base_fields(event: typing.Dict[str, typing.Any]):
    if _FIELD_EVENT_TYPE not in event:
        raise MaestroException(f"miss event_type field: {_FIELD_EVENT_TYPE}")

    if _FIELD_EVENT_ID not in event:
        event[_FIELD_EVENT_ID] = uuid.uuid4().hex
    if _FIELD_EVENT_TIME not in event:
        event[_FIELD_EVENT_TIME] = int(time.time())


def _delivery_report(err, msg):
    if err is not None:
        _LOGGER.error("Kafka Message delivery failed: {}".format(err))
    else:
        _LOGGER.debug(
            "Kafka Message delivered to {} [{}]".format(msg.topic(), msg.partition())
        )
