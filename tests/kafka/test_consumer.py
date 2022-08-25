import os
import typing
from peach.kafka import producer
from peach.kafka.consumer import listener, start_consumer


@listener(
    topics=["peach_test"],
    group_id="group_id_0",
    namespaces=["ns"],
)
def print_event0(event: typing.Dict):
    print(f"===== 0 - event: {event}")
    raise Exception("0 - hello...")


@listener(
    topics=["peach_test"],
    group_id="group_id_1",
    namespaces=["ns"],
)
def print_event1(event: typing.Dict):
    print(f"===== 1 - event: {event}")


def test_consume():
    if True:
        return
    producer.producer_client.init(
        os.getenv("APP_NAME", "Kafka"), {"bootstrap.servers": "127.0.0.1:9092"}
    )
    start_consumer("127.0.0.1:9092")
