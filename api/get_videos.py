import logging
import os

from box import Box

from http_client import HttpClient
from models.video import Video
from settings import BASE_DIR_MOVIES

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GetVideos:
    url = "/3/movie/{}/videos?language=en-US"
    size = 1080

    # sizes = [1080, 720]

    def __init__(self, items):
        self.items = items

    async def run(self):
        http_client = HttpClient.from_dict(
            {"urls": [f"{self.url.format(item.id)}" for item in self.items]}
        )
        responses = await http_client.run()
        for index, response in enumerate(responses):
            box = Box(response)
            # Find best available quality video
            best_video = None
            # for size in self.sizes:
            #     if best_video:
            #         break
            for video in box.results:
                if video.site == "YouTube" and video.size >= self.size and video.type == "Trailer":
                    print(
                        f"id: {self.items[index].id}, title: {self.items[index].title.en}, url: https://www.youtube.com/watch?v={video.key}")

            for video in box.results:
                if video.site == "YouTube" and video.size >= self.size and video.type == "Trailer":
                    best_video = video
                    break

            if best_video:
                _id = best_video.key
                self.items[index].video = Video(id=_id, url=f'https://www.youtube.com/watch?v={_id}')
            elif not os.path.isfile(os.path.join(BASE_DIR_MOVIES, self.items[index].title_to_dir(), "original.mp4")):
                raise RuntimeError(
                    f"id: {self.items[index].id}, title: {self.items[index].title.en}, no compatible URL found {box}")
