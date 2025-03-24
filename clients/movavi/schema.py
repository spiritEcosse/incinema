import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union, Optional, List

from utils import extract_filename


class FilePath:
    """
    Class to encapsulate file path information for Movavi projects

    Attributes:
        real_path (Path): The actual path to the file on disk (used for reading/processing)
        config_path (str): The path to use in the Movavi config file
    """

    def __init__(self, real_path: Union[Path, str], config_path: Optional[str] = None):
        """
        Initialize a FilePath object

        Args:
            real_path (Path or str): The actual path to the file on disk
            config_path (str, optional): The path to use in the Movavi config file.
                                        If None, defaults to real_path as string.
        """
        # Convert string to Path if needed
        self.real_path = Path(real_path) if not isinstance(real_path, Path) else real_path

        # If config_path is not provided, convert real_path to string
        if config_path is None:
            self.config_path = str(self.real_path)
        else:
            self.config_path = config_path

    @property
    def filename(self) -> str:
        """Get the filename from the config path"""
        return os.path.basename(self.config_path)

    @property
    def size(self) -> int:
        """Get the file size in bytes (from the real path)"""
        return self.real_path.stat().st_size if self.real_path.exists() else 10000000

    @property
    def extension(self) -> str:
        """Get the file extension (from the config path)"""
        return os.path.splitext(self.config_path)[1].lower().lstrip('.')

    def __str__(self) -> str:
        """String representation showing both paths"""
        return f"FilePath(real_path='{self.real_path}', config_path='{self.config_path}')"


class MovaviObject:
    """Base class for all Movavi objects"""

    def __init__(self, object_id: int, object_type: str):
        self.object_id = object_id
        self.object_type = object_type

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = ET.Element("RootObject")
        element.set("type", self.object_type)
        element.set("objectId", str(self.object_id))
        return element


class Predeclarator(MovaviObject):
    """Class for Predeclarator object"""

    def __init__(self, object_id: int):
        super().__init__(object_id, "Predeclarator")
        self.predeclarations = []

    def add_predeclaration(self, type_name: str, oid: int, poid: int = 0, refs: List[int] = None):
        """Add a predeclaration to the list"""
        if refs is None:
            refs = []
        self.predeclarations.append({
            "typeName": type_name,
            "oid": oid,
            "poid": poid,
            "refs": refs
        })

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()
        predeclarations = ET.SubElement(element, "predeclarations")
        predeclarations.set("type", "Array")
        predeclarations.set("size", str(len(self.predeclarations)))

        for i, predef in enumerate(self.predeclarations, 1):
            item = ET.SubElement(predeclarations, "Item")
            item.set("type", "Item")
            item.set("index", str(i))

            data = ET.SubElement(item, "Data")
            data.set("type", "Predeclare")
            data.set("objectId", str(self.object_id + i + 1))

            type_name = ET.SubElement(data, "typeName")
            type_name.set("type", "String")
            type_name.set("value", predef["typeName"])

            oid = ET.SubElement(data, "oid")
            oid.set("type", "ObjectRef")
            oid.set("value", str(predef["oid"]))

            poid = ET.SubElement(data, "poid")
            poid.set("type", "ObjectRef")
            poid.set("value", str(predef["poid"]))

            refs_elem = ET.SubElement(data, "refs")
            refs_elem.set("type", "Array")
            refs_elem.set("size", str(len(predef["refs"])))

            for j, ref in enumerate(predef["refs"], 1):
                ref_item = ET.SubElement(refs_elem, "Item")
                ref_item.set("type", "Item")
                ref_item.set("index", str(j))

                ref_data = ET.SubElement(ref_item, "Data")
                ref_data.set("type", "ObjectRef")
                ref_data.set("value", str(ref))

        return element


class ProjectContent(MovaviObject):
    """Class for Project::Content object"""

    def __init__(self, object_id: int, timeline_id: int, user_collection_id: int):
        super().__init__(object_id, "Project::Content")
        self.timeline_id = timeline_id
        self.user_collection_id = user_collection_id
        self.portable = False

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        timeline = ET.SubElement(element, "timeline")
        timeline.set("type", "ObjectRef")
        timeline.set("value", str(self.timeline_id))

        user_collection = ET.SubElement(element, "userCollection")
        user_collection.set("type", "ObjectRef")
        user_collection.set("value", str(self.user_collection_id))

        portable = ET.SubElement(element, "portable")
        portable.set("type", "bool")
        portable.set("value", "0" if not self.portable else "1")

        return element


