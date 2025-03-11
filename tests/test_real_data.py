from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import pytest

from main import handler, data


@pytest.mark.skip(reason="This test is real data")
@patch('boto3.client')
class TestDataReal(IsolatedAsyncioTestCase):
    maxDiff = None

    async def asyncSetUp(self) -> None:
        self.item_id_1 = "tt4154756"
        self.item_id_2 = "tt0050825"
        self.item_id_3 = "tt15325794"
        self.data = {'title': data['title'], 'items': data['items']}

    async def test_real_data(self, *args):
        # loop.run_until_complete(Item.delete_all_items())
        await handler(self.data)
