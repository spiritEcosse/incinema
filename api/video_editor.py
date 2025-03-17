import asyncio
import glob
import logging
import os
import re
import subprocess
from decimal import Decimal
from itertools import cycle

import aioboto3
from openai import OpenAI

from api.random_scenes import RandomScenes
from clients.aws import AWSS3Client
from models.video import Item, Description, Title
from settings import BASE_DIR, BUCKET_VIDEO, BASE_DIR_MOVIES

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VideoEditor:
    def __init__(self, item: Item):
        self.font_path = "static/Mulish-Black.ttf"
        self.item = item
        self.original = "original.mp4"
        self.file_resolution = "_resolution.mp4"
        self.file_random_scenes = 'scene_random.txt'
        self.concat = "concat.mp4"
        self.list_concat = "list_concat.txt"
        self.caption = "caption.mp4"
        self.audio = "audio.mp3"
        self.final = "final.mp4"
        self.video_background_audio = "video_background_audio.mp4"
        self.item_background_audio = "background_audio.mp3"
        self.re_download = False
        # self.re_do_resolution = False
        self.re_do_audio = False
        self.re_random_scenes = False
        self.re_cut_scenes = False
        # self.re_check_commercial_scene = False
        # self.re_check_commercial_scene_image = True
        self.re_concat = False  # or self.re_check_commercial_scene_image
        self.re_caption = False
        self.re_add_audio = False
        self.re_add_background_audio = False
        self.re_upload_files = False
        self.font_size = 35
        self.font_color = 'white'
        self.position_x = 20
        self.position_y = 'h-text_h-20'
        self.dir = str(self.item.title_to_dir())
        self.abs_path = BASE_DIR_MOVIES / self.dir
        self.audio_duration = 60
        self.session = aioboto3.Session()

    async def run(self):
        try:
            print(f"run : {self.dir}")

            self.abs_path.mkdir(exist_ok=True)
            os.chdir(self.abs_path)
            await self.download()
            await self.do_audio()
            await self.random_scenes()
            await self.cut_scenes()
            await self.do_concat()
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
            self.re_random_scenes = True

        if os.path.isfile(self.audio):
            print(f"audio_duration: {self.dir}")
            audio_duration = await self.get_duration_of_file(self.audio)
            self.audio_duration = audio_duration[0]

    async def random_scenes(self):
        # logger.warning(f"random_scenes : exists file_detect_scenes: {os.path.isfile(self.file_detect_scenes)}")
        if not os.path.isfile(self.file_random_scenes) or self.re_random_scenes:
            print(f"random_scenes: {self.dir}")
            duration_original = await self.get_duration_of_file(self.original)
            RandomScenes(
                duration_original=duration_original[0],
                duration_audio=self.audio_duration,
                output_file=self.file_random_scenes
            ).run()
            self.re_cut_scenes = True

    async def cut_scenes(self):
        if (not self.get_original_scenes() or self.re_cut_scenes) and os.path.isfile(self.file_random_scenes):
            print(f"cut_scenes {self.item}")
            subprocess.check_output("rm -fr original-*", shell=True)
            command = (
                f"{BASE_DIR / 'scene_cut.sh'} -i {self.original} -c {self.file_random_scenes}"
            )
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            self.re_concat = True

    async def do_concat(self):
        if not os.path.isfile(self.concat) or self.re_concat:
            print(f"do_concat : {self.dir}")
            files = sorted(self.get_original_scenes(), key=lambda s: int(re.search(r'\d+', s).group()))

            with open(self.list_concat, 'w') as f:
                for file_name in files:
                    f.write("file '{}'\n".format(self.abs_path / file_name))
            subprocess.check_output(f"ffmpeg -y -f concat -safe 0 -i {self.list_concat} -c copy {self.concat}",
                                    shell=True)
            self.re_add_audio = True

    async def add_audio(self):
        if (not os.path.isfile(self.final) or self.re_add_audio) and os.path.isfile(self.audio):
            print(f"add_audio: {self.dir}")
            command = (
                f"ffmpeg -y -i {self.concat} -i {self.audio} "
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

    async def get_duration_of_file(self, file_name):
        output = subprocess.check_output(f'ffprobe -i {file_name} -show_entries format=duration -v quiet -of csv="p=0"',
                                         shell=True)
        return float(output), file_name

    def filter_scenes_by_duration_audio(self, scenes):
        """
        >>> item = Item(id="tt4154756", title=Title(en='Avengers: -_*.Infinity War', ru=""), titleType="movie", year=2018, duration=149, rating=Decimal(8.4), description=Description(ru="Текст"))
        >>> scenes_ = [(2.043710, "1.mp4"),(3.211540, "1.mp4"),(3.712040, "1.mp4"),(5, "1.mp4"),(3.049700, "1.mp4"),(2.002000, "1.mp4"),(5, "1.mp4"),(5, "1.mp4"),(2.168800, "1.mp4"),(2.085400, "1.mp4"),(5, "1.mp4"),(3.383400, "1.mp4"),(2.210500, "1.mp4"),(4.379300, "1.mp4"),(2.043700, "1.mp4"),(4.212500, "1.mp4"),(2.461000, "1.mp4"),(2.211000, "1.mp4"),(3.503000, "1.mp4"),(3.211000, "1.mp4"),(2.044000, "1.mp4"),(2.127000, "1.mp4"),(4.591000, "1.mp4")]
        >>> VideoEditor(item).filter_scenes_by_duration_audio(scenes_)
        [(2.04371, '1.mp4'), (3.21154, '1.mp4'), (3.71204, '1.mp4'), (5, '1.mp4'), (3.0497, '1.mp4'), (2.002, '1.mp4'), (5, '1.mp4'), (5, '1.mp4'), (2.1688, '1.mp4'), (2.0854, '1.mp4'), (5, '1.mp4'), (3.3834, '1.mp4'), (2.2105, '1.mp4'), (4.3793, '1.mp4'), (2.0437, '1.mp4'), (4.2125, '1.mp4'), (2.461, '1.mp4'), (2.211, '1.mp4'), (3.503, '1.mp4')]
        >>> scenes_ = [(2.043710, "1.mp4"),(3.211540, "1.mp4"),(3.712040, "1.mp4"),(5, "1.mp4"),(3.049700, "1.mp4"),(2.002000, "1.mp4"),(5, "1.mp4"),(5, "1.mp4"),(2.168800, "1.mp4"),(2.085400, "1.mp4"),(5, "1.mp4"),(3.383400, "1.mp4"),(2.210500, "1.mp4"),(4.379300, "1.mp4"),(2.043700, "1.mp4"),(4.212500, "1.mp4"),(2.461000, "1.mp4"),(2.211000, "1.mp4"),(5, "1.mp4"),(3.211000, "1.mp4"),(2.044000, "1.mp4"),(2.127000, "1.mp4"),(4.591000, "1.mp4")]
        >>> VideoEditor(item).filter_scenes_by_duration_audio(scenes_)
        [(2.04371, '1.mp4'), (3.21154, '1.mp4'), (3.71204, '1.mp4'), (5, '1.mp4'), (3.0497, '1.mp4'), (2.002, '1.mp4'), (5, '1.mp4'), (5, '1.mp4'), (2.1688, '1.mp4'), (2.0854, '1.mp4'), (5, '1.mp4'), (3.3834, '1.mp4'), (2.2105, '1.mp4'), (4.3793, '1.mp4'), (2.0437, '1.mp4'), (4.2125, '1.mp4'), (2.461, '1.mp4'), (2.211, '1.mp4'), (5, '1.mp4')]
        """
        filtered_scenes = []
        sum_duration = 0

        for duration, filename in cycle(scenes):
            if sum_duration <= self.audio_duration:
                sum_duration += duration
                filtered_scenes.append((duration, filename))
            else:
                break
        # print(f"sum_duration: {sum_duration}")
        return filtered_scenes

    async def tasks_get_duration_of_file(self, files: list):
        tasks = [self.get_duration_of_file(file_name) for file_name in files]
        return await asyncio.gather(*tasks)

    def get_original_scenes(self):
        files = glob.glob(fr'{self.original.split(".")[0]}-*.mp4')
        return sorted(files, key=lambda s: int(re.search(r'\d+', s).group()))


def make_trailer(item: Item):
    # Run the async function in a new event loop
    return asyncio.run(VideoEditor(item=item).run())
