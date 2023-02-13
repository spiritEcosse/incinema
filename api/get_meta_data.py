import asyncio
import json

import boto3
from box import Box
from ordered_set import OrderedSet

from api.get_videos import GetVideos
from http_client import HttpClient
from models.initial_data import InitialData, ParseInitialData
from models.video import Item
from settings import STATE_MACHINE_ARN


class GetMetaData:
    url = "/title/get-meta-data"
    serializer = ParseInitialData

    def __init__(self, event: dict):
        self.body = event['body']
        self.items = []
        self.serializer_object = self.serializer.from_dict({"string": self.body}).from_string()
        self.step_function = boto3.client('stepfunctions')

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.wrapper_run())

    async def wrapper_run(self):
        response = Box(await Item.batch_get_item(ids=self.serializer_object.ids_items()))
        existing_ids = OrderedSet([item.id for item in response.Responses.item])
        ids_to_process = self.serializer_object.ids_to_set() - existing_ids

        if ids_to_process:
            http_client = HttpClient.from_dict(
                {"urls": [f"{self.url}{InitialData.items_id_to_query_string(ids_to_process)}"]}
            )
            for response in await http_client.run():
                for key, value in response.items():
                    box = Box(value)
                    self.items.append(
                        Item(
                            id=key,
                            title=box.title.title,
                            titleType=box.title.titleType,
                            year=box.title.year,
                            duration=box.title.runningTimeInMinutes,
                            rating=box.ratings.rating,
                        )
                    )

            await GetVideos(items=self.items).run()
            await Item.save(self.items)

        await self.run_executions()

    async def run_executions(self):
        for item in self.items:
            self.step_function.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=json.dumps({"id": item.id})
            )
