import asyncio
import os
from unittest import TestCase

from main import handler
from models.video import Item
from settings import BASE_DIR


class TestDataReal(TestCase):
    maxDiff = None

    def setUp(self, *args, **kwargs) -> None:
        with open(os.path.join(BASE_DIR, "data1.csv")) as file_:
            data = file_.read()

        self.string = data
        # for i, item in enumerate(data.split('#')):
        #     if i == 0:
        #         self.string = item
        #     if i == 7:
        #         self.string += f"#{item}"

    # def test_real_data(self, *args):
    #     loop = asyncio.get_event_loop()
    #     loop.run_until_complete(Item.delete_all_items())
    #     handler({"body": self.string}, {})

    def test_real_data_full(self, *args):
        handler({"body": self.string}, {})
