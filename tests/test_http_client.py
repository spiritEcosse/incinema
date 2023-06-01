import asyncio
from unittest import TestCase

from http_client import HttpClient


class TestDataReal(TestCase):
    maxDiff = None
    urls = [
    ]

    def test_http_client(self):
        http_client = HttpClient.from_dict(
            {"urls": self.urls * 50, "server": ""}
        )
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(http_client.run())

        for index, response in enumerate(responses):
            print(index, response)
