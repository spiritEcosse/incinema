import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
import async_timeout

from serializer import DataClassJSONSerializer
from settings import HOST_API_URL, HOST_API_TOKEN


@dataclass
class HttpClient(DataClassJSONSerializer):
    """
    A class representing a http_client

    >>> http_client = HttpClient.from_dict({"urls": ['example.com/1', 'example.com/2'], "token": "1234567890", "server": "example.com/3"})
    >>> http_client.urls
    ['example.com/1', 'example.com/2']
    >>> http_client.server
    'example.com/3'
    >>> http_client.token
    '1234567890'
    >>> http_client._header
    {'X-RapidAPI-Key': '1234567890', 'X-RapidAPI-Host': 'example.com/3'}

    """
    urls: list
    server: str = HOST_API_URL
    token: str = HOST_API_TOKEN

    @property
    def server_name(self) -> str:
        """
        >>> http_client = HttpClient.from_dict({"urls": ['example.com/1'], "token": "1234567890", "server": "example.com/3"})
        >>> http_client.server_name
        'https://example.com/3'
        """
        return f"https://{self.server}"

    @property
    def _header(self, *args, **kwargs) -> dict:
        """A property to get the http_client header

        >>> http_client = HttpClient.from_dict({"urls": [], "server": 'example.com', "token": '1234567890'})
        >>> http_client._header
        {'X-RapidAPI-Key': '1234567890', 'X-RapidAPI-Host': 'example.com'}
        """
        return {
            'X-RapidAPI-Key': self.token,
            'X-RapidAPI-Host': self.server
        }

    async def run(self):
        """Start point for non async context"""

        return await self.gather_tasks()

    async def request(self, url, response) -> Any:
        """A coroutine to request a http_client"""
        # raise Exception(inspect.isawaitable(response.json()))

        return await response.json()

    async def get_response(self, index, url, session):
        await asyncio.sleep(0.3 * index)
        async with async_timeout.timeout(5000):
            async with session.get(url) as response:
                return await self.request(url, response)

    async def gather_tasks(self):
        async with aiohttp.ClientSession(self.server_name, headers=self._header) as session:
            tasks = (self.get_response(index, url, session) for index, url in enumerate(self.urls, start=1))
            return await asyncio.gather(*tasks)
