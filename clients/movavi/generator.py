import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

from clients.movavi.schema import MovaviObject, Predeclarator, ProjectContent, TimelineObject, VideoTrack, File, \
    AudioTrack, TimelineTrack, TimelineClip, EditorCollectionUserObject, ImportObject
from utils import extract_filename, get_video_metadata


class MovaviProjectGenerator:
    """Class to generate a Movavi project file with structure matching the original XML"""

    def __init__(self, start_id=6589000):
        self.objects = {}
        self.root_ref = None
        self.next_id = start_id  # Use higher starting ID to match original XML

    def get_next_id(self) -> int:
        """Get the next available object ID with spacing similar to original XML"""
        self.next_id += 1
        return self.next_id

    def add_object(self, obj: MovaviObject):
        """Add an object to the project"""
        self.objects[obj.object_id] = obj
        return obj

    def add_video_to_project(self, video_path: str, real_path: str):
        """Add a video to an existing Movavi project with structure matching the original XML"""
        # Extract video metadata if available
        metadata = get_video_metadata(real_path) if os.path.exists(real_path) else {}

        # Extract values from metadata using direct dictionary access
        try:
            width = metadata['width']
            height = metadata['height']
            frame_rate_n = metadata['frame_rate_n']
            frame_rate_d = metadata['frame_rate_d']
            duration_frames = metadata['duration_frames']
            video_bitrate = metadata['video_bitrate']
            audio_bitrate = metadata['audio_bitrate']
        except KeyError as e:
            # Log which metadata is missing
            print(f"Error: Missing required video metadata: {e}")
            print("Cannot create project without complete metadata")
            raise ValueError(f"Required video metadata missing: {e}. Please ensure the video file is valid.")

        # Get file information
        filename = extract_filename(video_path)
        filesize = os.path.getsize(real_path) if os.path.exists(real_path) else 10000000
        file_ext = os.path.splitext(video_path)[1].lower().lstrip('.')

        # Get detailed audio properties
        audio_props = metadata['audio_props']

        # Create an ID generator
        class IdGenerator:
            def __init__(self, start=1000):
                self.current_id = start

            def next_id(self):
                self.current_id += 1
                return self.current_id

        # Create ID generators for different ID ranges
        predeclarator_gen = IdGenerator(7000000)
        project_content_gen = IdGenerator(4000)
        timeline_object_gen = IdGenerator(3900)
        video_audio_gen = IdGenerator(6580000)
        timeline_track_gen = IdGenerator(6582000)
        editor_gen = IdGenerator(3000)
        timing_gen = IdGenerator(6990000)

        # Generate IDs for all objects
        predeclarator_id = predeclarator_gen.next_id()
        project_content_id = project_content_gen.next_id()
        timeline_object_id = timeline_object_gen.next_id()

        # Other IDs using different ranges
        video_clip_id = video_audio_gen.next_id()
        audio_clip_id = video_audio_gen.next_id()
        file_id = video_audio_gen.next_id()
        video_track_id = video_audio_gen.next_id()
        audio_track_id = video_audio_gen.next_id()

        timeline_video_track_id = timeline_track_gen.next_id()
        timeline_audio_track_id = timeline_track_gen.next_id()
        timeline_titles_track_id = timeline_track_gen.next_id()
        timeline_overlay_track_id = timeline_track_gen.next_id()
        timeline_overlay2_track_id = timeline_track_gen.next_id()
        timeline_effects_track_id = timeline_track_gen.next_id()
        timeline_background_track_id = timeline_track_gen.next_id()

        editor_collection_id = editor_gen.next_id()
        import_object_id = video_audio_gen.next_id()

        video_timing_id = timing_gen.next_id()
        audio_timing_id = timing_gen.next_id()
        link_id = timing_gen.next_id()

        # Create Predeclarator
        predeclarator = self.add_object(Predeclarator(predeclarator_id))
        predeclarator.add_predeclaration("Project::Content", project_content_id)
        predeclarator.add_predeclaration("Timeline::Object", timeline_object_id, 0,
                                         [video_timing_id, audio_timing_id, link_id])
        predeclarator.add_predeclaration("Timeline::Clip", video_clip_id)
        predeclarator.add_predeclaration("File", file_id)
        predeclarator.add_predeclaration("VideoTrack", video_track_id)
        predeclarator.add_predeclaration("AudioTrack", audio_track_id)
        predeclarator.add_predeclaration("Timeline::ClipTiming", video_timing_id, timeline_object_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_video_track_id)
        predeclarator.add_predeclaration("Timeline::Clip", audio_clip_id)
        predeclarator.add_predeclaration("Timeline::ClipTiming", audio_timing_id, timeline_object_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_audio_track_id)
        predeclarator.add_predeclaration("Timeline::Link", link_id, timeline_object_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_titles_track_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_overlay_track_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_overlay2_track_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_effects_track_id)
        predeclarator.add_predeclaration("Timeline::Track", timeline_background_track_id)
        predeclarator.add_predeclaration("EditorCollection::UserObject", editor_collection_id)
        predeclarator.add_predeclaration("Import::Object", import_object_id)

        # Create ProjectContent
        project_content = self.add_object(ProjectContent(project_content_id, timeline_object_id, editor_collection_id))
        self.root_ref = project_content_id  # Set the root reference

        # Create Timeline Object - match the original XML structure
        # Convert channel_layout string to numeric value if needed
        channel_layout = audio_props.get('channel_layout')
        if isinstance(channel_layout, str):
            # Simplified mapping: only use 1 or 2
            channel_layout = 1 if channel_layout.lower() == "mono" else 2
        else:
            # If it's already a number or None
            channel_layout = 1 if channel_layout == 1 else 2

        timeline = self.add_object(
            TimelineObject(timeline_object_id, width, height, frame_rate_n, frame_rate_d,
                           sample_rate=audio_props['sample_rate'],
                           channel_layout=channel_layout))

        # Add tracks to timeline in the same order as original XML
        timeline.add_track(timeline_audio_track_id)
        timeline.add_track(timeline_titles_track_id)
        timeline.add_track(timeline_video_track_id)
        timeline.add_track(timeline_overlay_track_id)
        timeline.add_track(timeline_overlay2_track_id)
        timeline.add_track(timeline_effects_track_id)
        timeline.add_track(timeline_background_track_id)

        # Create File object
        file = self.add_object(
            File(file_id, video_path, filesize, file_ext, duration_frames, video_track_id, audio_track_id))

        # Create Video track with detected properties or defaults
        # For video track frame rate, use 24000/1001 as default (common in editing)
        video_track = self.add_object(
            VideoTrack(video_track_id, file_id, width, height,
                       frame_rate_n=30000,  # Common editing frame rate
                       frame_rate_d=1001,
                       bitrate=int(video_bitrate * 0.6) if video_bitrate else 1286899))  # Estimate from total bitrate

        # Create Audio track with detected properties
        audio_track = self.add_object(
            AudioTrack(audio_track_id, file_id,
                       audio_props['channel_layout'],
                       audio_props['sample_rate'],
                       audio_props['sample_format'],
                       audio_bitrate,
                       codec_id=audio_props['codec_id']))  # Match original XML

        # Create timeline tracks with exact settings from original XML
        self.add_object(TimelineTrack(
            timeline_video_track_id,
            timeline_object_id,
            48,
            linked=True,
            used=True
        ))

        self.add_object(TimelineTrack(
            timeline_audio_track_id,
            timeline_object_id,
            16,
            gapless=True,
            used=True
        ))

        self.add_object(TimelineTrack(
            timeline_titles_track_id,
            timeline_object_id,
            32,
            linked=True,
            used=False  # Match original: Unused track
        ))

        self.add_object(TimelineTrack(
            timeline_overlay_track_id,
            timeline_object_id,
            64,
            linked=True,
            used=True
        ))

        self.add_object(TimelineTrack(
            timeline_overlay2_track_id,
            timeline_object_id,
            64,
            used=False
        ))

        self.add_object(TimelineTrack(
            timeline_effects_track_id,
            timeline_object_id,
            80,
            linked=True,
            used=True
        ))

        self.add_object(TimelineTrack(
            timeline_background_track_id,
            timeline_object_id,
            96,
            linked=True,
            used=False
        ))

        # Create clips with correct IDs and types
        video_clip = self.add_object(
            TimelineClip(video_clip_id, timeline_object_id, 1, filename, file_id, duration_frames))  # type 1 for video
        audio_clip = self.add_object(
            TimelineClip(audio_clip_id, timeline_object_id, 2, filename, file_id, duration_frames))  # type 2 for audio

        # Add clips to timeline
        timeline.add_clip(video_clip_id, {
            "objectId": video_timing_id,
            "track": timeline_audio_track_id,  # Match original XML track position
            "trackLevel": 0,
            "timestamp": 0,
            "sourceDuration": duration_frames,
            "sourcePosition": 0,
            "duration": duration_frames,
            "transitionIn": 0,
            "transitionOut": 0,
            "fadeInDuraion": 0,
            "fadeOutDuraion": 0,
            "reversed": False,
            "timingMode": 0
        })

        timeline.add_clip(audio_clip_id, {
            "objectId": audio_timing_id,
            "track": timeline_video_track_id,  # Match original XML track position
            "trackLevel": 0,
            "timestamp": 0,
            "sourceDuration": duration_frames,
            "sourcePosition": 0,
            "duration": duration_frames,
            "transitionIn": 0,
            "transitionOut": 0,
            "fadeInDuraion": 0,
            "fadeOutDuraion": 0,
            "reversed": False,
            "timingMode": 0
        })

        # Link audio and video clips - match original XML
        timeline.add_link(audio_clip_id, {
            "objectId": link_id,
            "master": video_clip_id,  # Match original XML - video clip is master
            "offset": 0
        })

        # Create EditorCollection and Import objects
        editor_collection = self.add_object(EditorCollectionUserObject(editor_collection_id))
        editor_collection.add_item(import_object_id)

        # Create Import Object with kind=2 for video
        import_obj = self.add_object(ImportObject(import_object_id, filename, video_path, kind=2))

        return self

    def to_xml(self) -> str:
        """Convert the project to XML"""
        root = ET.Element("Archive")

        # Add all objects
        for obj_id, obj in self.objects.items():
            root.append(obj.to_element())

        # Add root reference
        if self.root_ref:
            root_ref = ET.SubElement(root, "RootRef")
            root_ref.set("type", "ObjectRef")
            root_ref.set("value", str(self.root_ref))

        # Format the XML
        xml_string = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="    ")

        # Add XML declaration and return
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml.split('\n', 1)[1]
