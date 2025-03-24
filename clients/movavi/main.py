import os

from clients.movavi.generator import MovaviProjectGenerator
from clients.movavi.schema import FilePath, TimelineObject, TimelineTrack, AudioTrack, File, TimelineClip, ImportObject, \
    EditorCollectionUserObject
from settings import BASE_DIR_SETS, BASE_DIR_MOVIES, BASE_DIR
from utils import extract_filename, get_detailed_audio_properties


# Function to create version.xml
def create_version_xml(output_file, project_file="config.xml", version=51):
    """
    Create a version.xml file for Movavi project

    Args:
        output_file (str): Path to save the version.xml file
        project_file (str): Name of the project file (default: config.xml)
        version (int): Version number (default: 51)

    Returns:
        str: Path to the created file
    """
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<versions>
    <project file="{project_file}" version="{version}"/>
</versions>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    return output_file


def get_video_duration_frames(file_path, frame_rate_n=30000, frame_rate_d=1001):
    """
    Get the duration of a video in Movavi timeline units, always rounding up

    Args:
        file_path (FilePath or str): Path to the video file
        frame_rate_n (int): Not used in this implementation
        frame_rate_d (int): Not used in this implementation

    Returns:
        int: Duration in Movavi timeline units, rounded up
    """
    import subprocess
    import math

    # Handle FilePath object or string
    if hasattr(file_path, 'real_path'):
        real_path = str(file_path.real_path)  # Convert Path to string if needed
    else:
        real_path = str(file_path)

    # Get duration in seconds
    cmd = f'ffprobe -i "{real_path}" -show_entries format=duration -v quiet -of csv="p=0"'

    try:
        duration_str = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()

        # Convert to float seconds
        duration_seconds = float(duration_str)

        # Convert to Movavi timeline units (milliseconds * 1000), always rounding up
        frames = math.ceil(duration_seconds * 1000)

        return frames
    except (subprocess.SubprocessError, ValueError) as e:
        raise RuntimeError(f"Failed to get video duration for '{real_path}'.\nCommand: {cmd}\nError: {str(e)}")


