import hashlib
import logging
import os
import subprocess
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

from box import Box
from ordered_set import OrderedSet

from api.get_videos import GetVideos
from api.video_editor import make_trailer
from http_client import HttpClient
from models.initial_data import InitialData
from models.video import Item
from settings import BASE_DIR, BASE_DIR_MOVIES

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
            abs_path = os.path.join(BASE_DIR_MOVIES, item.title_to_dir())
            Path(abs_path).mkdir(exist_ok=True)

        if ids_to_process:
            http_client = HttpClient.from_dict(
                {"urls": [f"{self.url.format(_id)}" for _id in ids_to_process]}
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
        workers = min(32, len(self.items))
        with Pool(workers) as p:
            p.map(make_trailer, [item for item in self.items])

    async def do_set(self):
        set_folder = self.serializer_object.title_to_dir()
        logger.info(f"do_set : {set_folder}")
        path_to_set = os.path.join(BASE_DIR_MOVIES, "sets", set_folder)
        Path(path_to_set).mkdir(exist_ok=True)
        os.chdir(path_to_set)

        files = [item.title_to_dir() for item in self.items]

        if len(files) != 10:
            raise RuntimeError("files must be 10")

        for movie_title in files:
            full_path_movie = str(os.path.join(BASE_DIR_MOVIES, movie_title))
            final_movie = os.path.join(full_path_movie, "final.mp4")
            subprocess.check_output(f"ln -sf {final_movie} {path_to_set}/{movie_title}.mp4", shell=True)

    def write_description(self):
        file_list_descriptions = os.path.join(BASE_DIR, "sets", "data1_descriptions.txt")
        with open(file_list_descriptions, 'w') as f:
            for item in self.items:
                f.write(f"{item.to_string()}\n\n")


def md5sum(filename):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def file_size(filename):
    """Get file size in bytes"""
    return os.path.getsize(filename)


def main(set_folder, files):
    # Set output project filename
    project_file = f"{set_folder}.kdenlive"

    # Get current date in the format Kdenlive expects
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Create a unique producer ID prefix (to avoid collisions)
    producer_prefix = "producer_"

    # Start building the project XML
    xml_content = f'''<?xml version='1.0' encoding='utf-8'?>
<mlt LC_NUMERIC="C" producer="main_bin" version="7.13.0" root="">
 <profile frame_rate_num="30" sample_aspect_num="1" display_aspect_den="9" colorspace="709" progressive="1" description="HD 1080p 30 fps" display_aspect_num="16" frame_rate_den="1" width="1920" height="1080" sample_aspect_den="1"/>
 <playlist id="main_bin">
  <property name="kdenlive:docproperties.activeTrack">2</property>
  <property name="kdenlive:docproperties.audioChannels">2</property>
  <property name="kdenlive:docproperties.audioTarget">1</property>
  <property name="kdenlive:docproperties.compositing">1</property>
  <property name="kdenlive:docproperties.disablepreview">0</property>
  <property name="kdenlive:docproperties.documentid">1678953734977</property>
  <property name="kdenlive:docproperties.enableTimelineZone">0</property>
  <property name="kdenlive:docproperties.enableexternalproxy">0</property>
  <property name="kdenlive:docproperties.enableproxy">0</property>
  <property name="kdenlive:docproperties.kdenliveversion">22.12.3</property>
  <property name="kdenlive:docproperties.position">0</property>
  <property name="kdenlive:docproperties.profile">atsc_1080p_30</property>
  <property name="kdenlive:docproperties.proxyextension"/>
  <property name="kdenlive:docproperties.proxyimageminsize">2000</property>
  <property name="kdenlive:docproperties.proxyimagesize">800</property>
  <property name="kdenlive:docproperties.proxyminsize">1000</property>
  <property name="kdenlive:docproperties.proxyparams"/>
  <property name="kdenlive:docproperties.proxyresize">640</property>
  <property name="kdenlive:docproperties.scrollPos">0</property>
  <property name="kdenlive:docproperties.seekOffset">30000</property>
  <property name="kdenlive:docproperties.version">1.04</property>
  <property name="kdenlive:docproperties.verticalzoom">1</property>
  <property name="kdenlive:docproperties.videoTarget">2</property>
  <property name="kdenlive:docproperties.zonein">0</property>
  <property name="kdenlive:docproperties.zoneout">75</property>
  <property name="kdenlive:docproperties.zoom">8</property>
  <property name="kdenlive:expandedFolders"/>
  <property name="kdenlive:documentnotes"/>
  <property name="xml_retain">1</property>
'''

    # Counter for IDs
    counter = 0

    # Add entries for each file
    for file in files:
        # Get absolute path
        absolute_path = os.path.abspath(file)

        producer_id = f"{producer_prefix}{counter}"
        counter += 1

        # Append producer entry
        xml_content += f'''  <entry producer="{producer_id}" in="00:00:00.000" out="00:00:00.000"/>
'''

    # Close playlist and add producers section
    xml_content += ''' </playlist>
 <tractor id="tractor0" in="00:00:00.000" out="00:00:00.000">
  <property name="kdenlive:projectTractor">1</property>
 </tractor>
'''

    # Add producers for each file
    counter = 0
    for file in files:
        absolute_path = os.path.abspath(file)
        filename = os.path.basename(file)

        producer_id = f"{producer_prefix}{counter}"
        counter += 1

        # Add producer
        xml_content += f''' <producer id="{producer_id}" in="00:00:00.000" out="00:10:00.000">
  <property name="length">18000</property>
  <property name="eof">pause</property>
  <property name="resource">{absolute_path}</property>
  <property name="audio_index">1</property>
  <property name="video_index">0</property>
  <property name="mute_on_pause">0</property>
  <property name="mlt_service">avformat-novalidate</property>
  <property name="kdenlive:clipname">{filename}</property>
  <property name="kdenlive:folderid">-1</property>
  <property name="kdenlive:id">{counter}</property>
  <property name="kdenlive:file_size">{file_size(file)}</property>
  <property name="kdenlive:file_hash">{md5sum(file)}</property>
  <property name="kdenlive:originalurl">{absolute_path}</property>
  <property name="xml">was here</property>
 </producer>
'''

    # Add main_bin producer and close the document
    xml_content += ''' <producer id="main_bin" in="00:00:00.000" out="00:00:00.000">
  <property name="kdenlive:projectFolder">1678953734979</property>
 </producer>
</mlt>
'''

    # Write the project file
    with open(project_file, 'w') as f:
        f.write(xml_content)

    print(f"Kdenlive project file created: {project_file}")
    print(f"Found and added {len(files)} MP4 files.")
    print(f"Now open {project_file} in Kdenlive and arrange clips on the timeline.")
