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
        # self.data = Path(f"{BASE_DIR_SETS}/adventure/adventure.json")
        # self.data = Path(f"{BASE_DIR_SETS}/adventure/adventure.json")
        self.data = Path(f"{BASE_DIR_SETS}/comedy/comedy.json")
        # self.data = Path(f"{BASE_DIR_SETS}/survival/survival.json")

    async def test_real_data(self, *args):
        await handler(self.data)
