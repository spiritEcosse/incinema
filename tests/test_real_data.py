from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import pytest

from main import handler, gather_tasks, upload_set, retrieve_and_save_all_movies
from settings import BASE_DIR_SETS


@pytest.mark.skip(reason="This test is real data")
@patch('boto3.client')
class TestDataReal(IsolatedAsyncioTestCase):
    maxDiff = None

    async def asyncSetUp(self) -> None:
        self.sets = [
            'series2',
            'action',
            'comedy',
            'mistery',
            'sci-fi',
            'survival',
            'series',
        ]
        self._set = self.sets[1]

    async def test_real_data_upload_set(self, *args):
        await gather_tasks(self.sets[1:2], upload_set)

    async def test_real_data(self, *args):
        data = BASE_DIR_SETS / self._set / f'{self._set}.json'
        await handler(data)

    async def test_retrieve_and_save_all_movies(self, *args):
        await retrieve_and_save_all_movies()