class TimelineObject(MovaviObject):
    """Class for Timeline::Object"""

    def __init__(self, object_id: int, width: int, height: int, frame_rate_n: int, frame_rate_d: int,
                 sample_rate: int, channel_layout=None):
        super().__init__(object_id, "Timeline::Object")
        self.width = width
        self.height = height
        self.frame_rate_n = frame_rate_n
        self.frame_rate_d = frame_rate_d
        self.aspect_x = 1
        self.aspect_y = 1

        # Handle channel_layout properly
        if isinstance(channel_layout, str):
            # Simplified mapping: only use 1 or 2
            self.channel_layout = 1 if channel_layout.lower() == "mono" else 2
        else:
            # If it's already a number or None
            self.channel_layout = 1 if channel_layout == 1 else 2

        self.sample_rate = sample_rate
        self.sample_format = 1
        self.clips = []
        self.links = []
        self.tracks = []

    def add_clip(self, clip_id: int, clip_timing: dict):
        """Add a clip to the timeline"""
        self.clips.append({
            "key": clip_id,
            "value": clip_timing
        })

    def add_link(self, key_id: int, link: dict):
        """Add a link to the timeline"""
        self.links.append({
            "key": key_id,
            "value": link
        })

    def add_track(self, track_id: int):
        """Add a track to the timeline"""
        self.tracks.append(track_id)

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        # Add video base
        video_base = ET.SubElement(element, "BaseOfObject")
        video_base.set("type", "Video")
        video_base.set("objectId", str(self.object_id))

        width = ET.SubElement(video_base, "width")
        width.set("type", "int32_t")
        width.set("value", str(self.width))

        height = ET.SubElement(video_base, "height")
        height.set("type", "int32_t")
        height.set("value", str(self.height))

        frame_rate_n = ET.SubElement(video_base, "frameRateN")
        frame_rate_n.set("type", "int32_t")
        frame_rate_n.set("value", str(self.frame_rate_n))

        frame_rate_d = ET.SubElement(video_base, "frameRateD")
        frame_rate_d.set("type", "int32_t")
        frame_rate_d.set("value", str(self.frame_rate_d))

        aspect_x = ET.SubElement(video_base, "aspectX")
        aspect_x.set("type", "int32_t")
        aspect_x.set("value", str(self.aspect_x))

        aspect_y = ET.SubElement(video_base, "aspectY")
        aspect_y.set("type", "int32_t")
        aspect_y.set("value", str(self.aspect_y))

        # Add audio base
        audio_base = ET.SubElement(element, "BaseOfObject")
        audio_base.set("type", "Audio")
        audio_base.set("objectId", str(self.object_id))

        channel_layout = ET.SubElement(audio_base, "channelLayout")
        channel_layout.set("type", "int32_t")
        channel_layout.set("value", str(self.channel_layout))

        sample_rate = ET.SubElement(audio_base, "sampleRate")
        sample_rate.set("type", "int32_t")
        sample_rate.set("value", str(self.sample_rate))

        sample_format = ET.SubElement(audio_base, "sampleFormat")
        sample_format.set("type", "int32_t")
        sample_format.set("value", str(self.sample_format))

        # Add clips
        clips_elem = ET.SubElement(element, "clips")
        clips_elem.set("type", "Array")
        clips_elem.set("size", str(len(self.clips)))

        for i, clip in enumerate(self.clips, 1):
            item = ET.SubElement(clips_elem, "Item")
            item.set("type", "Item")
            item.set("index", str(i))

            key = ET.SubElement(item, "Key")
            key.set("type", "ObjectRef")
            key.set("value", str(clip["key"]))

            value = ET.SubElement(item, "Value")
            value.set("type", "Timeline::ClipTiming")
            value.set("objectId", str(clip["value"]["objectId"]))

            # Define fields that must be int64_t
            int64_fields = ["timestamp", "sourceDuration", "sourcePosition", "duration",
                            "transitionIn", "transitionOut", "fadeInDuraion", "fadeOutDuraion"]

            for prop_name, prop_value in clip["value"].items():
                if prop_name == "objectId":
                    continue

                prop = ET.SubElement(value, prop_name)
                if isinstance(prop_value, bool):
                    prop.set("type", "bool")
                    prop.set("value", "1" if prop_value else "0")
                elif isinstance(prop_value, int):
                    if prop_name == "track":
                        prop.set("type", "ObjectRef")
                    elif prop_name in int64_fields:
                        prop.set("type", "int64_t")
                    else:
                        prop.set("type", "int32_t")
                    prop.set("value", str(prop_value))
                else:
                    prop.set("type", "String")
                    prop.set("value", str(prop_value))

        # Add links
        links_elem = ET.SubElement(element, "links")
        links_elem.set("type", "Array")
        links_elem.set("size", str(len(self.links)))

        for i, link in enumerate(self.links, 1):
            item = ET.SubElement(links_elem, "Item")
            item.set("type", "Item")
            item.set("index", str(i))

            key = ET.SubElement(item, "Key")
            key.set("type", "ObjectRef")
            key.set("value", str(link["key"]))

            value = ET.SubElement(item, "Value")
            value.set("type", "Timeline::Link")
            value.set("objectId", str(link["value"]["objectId"]))

            master = ET.SubElement(value, "master")
            master.set("type", "ObjectRef")
            master.set("value", str(link["value"]["master"]))

            offset = ET.SubElement(value, "offset")
            offset.set("type", "int64_t")
            offset.set("value", str(link["value"]["offset"]))

        # Add tracks
        tracks_elem = ET.SubElement(element, "tracks")
        tracks_elem.set("type", "Array")
        tracks_elem.set("size", str(len(self.tracks)))

        for i, track_id in enumerate(self.tracks, 1):
            item = ET.SubElement(tracks_elem, "Item")
            item.set("type", "Item")
            item.set("index", str(i))

            data = ET.SubElement(item, "Data")
            data.set("type", "ObjectRef")
            data.set("value", str(track_id))

        # Add transitions (empty in example)
        transitions = ET.SubElement(element, "transitions")
        transitions.set("type", "Array")
        transitions.set("size", "0")

        return element


