import json
import logging
import typing
from confluent_kafka import Producer
from peach.misc import dt


_LOGGER = logging.getLogger(__name__)


class ProducerClient:
    def __init__(self):
        self._initialized = False
        self._app = None
        self._config = None
        self._producer = None

    def init(self, app: str, config: typing.Dict):
        self._app = app
        self._config = config
        self._producer = Producer(self._config)
        self._initialized = True

    def send(self, topic: str, namespace: str, data: typing.Dict, key: str = None):
        if not self._initialized:
            _LOGGER.info("kafka producer is not initialized yet")
            return

        self._producer.produce(
            topic,
            self._fill_data(namespace, data),
            key,
            callback=self._delivery_callback,
        )
        self._producer.poll(0)

    def _fill_data(self, namespace: str, data: typing.Dict):
        return json.dumps(
            {
                "ts": dt.now_mts(),
                "trace": None,
                "app": self._app,
                "np": namespace,
                "data": data,
            }
        )

    def _delivery_callback(self, err, msg):
        if err:
            _LOGGER.error("kafka message failed delivery: {}".format(err))
        else:
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug(
                    "Produced event to topic {topic}, part: {part}: key = {key} value = {value:12}".format(
                        topic=msg.topic(),
                        part=msg.partition(),
                        key=msg.key().decode("utf-8") if msg.key() else "None",
                        value=msg.value().decode("utf-8"),
                    )
                )

    def close(self):
        if not self._initialized:
            return

        self._producer.flush(5)


producer_client = ProducerClient()
