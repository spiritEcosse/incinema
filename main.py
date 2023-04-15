# This is a sample Python script.
import logging
from api.get_meta_data import GetMetaData

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict, context: {}) -> dict:
    GetMetaData(event=event).run()
    return {}
