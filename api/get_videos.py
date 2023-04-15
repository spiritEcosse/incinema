from box import Box

from api.get_video_playback import GetVideoPlayback
from http_client import HttpClient
from models.video import Video


class GetVideos:
    url = "/title/get-videos"

    def __init__(self, items):
        self.items = items

    async def run(self):
        http_client = HttpClient.from_dict(
            {"urls": [f"{self.url}?tconst={item.id}" for item in self.items]}
        )
        responses = await http_client.run()
        for index, response in enumerate(responses):
            box = Box(response)
            self.items[index].video = Video(id=box.resource.videos[0].id.split('/')[-1])

        await GetVideoPlayback(items=self.items).run()
