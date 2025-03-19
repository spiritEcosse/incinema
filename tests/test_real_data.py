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
            'action',
            'mistery',
            'sci-fi',
            'survival',
            'series',
            'comedy',
            'action2',
            'series2',
            'sci-fi2',
        ]
        self._set = self.sets[-1]

    async def test_real_data_upload_set(self, *args):
        await gather_tasks(self.sets[-1:], upload_set)

    async def test_transform_trailers(self, *args):
        data = BASE_DIR_SETS / self._set / f'{self._set}.json'
        await handler(data)

    async def test_retrieve_and_save_all_movies(self, *args):
        await retrieve_and_save_all_movies()