class TimelineClip(MovaviObject):
    """Class for Timeline::Clip object"""

    def __init__(self, object_id: int, timeline_id: int, clip_type: int, name: str, file_id: int, source_duration: int):
        super().__init__(object_id, "Timeline::Clip")
        self.timeline_id = timeline_id
        self.clip_type = clip_type  # 1 for video, 2 for audio

        # Ensure we're always using just the filename, not a full path
        self.name = extract_filename(name)

        self.file_id = file_id
        self.source_duration = source_duration
        self.enabled = True
        self.volume = 100

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        timeline = ET.SubElement(element, "timeline")
        timeline.set("type", "ObjectRef")
        timeline.set("value", str(self.timeline_id))

        clip_type = ET.SubElement(element, "type")
        clip_type.set("type", "int32_t")
        clip_type.set("value", str(self.clip_type))

        name = ET.SubElement(element, "name")
        name.set("type", "String")
        name.set("value", self.name)

        enabled = ET.SubElement(element, "enabled")
        enabled.set("type", "bool")
        enabled.set("value", "1" if self.enabled else "0")

        # Add empty or zero refs
        for ref_name in ["overlay", "quiz"]:
            ref = ET.SubElement(element, ref_name)
            ref.set("type", "ObjectRef")
            ref.set("value", "0")

        file_ref = ET.SubElement(element, "file")
        file_ref.set("type", "ObjectRef")
        file_ref.set("value", str(self.file_id))

        nested_timeline = ET.SubElement(element, "nestedTimeline")
        nested_timeline.set("type", "ObjectRef")
        nested_timeline.set("value", "0")

        volume = ET.SubElement(element, "volume")
        volume.set("type", "int32_t")
        volume.set("value", str(self.volume))

        # Add more empty refs
        for ref_name in ["volumeEnvelope", "cropEnvelope", "moveEnvelope"]:
            ref = ET.SubElement(element, ref_name)
            ref.set("type", "ObjectRef")
            ref.set("value", "0")

        volume_normalize = ET.SubElement(element, "volumeNormalize")
        volume_normalize.set("type", "bool")
        volume_normalize.set("value", "0")

        broken = ET.SubElement(element, "broken")
        broken.set("type", "bool")
        broken.set("value", "0")

        unlimited_duration = ET.SubElement(element, "unlimitedDuration")
        unlimited_duration.set("type", "bool")
        unlimited_duration.set("value", "0")

        source_duration = ET.SubElement(element, "sourceDuration")
        source_duration.set("type", "int64_t")
        source_duration.set("value", str(self.source_duration))

        # Empty arrays
        for array_name in ["effects", "labels", "motionTrackings"]:
            array = ET.SubElement(element, array_name)
            array.set("type", "Array")
            array.set("size", "0")

        # More refs
        for ref_name in ["rhythm", "stabilization"]:
            ref = ET.SubElement(element, ref_name)
            ref.set("type", "ObjectRef")
            ref.set("value", "0")

        media_track = ET.SubElement(element, "mediaTrack")
        media_track.set("type", "int32_t")
        media_track.set("value", "0")

        return element


