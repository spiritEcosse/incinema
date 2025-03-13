from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import pytest

from main import handler
from settings import BASE_DIR_SETS


@pytest.mark.skip(reason="This test is real data")
@patch('boto3.client')
class TestDataReal(IsolatedAsyncioTestCase):
    maxDiff = None

    async def asyncSetUp(self) -> None:
        # self.data1 = Path(f"{BASE_DIR_SETS}/action/action.json")
        self.data = Path(f"{BASE_DIR_SETS}/adventure/adventure.json")
        # self.data3 = Path(f"{BASE_DIR_SETS}/comedy/comedy.json")
        # self.data4 = Path(f"{BASE_DIR_SETS}/mistery/mistery.json")
        # self.data5 = Path(f"{BASE_DIR_SETS}/series/series.json")
        # self.data6 = Path(f"{BASE_DIR_SETS}/survival/survival.json")
        # self.data7 = Path(f"{BASE_DIR_SETS}/sci-fi/sci-fi.json")
        # self.all_data = [self.data1, self.data2, self.data3, self.data4, self.data5, self.data6, self.data7]
        # self.data = Path(f"{BASE_DIR_SETS}/series2/series2.json")

    async def test_real_data(self, *args):
        await handler(self.data)
