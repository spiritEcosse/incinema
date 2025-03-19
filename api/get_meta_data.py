import logging
import os
import subprocess
from multiprocessing import Pool
from pathlib import Path

from box import Box
from ordered_set import OrderedSet

from api.get_videos import GetVideos
from api.video_editor import make_trailer
from http_client import HttpClient
from models.initial_data import InitialData
from models.video import Item
from settings import BASE_DIR_MOVIES, HOST_API_TOKEN, WORKERS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GetMetaData:
    url = "/3/movie/{}?language=en-US"
    serializer = InitialData

    def __init__(self, data: dict):
        self.data = data
        self.items = []
        self.serializer_object = self.serializer.from_dict(self.data)

    async def run(self):
        await self.wrapper_run()

    async def wrapper_run(self):
        response = Box(await Item.batch_get_item(ids=self.serializer_object.ids_items()))
        existing_ids = OrderedSet([item.id for item in response.Responses.item])
        self.items = [Item.from_dict(item) for item in response.Responses.item]

        # Find items with videos from original items and add them if not already included
        items_with_videos = [item for item in self.serializer_object.items if item.video]
        for item in items_with_videos:
            if item.id not in existing_ids:
                self.items.append(item)

        # Now calculate ids_to_process (excluding both existing IDs and IDs with videos)
        ids_with_videos = OrderedSet([item.id for item in items_with_videos])
        ids_to_process = OrderedSet(self.serializer_object.ids_to_set() - existing_ids - ids_with_videos)

        for item in self.serializer_object.items:
            (BASE_DIR_MOVIES / item.title_to_dir()).mkdir(parents=True, exist_ok=True)

        if ids_to_process:
            http_client = HttpClient.from_dict(
                {"urls": [f"{self.url.format(_id)}" for _id in ids_to_process], 'token': HOST_API_TOKEN, 'json': True}
            )
            for response in await http_client.run():
                key = response['imdb_id']
                box = Box(response)
                item = self.serializer_object.items_map[key]

                # Update only the necessary fields from the response
                item.year = int(box.release_date.split("-")[0])
                item.duration = box.runtime
                item.rating = round(box.vote_average, 1)

                # Add the updated item to self.items
                self.items.append(item)

            await GetVideos(items=self.items, ids=ids_to_process).run()
        await Item.save(self.items)
        self.run_executions()
        await self.do_set()

    def run_executions(self):
        workers = min(WORKERS, len(self.items))
        with Pool(workers) as p:
            p.map(make_trailer, [item for item in self.items])

    async def do_set(self):
        set_folder = self.serializer_object.title_to_dir()
        logger.info(f"do_set : {set_folder}")
        path_to_set = BASE_DIR_MOVIES / "sets" / set_folder
        path_to_set.mkdir(parents=True, exist_ok=True)
        os.chdir(path_to_set)

        files = [item.title_to_dir() for item in self.items]

        if len(files) != 10:
            raise RuntimeError("files must be 10")

        for movie_title in files:
            full_path_movie = Path(BASE_DIR_MOVIES, movie_title)
            final_movie = full_path_movie / "final.mp4"
            subprocess.check_output(f"ln -sf {final_movie} {path_to_set}/{movie_title}.mp4", shell=True)
