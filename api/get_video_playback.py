from box import Box

from http_client import HttpClient


class GetVideoPlayback:
    url = "/title/get-video-playback"
    # Qualities in descending order of preference
    qualities = ['1080p', '720p']
    formats = ['video/mp4']

    def __init__(self, items):
        self.items = items

    async def run(self):
        # Create HTTP client with URLs for movie items only
        http_client = HttpClient.from_dict(
            {"urls": [f"{self.url}?viconst={item.video.id}" for item in self.items if item.titleType == 'movie']}
        )

        # Process responses
        for index, response in enumerate(await http_client.run()):
            if self.items[index].titleType == 'movie':
                box = Box(response)

                # Find best available quality (highest quality first)
                best_url = None
                for quality in self.qualities:
                    if best_url:
                        break
                    for encoding in box.resource.encodings:
                        if encoding.mimeType in self.formats and encoding.definition == quality:
                            best_url = encoding.playUrl
                            break

                if not best_url:
                    raise Exception(f"title: {self.items[index].title.en}, no compatible URL found {box}")

                self.items[index].video.url = best_url
