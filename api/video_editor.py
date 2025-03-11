import asyncio
import glob
import logging
import os
import re
import subprocess
from decimal import Decimal
from itertools import cycle
from pathlib import Path

import aioboto3
from openai import OpenAI

from api.random_scenes import RandomScenes
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
        self.background_audio = os.path.join(BASE_DIR, "background_audio", f"{self.item.background_audio}.mp3")
        self.re_download = False
        # self.re_do_resolution = False
        self.re_do_audio = False
        self.re_random_scenes = True
        self.re_cut_scenes = False
        # self.re_check_commercial_scene = False
        # self.re_check_commercial_scene_image = True
        self.re_concat = False  # or self.re_check_commercial_scene_image
        self.re_caption = False
        self.re_add_audio = False
        self.re_add_background_audio = False
        self.re_upload_all_files = False
        self.font_size = 35
        self.font_color = 'white'
        self.position_x = 20
        self.position_y = 'h-text_h-20'
        self.dir = str(self.item.title_to_dir())
        self.abs_path = os.path.join(BASE_DIR_MOVIES, self.dir)
        self.audio_duration = 60

    async def run(self):
        try:
            print(f"run : {self.dir}")

            Path(self.abs_path).mkdir(exist_ok=True)
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
            # ###########################################################################  await self.upload_all_files()
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
                logger.exception(e)
                self.re_download = True

    async def do_audio(self):
        if not os.path.isfile(self.audio) or self.re_do_audio:
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
                f"{os.path.join(BASE_DIR, 'scene_cut.sh')} -i {self.original} -c {self.file_random_scenes}"
            )
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            self.re_concat = True

    async def do_concat(self):
        if not os.path.isfile(self.concat) or self.re_concat:
            print(f"do_concat : {self.dir}")
            files = sorted(self.get_original_scenes(), key=lambda s: int(re.search(r'\d+', s).group()))

            with open(self.list_concat, 'w') as f:
                for file_name in files:
                    f.write("file '{}'\n".format(os.path.join(self.abs_path, file_name)))
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

    async def upload_all_files(self):
        if self.re_upload_all_files:
            await self.tasks_upload(glob.glob("*"))

    async def upload(self, file_name: str) -> None:
        s3_key = f"{self.dir}/{file_name}"
        print(f"upload {s3_key}")

        session = aioboto3.Session()
        async with session.client("s3") as s3:
            with Path(self.abs_path, file_name).open("rb") as file_data:
                await s3.upload_fileobj(file_data, BUCKET_VIDEO, s3_key)

    async def tasks_upload(self, files: list):
        tasks = [self.upload(file_name) for file_name in files]
        return await asyncio.gather(*tasks)

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

    # async def add_background_audio(self):
    #     if (not os.path.isfile(self.video_background_audio) or self.re_add_background_audio) and os.path.isfile(
    #             self.background_audio) and os.path.isfile(self.video_audio):
    #         print(f"add_background_audio: {self.dir}")
    #         subprocess.check_output(
    #             f"ffmpeg -y -i {self.background_audio} -to {self.audio_duration} {self.item_background_audio}",
    #             shell=True)
    #         subprocess.check_output(
    #             f'ffmpeg -y -i {self.video_audio} -i {self.item_background_audio} -c:v copy -filter_complex "[0:a][1:a] amix=inputs=2:duration=longest [audio_out]" -c:a aac -map 0:v -map "[audio_out]" {self.video_background_audio}',
    #             shell=True)
    #         self.re_upload_all_files = True

    # async def do_caption(self):
    #     if not os.path.isfile(self.caption) or self.re_caption:
    #         print(f"do_caption: {self.dir}")
    #         command = (
    #             f"ffmpeg -y -i {self.concat} -vf "
    #             f"\"drawtext=fontfile={self.font_path}: text='{self.item.to_string()}': "
    #             f"fontsize={self.font_size}: fontcolor={self.font_color}: "
    #             f"x={self.position_x}: y={self.position_y}\" "
    #             f"-codec:a copy {self.caption}"
    #         )
    #         print(command)
    #         subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    #         self.re_add_audio = True

    # async def tasks_video_detect(self, files: list):
    #     tasks = [VideoDetect(file_name, f"{self.dir}/{file_name}", position).run() for position, file_name in enumerate(files)]
    #     return await asyncio.gather(*tasks)
    #
    # def split_scene_on_frames(self, scene):
    #     scene_folder = scene.split('.mp4')[0]
    #     folder_frames = f"frames-{scene_folder}"
    #     shutil.rmtree(folder_frames, ignore_errors=True)
    #     Path(folder_frames).mkdir(exist_ok=True)
    #     subprocess.run(['ffmpeg', '-i', scene, f'{folder_frames}/frame-%06d.png'])
    #     return folder_frames
    #
    # def get_images_in_folder(self, folder):
    #     return [os.path.join(BASE_DIR, folder, image) for image in
    #             os.listdir(os.path.join(BASE_DIR, folder)) if image.endswith(".png")]
    #
    # async def check_commercial_scene_image(self):
    #     if self.re_check_commercial_scene_image:
    #         print(f"check_commercial_scene_image {self.dir}")
    #         assert self.get_original_scenes() != [], "get_original_scenes is empty."
    #         images_exclude = self.get_images_in_folder("images_exclude")
    #
    #         data = []
    #         for file_name in self.get_original_scenes():
    #             folder_frames = self.split_scene_on_frames(file_name)
    #             data.append((file_name, folder_frames))
    #             # print(f"after split_scene_on_frames: {file_name}")
    #
    #         tasks = [
    #             (file_name, image, frame)
    #             for file_name, folder_frames in data
    #             for frame in self.get_images_in_folder(f"{self.dir}/{folder_frames}")
    #             for image in images_exclude
    #         ]
    #
    #         with Pool(10) as p:
    #             result = p.map(func_compare_image, tasks)
    #
    #             print(f"after Pool")
    #             for video, is_commercial in result:
    #                 if is_commercial:
    #                     Path(self.abs_path, video).unlink(missing_ok=True)
    #                     break
    #
    # async def check_commercial_scene(self):
    #     if self.re_check_commercial_scene:
    #         print(f"check_commercial_scene {self.dir}")
    #         # assert self.get_original_scenes() != [], "get_original_scenes is empty."
    #         list_video_detect = await self.tasks_video_detect(self.get_original_scenes())
    #         for file_name, is_commercial in list_video_detect:
    #             if is_commercial:
    #                 Path(self.abs_path, file_name).unlink(missing_ok=True)
    #         self.re_concat = True

    # async def do_resolutions(self):
    #     if self.re_do_resolution:
    #         print(f"do_resolutions: {self.dir}")
    #         resolution = subprocess.check_output(f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of json {self.original}", shell=True)
    #         resolution_json = json.loads(resolution)
    #         box = Box(resolution_json)
    #
    #         if box.streams[0].width != 1920:
    #             [self.do_resolution(file_) for file_ in self.get_original_scenes()]
    #         self.re_concat = True

    # def do_resolution(self, file_):
    #     subprocess.run([
    #         "ffmpeg", "-y", "-i", file_, "-vf", "scale=1920:-1", "-preset", "slow", "-crf", "18", "-ac", "2", f"{file_}{self.file_resolution}"])
    #     subprocess.check_output(f"mv -f {file_}{self.file_resolution} {file_}", shell=True)


def make_trailer(item: Item):
    # Run the async function in a new event loop
    return asyncio.run(VideoEditor(item=item).run())