# Modify the existing create_movavi_project function to accept additional audio as FilePath
def create_movavi_project(video_path, output_mepx, additional_audio_path=None):
    """
    Create a complete Movavi project (.mepx) file with optional additional audio

    Args:
        video_path (FilePath): Object containing real and config paths for the video
        output_mepx (str): Path to save the .mepx file
        additional_audio_path (FilePath, optional): FilePath containing real and config paths for additional audio

    Returns:
        str: Path to the created .mepx file
    """
    import tempfile
    import zipfile
    import os
    import shutil

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Get video duration in frames
        duration_frames = get_video_duration_frames(video_path.real_path)

        # Generate config.xml
        generator = MovaviProjectGenerator()
        generator.add_video_to_project(
            video_path=video_path.config_path,  # Use the config path for the project
            real_path=video_path.real_path
        )

        # If additional audio file is provided, add it to the project
        if additional_audio_path:
            # Find timeline object ID and audio track ID for positioning the new audio
            timeline_object_id = None
            audio_track_id = None

            for obj_id, obj in generator.objects.items():
                if isinstance(obj, TimelineObject):
                    timeline_object_id = obj_id
                elif isinstance(obj, TimelineTrack) and obj.track_type == 64:  # Audio track type
                    audio_track_id = obj_id

            if timeline_object_id and audio_track_id:
                # Get the existing audio file duration to position the new one after it
                existing_audio_duration = 0
                for clip in generator.objects[timeline_object_id].clips:
                    if clip["value"]["track"] == audio_track_id:
                        existing_audio_duration = max(
                            existing_audio_duration,
                            clip["value"]["timestamp"] + clip["value"]["duration"]
                        )

                # Add the additional audio file
                add_audio_to_project(
                    generator=generator,
                    audio_path=additional_audio_path,
                    timeline_object_id=timeline_object_id,
                    timeline_audio_track_id=audio_track_id,
                    start_timestamp=existing_audio_duration
                )

        config_path = os.path.join(temp_dir, "config.xml")
        xml_content = generator.to_xml()
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        # Also save config.xml to the specified BASE_DIR/ location
        api_config_path = os.path.join(BASE_DIR, "config.xml")
        os.makedirs(os.path.dirname(api_config_path), exist_ok=True)  # Ensure directory exists
        with open(api_config_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        # Generate version.xml
        version_path = os.path.join(temp_dir, "version.xml")
        create_version_xml(version_path)

        # Create .mepx file (which is just a ZIP file with a different extension)
        with zipfile.ZipFile(output_mepx, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(config_path, arcname="config.xml")
            zipf.write(version_path, arcname="version.xml")

        return output_mepx

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


# Define the helper function to add the audio, properly using FilePath
def add_audio_to_project(generator, audio_path, timeline_object_id, timeline_audio_track_id,
                         start_timestamp=0):
    """
    Add an additional audio file to an existing Movavi project

    Args:
        generator (MovaviProjectGenerator): The generator instance
        audio_path (FilePath): FilePath object containing real and config paths for the audio
        timeline_object_id (int): ID of the timeline object
        timeline_audio_track_id (int): ID of the audio track in timeline
        start_timestamp (int): Start position in timeline (in frames)
    """
    # Get file information - use only the base filename, not the full path
    filename = extract_filename(audio_path.config_path)
    filesize = os.path.getsize(audio_path.real_path) if os.path.exists(audio_path.real_path) else 677280
    file_ext = os.path.splitext(audio_path.config_path)[1].lower().lstrip('.')

    # Get duration frames
    duration_frames = get_video_duration_frames(audio_path.real_path)

    # Get detailed audio properties
    audio_props = get_detailed_audio_properties(audio_path.real_path)

    # Create IDs for all objects
    audio_clip_id = generator.get_next_id()
    file_id = generator.get_next_id()
    audio_track_id = generator.get_next_id()
    audio_timing_id = generator.get_next_id()
    import_object_id = generator.get_next_id()

    # Create File object - use config_path for the path in the project file
    generator.add_object(
        File(file_id, audio_path.config_path, filesize, file_ext, duration_frames, None, audio_track_id))

    # Create Audio track with all the detected properties
    generator.add_object(
        AudioTrack(audio_track_id, file_id,
                   audio_props['channel_layout'],
                   audio_props['sample_rate'],
                   audio_props['sample_format'],
                   audio_props['bitrate'],
                   codec_id=audio_props['codec_id']))

    # Create clip - using just the filename, not the full path
    generator.add_object(
        TimelineClip(audio_clip_id, timeline_object_id, 2, filename, file_id, duration_frames))

    # Get the timeline object and add the clip to it
    timeline = generator.objects[timeline_object_id]
    timeline.add_clip(audio_clip_id, {
        "objectId": audio_timing_id,
        "track": timeline_audio_track_id,
        "trackLevel": 0,
        "timestamp": start_timestamp,
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

    # Add import object - use config_path for location in the project
    generator.add_object(ImportObject(import_object_id, filename, audio_path.config_path))

    # Add the import to editor collection
    for obj_id, obj in generator.objects.items():
        if isinstance(obj, EditorCollectionUserObject):
            obj.add_item(import_object_id)
            break


if __name__ == "__main__":
    # Create FilePath objects with real and config paths
    set_name = "adventure"
    movie = "uncharted"

    # Video file path
    video_path = FilePath(
        real_path=BASE_DIR_MOVIES / movie / "original.mp4",
        config_path=r"C:\users\Public\Videos\uncharted.mp4"
    )

    # Additional audio file path
    additional_audio = FilePath(
        real_path=BASE_DIR_MOVIES / movie / "audio.mp3",
        config_path=r"C:\users\Public\Videos\audio.mp3"
    )

    mepx_path = os.path.join(BASE_DIR_SETS, set_name, f"{set_name}.mepx")

    create_movavi_project(
        video_path=video_path,
        output_mepx=mepx_path,
        additional_audio_path=None
    )

    print(f"Created Movavi project with additional audio: {mepx_path}")
