import os
from django.apps import AppConfig
from django.conf import settings

from peach.kafka import producer


class KafkaConfig(AppConfig):
    name = "peach.kafka"

    def ready(self):
        bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS

        producer.producer_client.init(
            os.getenv("APP_NAME", "Kafka"), {"bootstrap.servers": bootstrap_servers}
        )
