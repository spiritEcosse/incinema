import asyncio
import logging
import os
import subprocess
from multiprocessing import Pool
from pathlib import Path

from box import Box
from ordered_set import OrderedSet

from api.get_videos import GetVideos
from api.video_editor import VideoEditor, video_editor
from http_client import HttpClient
from models.initial_data import InitialData, ParseInitialData
from models.video import Item, Description, Title
from settings import BASE_DIR


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GetMetaData:
    url = "/title/get-meta-data"
    serializer = ParseInitialData

    def __init__(self, event: dict):
        self.body = event['body']
        self.items = []
        self.serializer_object = self.serializer.from_dict({"string": self.body}).from_string()

    def run(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.wrapper_run())

    async def wrapper_run(self):
        response = Box(await Item.batch_get_item(ids=self.serializer_object.ids_items()))
        response_ = response.Responses.item if response else []
        items = [Item.from_dict(item.to_dict()) for item in response_]
        existing_ids = OrderedSet([item.id for item in items])
        ids_to_process = self.serializer_object.ids_to_set() - existing_ids
        items_to_dict = self.serializer_object.items_to_dict()
        # ids_to_process = OrderedSet(["tt5294522", "tt5052448", "tt4052882", "tt5670152", "tt15325794", "tt6805938", "tt3758172", "tt13223398", "tt10081762", "tt2737304"])
        # ids_to_process = OrderedSet(["tt10081762"])

        if ids_to_process:
            http_client = HttpClient.from_dict(
                {"urls": [f"{self.url}{InitialData.items_id_to_query_string(ids_to_process)}"]}
            )
            for response in await http_client.run():
                for key, value in response.items():
                    box = Box(value)
                    if box.title.titleType == 'movie':
                        self.items.append(
                            Item(
                                id=key,
                                title=Title(en=box.title.title, ru=items_to_dict[key].title),
                                titleType=box.title.titleType,
                                year=box.title.year,
                                duration=box.title.runningTimeInMinutes,
                                background_audio=items_to_dict[key].background_audio,
                                rating=box.ratings.rating,
                                description=Description(ru=items_to_dict[key].description) if items_to_dict[key].description else None
                            )
                        )

            await GetVideos(items=self.items).run()
            await Item.save(self.items)
        self.items.extend(items)
        await self.run_executions()
        await self.do_set()

    async def run_executions(self):
        with Pool(10) as p:
            print(p.map(video_editor, [item for item in self.items]))

    def write_description(self):
        file_list_descriptions = os.path.join(BASE_DIR, "sets", "data1_descriptions.txt")
        with open(file_list_descriptions, 'w') as f:
            for item in self.items:
                f.write(f"{item.to_string()}\n\n")

    async def do_set(self):
        file_name = "data3"
        Path(os.path.join(BASE_DIR, "sets")).mkdir(exist_ok=True)
        logger.info(f"do_set : {file_name}")
        self.write_description()

        files = [(os.path.join(BASE_DIR, item.title_to_dir), item.title_to_dir) for item in self.items]
        # file_list_concat = os.path.join(BASE_DIR, "sets", f"{file_name}.txt")
        file_concat = os.path.join(BASE_DIR, "sets", f"{file_name}.mp4")
        data = []

        if not files:
            raise Exception("files is empty.")
        # data.append(f"{os.path.join(BASE_DIR, 'sets')}/silence-1.mp4")
        Path(os.path.join(BASE_DIR, "sets")).mkdir(exist_ok=True)
        # with open(file_list_concat, 'w') as f:
        for index, folder_data in enumerate(files, 1):
            full_path, folder_name = folder_data[0], folder_data[1]
            # data.append(f"{os.path.join(BASE_DIR, 'sets')}/silence-{index}.mp4")
            data.append(f"{full_path}/video_background_audio.mp4")
            # f.write(f"file '{os.path.join(BASE_DIR, 'sets')}/{index}.mp4'\n")
            # f.write(f"file '{full_path}/video_background_audio.mp4'\n")
            subprocess.check_output(f"cp -f {full_path}/video_background_audio.mp4 {os.path.join(BASE_DIR, 'sets', f'{folder_name}.mp4')}", shell=True)

        # subprocess.check_output(f"rm -f {file_concat}", shell=True)
        if data:
            files_concat = " -cat ".join(data)
            subprocess.check_output(f"MP4Box -cat {files_concat} -new {file_concat}", shell=True)
            # subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', file_list_concat, "-c", "copy", file_concat])
