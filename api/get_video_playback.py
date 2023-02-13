from box import Box

from http_client import HttpClient


class GetVideoPlayback:
    url = "/title/get-video-playback"
    qualities = ['1080p', '720p']
    formats = ['video/mp4']

    def __init__(self, items):
        self.items = items

    async def run(self):
        http_client = HttpClient.from_dict(
            {"urls": [f"{self.url}?viconst={item.video.id}" for item in self.items if item.titleType == 'movie']}
        )
        for index, response in enumerate(await http_client.run()):
            if self.items[index].titleType == 'movie':
                box = Box(response)
                for encoding in box.resource.encodings:
                    if encoding.mimeType in self.formats and encoding.definition in self.qualities:
                        url = encoding.playUrl
                        break
                else:
                    raise Exception(f"url cannot be find {box}")
                self.items[index].video.url = url