class File(MovaviObject):
    """Class for File object"""

    def __init__(self, object_id: int, path: str, size: int, format: str, length: int,
                 video_track_id: int = None, audio_track_id: int = None):
        super().__init__(object_id, "File")
        self.path = path
        self.size = size
        self.format = format
        self.length = length
        self.is_opening = False
        self.is_opened = True
        self.is_failed = False
        self.video_track_id = video_track_id
        self.audio_track_id = audio_track_id

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        path = ET.SubElement(element, "path")
        path.set("type", "String")
        path.set("value", self.path)

        size = ET.SubElement(element, "size")
        size.set("type", "int64_t")
        size.set("value", str(self.size))

        format_elem = ET.SubElement(element, "format")
        format_elem.set("type", "String")
        format_elem.set("value", self.format)

        length = ET.SubElement(element, "length")
        length.set("type", "int64_t")
        length.set("value", str(self.length))

        is_opening = ET.SubElement(element, "isOpening")
        is_opening.set("type", "bool")
        is_opening.set("value", "1" if self.is_opening else "0")

        is_opened = ET.SubElement(element, "isOpened")
        is_opened.set("type", "bool")
        is_opened.set("value", "1" if self.is_opened else "0")

        is_failed = ET.SubElement(element, "isFailed")
        is_failed.set("type", "bool")
        is_failed.set("value", "1" if self.is_failed else "0")

        # Video tracks
        video_tracks = ET.SubElement(element, "videoTracks")
        if self.video_track_id:
            video_tracks.set("type", "Array")
            video_tracks.set("size", "1")

            item = ET.SubElement(video_tracks, "Item")
            item.set("type", "Item")
            item.set("index", "1")

            data = ET.SubElement(item, "Data")
            data.set("type", "ObjectRef")
            data.set("value", str(self.video_track_id))
        else:
            video_tracks.set("type", "Array")
            video_tracks.set("size", "0")

        # Audio tracks
        audio_tracks = ET.SubElement(element, "audioTracks")
        if self.audio_track_id:
            audio_tracks.set("type", "Array")
            audio_tracks.set("size", "1")

            item = ET.SubElement(audio_tracks, "Item")
            item.set("type", "Item")
            item.set("index", "1")

            data = ET.SubElement(item, "Data")
            data.set("type", "ObjectRef")
            data.set("value", str(self.audio_track_id))
        else:
            audio_tracks.set("type", "Array")
            audio_tracks.set("size", "0")

        return element


