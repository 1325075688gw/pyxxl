from .producer import producer_client
from .consumer import listener  # noqa F401


send = producer_client.send
