import logging
import re

from box import Box

from http_client import HttpClient
from models.video import Video
from settings import BASE_DIR_MOVIES, YOUTUBE_API_KEY, HOST_API_TOKEN

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GetVideos:
    url = "/3/movie/{}/videos?language=en-US"
    size = 1080

    def __init__(self, items, ids):
        self.items = items
        self.ids = ids

    @staticmethod
    async def get_best_video(item, candidate_videos):
        server = "www.googleapis.com"
        urls = [f"youtube/v3/videos?id={video.key}&part=contentDetails&key={YOUTUBE_API_KEY}"
                for video in candidate_videos]
        http_client = HttpClient.from_dict({"server": server, "urls": urls, 'json': True})
        responses = await http_client.run()

        longest_video = None
        max_duration = 0

        # For each candidate, get the actual duration
        for index, response in enumerate(responses):
            video = candidate_videos[index]
            print(f"id: {item.id}, title: {item.title.en}, video: {video.key}")
            try:
                # Extract duration in ISO 8601 format (PT1M30S = 1 minute 30 seconds)
                if response.get('items') and len(response['items']) > 0:
                    duration_str = response['items'][0]['contentDetails']['duration']

                    # Parse the duration string (PT1M30S format)
                    minutes = re.search(r'(\d+)M', duration_str)
                    seconds = re.search(r'(\d+)S', duration_str)

                    # Calculate total seconds
                    total_seconds = 0
                    if minutes:
                        total_seconds += int(minutes.group(1)) * 60
                    if seconds:
                        total_seconds += int(seconds.group(1))

                    print(f"title: {item.title.en}", f"duration: {total_seconds / 60} seconds")
                    # Update longest video if this one is longer
                    if total_seconds > max_duration:
                        max_duration = total_seconds
                        longest_video = video
            except Exception as e:
                print(f"Error fetching duration for video {video.key}: {e}")
        return longest_video

    async def run(self):
        item_id_pairs = [(item, item.id) for item in self.items if item.id in self.ids]

        # Fetch videos only for matching items
        http_client = HttpClient.from_dict({
            "urls": [f"{self.url.format(item_id)}" for _, item_id in item_id_pairs], 'token': HOST_API_TOKEN
            , 'json': True})

        responses = await http_client.run()

        # Process each response
        for i, response in enumerate(responses):
            item, _ = item_id_pairs[i]
            box = Box(response)

            # Filter for YouTube trailers with the right size
            candidate_videos = [
                video for video in box.results
                if video.site == "YouTube" and video.size >= self.size and video.type == "Trailer"
            ]

            if not candidate_videos:
                raise RuntimeError(f"id: {item.id}, title: {item.title.en}, candidate_videos is empty : {box}")

            # Get the best video based on duration
            best_video = await self.get_best_video(item, candidate_videos)

            # Update the item if we found a suitable video
            if best_video:
                video_id = best_video.key
                item.video = Video(id=video_id, url=f'https://www.youtube.com/watch?v={video_id}')
            elif not (BASE_DIR_MOVIES / item.title_to_dir() / "original.mp4").is_file():
                raise RuntimeError(
                    f"id: {item.id}, title: {item.title.en}, no compatible URL found {box}")