class VideoTrack(MovaviObject):
    """Class for VideoTrack object"""

    def __init__(self, object_id: int, file_id: int, width: int, height: int,
                 frame_rate_n: int, frame_rate_d: int, bitrate: int, codec_id: str):
        super().__init__(object_id, "VideoTrack")
        self.file_id = file_id
        self.width = width
        self.height = height
        self.frame_rate_n = frame_rate_n
        self.frame_rate_d = frame_rate_d
        self.aspect_x = 1
        self.aspect_y = 1
        self.codec_id = codec_id
        self.bitrate = bitrate
        self.is_image = False

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        # Base video object
        base_video = ET.SubElement(element, "BaseOfObject")
        base_video.set("type", "Video")
        base_video.set("objectId", str(self.object_id))

        width = ET.SubElement(base_video, "width")
        width.set("type", "int32_t")
        width.set("value", str(self.width))

        height = ET.SubElement(base_video, "height")
        height.set("type", "int32_t")
        height.set("value", str(self.height))

        frame_rate_n = ET.SubElement(base_video, "frameRateN")
        frame_rate_n.set("type", "int32_t")
        frame_rate_n.set("value", str(self.frame_rate_n))

        frame_rate_d = ET.SubElement(base_video, "frameRateD")
        frame_rate_d.set("type", "int32_t")
        frame_rate_d.set("value", str(self.frame_rate_d))

        aspect_x = ET.SubElement(base_video, "aspectX")
        aspect_x.set("type", "int32_t")
        aspect_x.set("value", str(self.aspect_x))

        aspect_y = ET.SubElement(base_video, "aspectY")
        aspect_y.set("type", "int32_t")
        aspect_y.set("value", str(self.aspect_y))

        # Base track object
        base_track = ET.SubElement(element, "BaseOfObject")
        base_track.set("type", "Track")
        base_track.set("objectId", str(self.object_id))

        file_ref = ET.SubElement(base_track, "file")
        file_ref.set("type", "ObjectRef")
        file_ref.set("value", str(self.file_id))

        index = ET.SubElement(base_track, "index")
        index.set("type", "int32_t")
        index.set("value", "0")  # First track

        codec_id = ET.SubElement(base_track, "codecId")
        codec_id.set("type", "String")
        codec_id.set("value", self.codec_id)

        bitrate = ET.SubElement(base_track, "bitrate")
        bitrate.set("type", "int32_t")
        bitrate.set("value", str(self.bitrate))

        # Is image
        is_image = ET.SubElement(element, "isImage")
        is_image.set("type", "bool")
        is_image.set("value", "1" if self.is_image else "0")

        return element


class AudioTrack(MovaviObject):
    """Class for AudioTrack object"""

    def __init__(self, object_id: int, file_id: int, channel_layout,
                 sample_rate: int, sample_format: int, bitrate: int, codec_id=None):
        super().__init__(object_id, "AudioTrack")
        self.file_id = file_id

        # Handle channel_layout properly
        if isinstance(channel_layout, str):
            # Simplified mapping: only use 1 or 2
            self.channel_layout = 1 if channel_layout.lower() == "mono" else 2
        else:
            # If it's already a number or None
            self.channel_layout = 1 if channel_layout == 1 else 2

        self.sample_rate = sample_rate
        self.sample_format = sample_format
        self.codec_id = codec_id if codec_id else "CODEC_ID_AAC"
        self.bitrate = bitrate

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        # Base audio object
        base_audio = ET.SubElement(element, "BaseOfObject")
        base_audio.set("type", "Audio")
        base_audio.set("objectId", str(self.object_id))

        channel_layout = ET.SubElement(base_audio, "channelLayout")
        channel_layout.set("type", "int32_t")
        channel_layout.set("value", str(self.channel_layout))

        sample_rate = ET.SubElement(base_audio, "sampleRate")
        sample_rate.set("type", "int32_t")
        sample_rate.set("value", str(self.sample_rate))

        sample_format = ET.SubElement(base_audio, "sampleFormat")
        sample_format.set("type", "int32_t")
        sample_format.set("value", str(self.sample_format))

        # Base track object
        base_track = ET.SubElement(element, "BaseOfObject")
        base_track.set("type", "Track")
        base_track.set("objectId", str(self.object_id))

        file_ref = ET.SubElement(base_track, "file")
        file_ref.set("type", "ObjectRef")
        file_ref.set("value", str(self.file_id))

        index = ET.SubElement(base_track, "index")
        index.set("type", "int32_t")
        index.set("value", "1")  # Audio is usually track 1

        codec_id = ET.SubElement(base_track, "codecId")
        codec_id.set("type", "String")
        codec_id.set("value", self.codec_id)

        bitrate = ET.SubElement(base_track, "bitrate")
        bitrate.set("type", "int32_t")
        bitrate.set("value", str(self.bitrate))

        return element


