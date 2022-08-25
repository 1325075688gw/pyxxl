import os
from peach.kafka import producer


def test_producer():
    if True:
        return
    producer.producer_client.init(
        os.getenv("APP_NAME", "Kafka"), {"bootstrap.servers": "127.0.0.1:9092"}
    )

    producer.producer_client.send("peach_test", "ns", {"uid": 1000})
