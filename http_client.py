import asyncio
import logging
import random
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Optional

import aiohttp
from propcache import cached_property

from serializer import DataClassJSONSerializer
from settings import HOST_API_URL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    headers: dict = field(default_factory=dict)
    token: Optional[str] = ""
    sleep: bool = False
    json: bool = True

    @property
    def server_name(self) -> str:
        """
        >>> http_client = HttpClient.from_dict({"urls": ['example.com/1'], "token": "1234567890", "server": "example.com/3"})
        >>> http_client.server_name
        'https://example.com/3'
        """
        return f"https://{self.server}"

    @cached_property
    def _headers(self, *args, **kwargs) -> dict:
        """A property to get the http_client header

        >>> http_client = HttpClient.from_dict({"urls": [], "server": 'example.com', "token": '1234567890'})
        >>> http_client._headers
        {'Authorization': 'Bearer 1234567890'}
        """
        headers = {}
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        headers.update(self.headers)
        return headers

    async def run(self):
        """Start point for non async context"""
        return await self.gather_tasks()

    async def request(self, url, response) -> Any:
        """A coroutine to request a http_client"""
        if self.json:
            data = await response.json()
        else:
            data = await response.text()
        if response.status != HTTPStatus.OK:
            raise RuntimeError(f"url: {url}, status: {response.status}, {data}")
        return data

    async def get_response(self, url, session):
        if self.sleep:
            # Add random delay between 1-3 seconds to avoid being blocked
            await asyncio.sleep(random.uniform(1, 3))

        async with asyncio.timeout(20):
            response = await session.get(url)
            return await self.request(url, response)

    async def gather_tasks(self):
        async with aiohttp.ClientSession(self.server_name, headers=self._headers) as session:
            tasks = (self.get_response(url, session) for url in self.urls)
            return await asyncio.gather(*tasks)