class TimelineTrack(MovaviObject):
    """Class for Timeline::Track object"""

    def __init__(self, object_id: int, timeline_id: int, track_type: int,
                 muted: bool = False, hidden: bool = False, linked: bool = False,
                 gapless: bool = False, used: bool = False):
        super().__init__(object_id, "Timeline::Track")
        self.timeline_id = timeline_id
        self.track_type = track_type
        self.muted = muted
        self.hidden = hidden
        self.linked = linked
        self.gapless = gapless
        self.used = used

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        track_type = ET.SubElement(element, "type")
        track_type.set("type", "int32_t")
        track_type.set("value", str(self.track_type))

        muted = ET.SubElement(element, "muted")
        muted.set("type", "bool")
        muted.set("value", "1" if self.muted else "0")

        hidden = ET.SubElement(element, "hidden")
        hidden.set("type", "bool")
        hidden.set("value", "1" if self.hidden else "0")

        linked = ET.SubElement(element, "linked")
        linked.set("type", "bool")
        linked.set("value", "1" if self.linked else "0")

        gapless = ET.SubElement(element, "gapless")
        gapless.set("type", "bool")
        gapless.set("value", "1" if self.gapless else "0")

        used = ET.SubElement(element, "used")
        used.set("type", "bool")
        used.set("value", "1" if self.used else "0")

        timeline = ET.SubElement(element, "timeline")
        timeline.set("type", "ObjectRef")
        timeline.set("value", str(self.timeline_id))

        return element


class EditorCollectionUserObject(MovaviObject):
    """Class for EditorCollection::UserObject"""

    def __init__(self, object_id: int, items=None):
        super().__init__(object_id, "EditorCollection::UserObject")
        self.items = items if items else []

    def add_item(self, item_id: int):
        """Add an item to the collection"""
        self.items.append(item_id)

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        items_elem = ET.SubElement(element, "items")
        items_elem.set("type", "Array")
        items_elem.set("size", str(len(self.items)))

        for i, item_id in enumerate(self.items, 1):
            item = ET.SubElement(items_elem, "Item")
            item.set("type", "Item")
            item.set("index", str(i))

            data = ET.SubElement(item, "Data")
            data.set("type", "ObjectRef")
            data.set("value", str(item_id))

        return element


class ImportObject(MovaviObject):
    """Class for Import::Object"""

    def __init__(self, object_id: int, tag: str, location: str, kind: int = 2):
        super().__init__(object_id, "Import::Object")
        # Make sure tag is just a filename if it's not already
        self.tag = extract_filename(tag) if '\\' in tag or '/' in tag else tag
        self.location = location
        self.description = location
        self.description_url = ""
        self.remote_url = ""
        self.remote_size = -1
        self.kind = kind  # Added kind parameter with default value 2
        self.category = "user_files"

    def to_element(self) -> ET.Element:
        """Convert object to XML element"""
        element = super().to_element()

        tag = ET.SubElement(element, "tag")
        tag.set("type", "String")
        tag.set("value", self.tag)

        description = ET.SubElement(element, "description")
        description.set("type", "String")
        description.set("value", self.description)

        description_url = ET.SubElement(element, "descriptionUrl")
        description_url.set("type", "String")
        description_url.set("value", self.description_url)

        location = ET.SubElement(element, "location")
        location.set("type", "String")
        location.set("value", self.location)

        remote_url = ET.SubElement(element, "remoteUrl")
        remote_url.set("type", "String")
        remote_url.set("value", self.remote_url)

        remote_size = ET.SubElement(element, "remoteSize")
        remote_size.set("type", "int64_t")
        remote_size.set("value", str(self.remote_size))

        kind = ET.SubElement(element, "kind")
        kind.set("type", "int32_t")
        kind.set("value", str(self.kind))

        category = ET.SubElement(element, "category")
        category.set("type", "String")
        category.set("value", self.category)

        return element
