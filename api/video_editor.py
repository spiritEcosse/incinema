import asyncio
import logging
import os
import subprocess

import aioboto3
from openai import OpenAI

from clients.aws import AWSS3Client
from models.video import Item
from settings import BUCKET_VIDEO, BASE_DIR_MOVIES

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VideoEditor:
    def __init__(self, item: Item):
        self.font_path = "static/Mulish-Black.ttf"
        self.item = item
        self.original = "original.mp4"
        self.audio = "audio.mp3"
        self.final = "final.mp4"
        self.re_download = False
        self.re_do_audio = False
        self.re_add_audio = False
        self.re_upload_files = False
        self.dir = str(self.item.title_to_dir())
        self.abs_path = BASE_DIR_MOVIES / self.dir
        self.session = aioboto3.Session()

    async def run(self):
        try:
            print(f"run : {self.dir}")

            self.abs_path.mkdir(exist_ok=True)
            os.chdir(self.abs_path)
            await self.download()
            await self.do_audio()
            # await self.random_scenes()
            # await self.cut_scenes()
            # await self.do_concat()
            # ########################################################################### await self.check_commercial_scene()
            # ########################################################################### await self.check_commercial_scene_image()
            # ###########################################################################  await self.do_caption()
            await self.add_audio()
            # ###########################################################################  await self.add_background_audio()
            await self.upload_files()
        except Exception as e:
            logger.exception(e)

    async def download(self):
        if not os.path.isfile(self.original) or self.re_download:
            command = f"yt-dlp --geo-bypass --merge-output-format mp4 --cookies-from-browser 'vivaldi' -o '{self.original}' '{self.item.video.url}'"
            try:
                subprocess.check_output(command, shell=True)
                print(f"download : {self.original} from {self.item.video.url}")
                self.re_random_scenes = True
            except Exception as e:
                print(f"Error downloading, dir: {self.dir}", command)
                raise e

    async def do_audio(self):
        if not os.path.isfile(self.audio) or self.re_do_audio:
            if self.item.description.en is None:
                raise RuntimeError(f"Description for {self.item.title.en} is empty. id: {self.item.id}")
            print(f"do_audio: {self.dir}")
            client = OpenAI()
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice="sage",  # sage, coral
                input=self.item.description.en,
            )
            response.write_to_file(self.audio)
            print(f'downloaded to {self.audio}')
            self.re_add_audio = True

    async def add_audio(self):
        if (not os.path.isfile(self.final) or self.re_add_audio) and os.path.isfile(self.audio):
            print(f"add_audio: {self.dir}")
            command = (
                f"ffmpeg -y -i {self.original} -i {self.audio} "
                f"-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 {self.final}"
            )
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            self.re_upload_files = True

    async def upload_files(self):
        if self.re_upload_files:
            files = [self.final, self.audio, self.original]

            # Create file mappings using a loop
            file_mappings = []
            for file_name in files:
                local_path = self.abs_path / file_name
                s3_key = f"movies/{self.dir}/{file_name}"
                file_mappings.append((local_path, s3_key))

            client = AWSS3Client(file_mappings, BUCKET_VIDEO)
            await client.upload_files()


def make_trailer(item: Item):
    # Run the async function in a new event loop
    return asyncio.run(VideoEditor(item=item).run())
