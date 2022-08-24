import json
import logging
import requests

_LOGGER = logging.getLogger(__name__)


def get(*args, **kwargs):
    return requests.get(*args, **kwargs)


def get_json(*args, **kwargs):
    resp = get(*args, **kwargs)
    try:
        return json.loads(resp.content)
    except Exception:
        _LOGGER.exception(f"requests fail, args: f{args}, kwargs: {kwargs}")
        raise


def post(*args, **kwargs):
    return requests.post(*args, **kwargs)
