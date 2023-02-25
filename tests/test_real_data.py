import asyncio
from unittest import TestCase
from unittest.mock import patch

from main import handler
from models.video import Item


@patch('boto3.client')
class TestDataReal(TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.item_id_1 = "tt4154756"
        self.item_id_2 = "tt0050825"
        self.item_id_3 = "tt15325794"
        # self.string = f"Suspense, Survey .1.\n1.Вышка | {self.item_id_1} \n2.Джунгли | {self.item_id_2} \n3.Новое | {self.item_id_3}\n"
        self.string = f"Suspense, Survey .1.\n1.Winter Is Coming | tt1480055 \n2.The Kingsroad | tt1668746 \n3.Lord Snow | tt1829962\n4.Cripples, Bastards, and Broken Things | tt1829963\n5.The Wolf and the Lion | tt1829964\n6.A Golden Crown | tt1837862\n7.You Win or You Die | tt1837863\n8.The Pointy End | tt1837864\n9.Baelor | tt1851398\n10.Fire and Blood | tt1851397\n"

    def test_real_data(self, *args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(Item.delete_all_items())
        handler({"body": self.string}, {})
