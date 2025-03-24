import asyncio


async def gather_tasks(data: list, func):
    tasks = [func(obj) for obj in data]
    await asyncio.gather(*tasks)


def extract_filename(path_str):
    """
    Extract just the filename from a path string, handling both forward and backward slashes.
    Works with paths that may not exist in the filesystem (like config paths).

    Args:
        path_str (str): Path string that may contain forward or backward slashes

    Returns:
        str: Just the filename portion
    """
    # First split by backslashes, then by forward slashes to handle both separators
    return path_str.split('\\')[-1].split('/')[-1]


# Define the codec mapping dictionary at module level to be reused by both functions
CODEC_MAP = {
    # Audio codecs
    'mp3': 'CODEC_ID_MP3',
    'aac': 'CODEC_ID_AAC',
    'opus': 'CODEC_ID_OPUS',
    'vorbis': 'CODEC_ID_VORBIS',
    'flac': 'CODEC_ID_FLAC',
    'alac': 'CODEC_ID_ALAC',
    'wmav2': 'CODEC_ID_WMAV2',
    'pcm_s16le': 'CODEC_ID_PCM_S16LE',
    'pcm_s24le': 'CODEC_ID_PCM_S24LE',
    'amr_nb': 'CODEC_ID_AMR_NB',

    # Video codecs
    'h264': 'CODEC_ID_H264',
    'hevc': 'CODEC_ID_HEVC',
    'h265': 'CODEC_ID_HEVC',  # Alias for HEVC
    'av1': 'CODEC_ID_AV1',
    'vp9': 'CODEC_ID_VP9',
    'vp8': 'CODEC_ID_VP8',
    'mpeg2video': 'CODEC_ID_MPEG2VIDEO',
    'mpeg4': 'CODEC_ID_MPEG4',
    'mjpeg': 'CODEC_ID_MJPEG',
    'prores': 'CODEC_ID_PRORES'
}

# Sample format mapping
# In Movavi XML format, sample formats need to be numeric values
# 1 = PCM formats, 8 = compressed formats
SAMPLE_FORMAT_MAP = {
    # PCM formats (integer)
    'u8': 1, 's16': 1, 's32': 1, 's64': 1,
    'u8p': 1, 's16p': 1, 's32p': 1, 's64p': 1,

    # PCM formats (float)
    'flt': 1, 'fltp': 8, 'dbl': 1, 'dblp': 1,

    # Compressed formats - all map to 8
    'mp3': 8, 'aac': 8, 'opus': 8, 'vorbis': 8,
    'flac': 8, 'alac': 8, 'wmav2': 8
}


def map_codec_id(codec_name):
    """
    Map a codec name to Movavi's CODEC_ID format.

    Args:
        codec_name (str): The codec name from ffprobe

    Returns:
        str: The Movavi codec ID with "CODEC_ID_" prefix
    """
    codec_name = codec_name.lower()
    return CODEC_MAP.get(codec_name, f"CODEC_ID_{codec_name.upper()}")


def map_sample_format(sample_fmt):
    """
    Map a sample format string to Movavi's numeric format.

    Args:
        sample_fmt (str): The sample format from ffprobe (e.g., "fltp")

    Returns:
        int: The Movavi sample format value (1 for PCM, 8 for compressed)
    """
    sample_fmt = sample_fmt.lower()
    # Default to 8 for unknown formats
    return SAMPLE_FORMAT_MAP.get(sample_fmt, 8)


def get_video_metadata(video_path: str) -> dict:
    """
    Extract video metadata using ffprobe with no default values.
    Raises exceptions if required metadata cannot be extracted.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary containing video metadata
    """
    import subprocess
    import json
    from pathlib import Path

    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Run ffprobe to get video information in JSON format
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]

    try:
        # Execute ffprobe command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parsed_ffmpeg = json.loads(result.stdout)

        # Verify we got some data
        if not parsed_ffmpeg.get("streams"):
            raise ValueError(f"No stream information found in {video_path}")

        # Find video and audio streams
        video_stream = None
        audio_stream = None

        for stream in parsed_ffmpeg.get("streams", []):
            if stream.get("codec_type") == "video" and video_stream is None:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and audio_stream is None:
                audio_stream = stream

        # Initialize metadata dictionary
        metadata = {}

        # Require video stream
        if not video_stream:
            raise ValueError(f"No video stream found in {video_path}")

        # Extract required video metadata
        try:
            metadata["width"] = int(video_stream["width"])
            metadata["height"] = int(video_stream["height"])

            # Extract video codec
            if "codec_name" not in video_stream:
                raise ValueError("Video codec information missing")
            video_codec = video_stream["codec_name"]
            metadata["video_codec_id"] = map_codec_id(video_codec)

            # Parse frame rate
            if "r_frame_rate" not in video_stream:
                raise ValueError("Frame rate information missing")

            fr_parts = video_stream["r_frame_rate"].split('/')
            if len(fr_parts) == 2:
                metadata["frame_rate_n"] = int(fr_parts[0])
                metadata["frame_rate_d"] = int(fr_parts[1])
            else:
                metadata["frame_rate_n"] = int(float(fr_parts[0]))
                metadata["frame_rate_d"] = 1

            # Extract duration
            if "duration" in video_stream:
                # Convert duration to Movavi's format (seems to be approximately 100 units per second)
                duration_sec = float(video_stream["duration"])
                metadata["duration_frames"] = int(duration_sec * 1000)
            elif "nb_frames" in video_stream:
                # If we have frame count, convert to approximate Movavi units
                # assuming standard rate (25 frames ≈ 1 second)
                frame_count = int(video_stream["nb_frames"])
                # Convert frames to seconds, then to Movavi units
                approx_seconds = frame_count / 25
                metadata["duration_frames"] = int(approx_seconds * 100)
            else:
                raise ValueError("Video duration information missing")

            # Video bitrate
            if "bit_rate" in video_stream:
                metadata["video_bitrate"] = int(video_stream["bit_rate"])
            elif "format" in parsed_ffmpeg and "bit_rate" in parsed_ffmpeg["format"]:
                # Use format bitrate as a fallback
                format_bitrate = int(parsed_ffmpeg["format"]["bit_rate"])
                # Assume video is 80% of total bitrate if audio is present
                metadata["video_bitrate"] = int(format_bitrate * 0.8) if audio_stream else format_bitrate
            else:
                raise ValueError("Video bitrate information missing")

        except KeyError as e:
            raise ValueError(f"Required video metadata missing: {e}")

        # Handle audio metadata
        if audio_stream:
            try:
                # Audio bitrate
                if "bit_rate" in audio_stream:
                    metadata["audio_bitrate"] = int(audio_stream["bit_rate"])
                else:
                    raise ValueError("Audio bitrate information missing")

                # Get required audio properties
                sample_rate = audio_stream.get("sample_rate")
                channel_layout = audio_stream.get("channel_layout")
                sample_format = audio_stream.get("sample_fmt")
                codec_name = audio_stream.get("codec_name")

                if not all([sample_rate, channel_layout, sample_format, codec_name]):
                    missing = []
                    if not sample_rate: missing.append("sample_rate")
                    if not channel_layout: missing.append("channel_layout")
                    if not sample_format: missing.append("sample_format")
                    if not codec_name: missing.append("codec_name")
                    raise ValueError(f"Missing audio properties: {', '.join(missing)}")

                # Map the codec name to Movavi's format
                codec_id = map_codec_id(codec_name)

                # Store audio properties
                metadata["audio_props"] = {
                    "codec_id": codec_id,
                    "sample_rate": int(sample_rate),
                    "sample_format": map_sample_format(sample_format),
                    "channel_layout": channel_layout
                }
            except KeyError as e:
                raise ValueError(f"Required audio metadata missing: {e}")
        else:
            raise ValueError(f"No audio stream found in {video_path}")

        return metadata

    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Error running ffprobe: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error parsing ffprobe output: {e}")
    except Exception as e:
        raise RuntimeError(f"Error in get_video_metadata: {str(e)}")


def get_detailed_audio_properties(file_path):
    """
    Get comprehensive audio properties from a media file without using default values.
    Raises exceptions if required properties cannot be extracted.

    Args:
        file_path (FilePath or str): Path to the media file

    Returns:
        dict: Dictionary containing audio properties including:
            - sample_rate: Audio sample rate
            - channel_layout: Audio channel layout (number of channels)
            - codec_id: Movavi codec ID (e.g., "CODEC_ID_MP3", "CODEC_ID_AAC")
            - sample_format: Audio sample format (e.g., 1 for PCM, 8 for compressed formats)
            - bitrate: Audio bitrate in bits per second
    """
    import subprocess
    import json
    import os

    # Handle FilePath object or string
    if hasattr(file_path, 'real_path'):
        real_path = str(file_path.real_path)
    else:
        real_path = str(file_path)

    # Check if file exists
    if not os.path.exists(real_path):
        raise FileNotFoundError(f"Audio file not found: {real_path}")

    # Use ffprobe to get detailed audio information
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,codec_type,sample_rate,channels,bits_per_sample,bit_rate,channel_layout",
        "-of", "json",
        real_path
    ]

    try:
        # Use subprocess.run instead of check_output with shell=True for better security
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        audio_info = json.loads(result.stdout)

        # Verify we have audio streams
        if 'streams' not in audio_info or not audio_info['streams']:
            raise ValueError(f"No audio stream found in {real_path}")

        stream = audio_info['streams'][0]

        # Initialize properties dictionary
        properties = {}

        # Get sample rate (required)
        if 'sample_rate' not in stream:
            raise ValueError("Sample rate information missing")
        properties['sample_rate'] = int(stream['sample_rate'])

        # Get channel layout/count (required)
        if 'channels' not in stream:
            raise ValueError("Channel information missing")

        # Set channel_layout as an integer based on channel count
        channel_count = int(stream['channels'])
        # Simplified channel layout mapping: 1 for mono, 2 for everything else
        properties['channel_layout'] = 1 if channel_count == 1 else 2

        # Get bitrate (required)
        if 'bit_rate' not in stream or not stream['bit_rate']:
            # Try format section as fallback
            try:
                format_info = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=bit_rate", "-of", "json", real_path],
                    capture_output=True, text=True, check=True
                )
                format_data = json.loads(format_info.stdout)
                if 'format' in format_data and 'bit_rate' in format_data['format'] and format_data['format'][
                    'bit_rate']:
                    properties['bitrate'] = int(format_data['format']['bit_rate'])
                else:
                    raise ValueError("Audio bitrate information missing")
            except Exception:
                raise ValueError("Audio bitrate information missing")
        else:
            properties['bitrate'] = int(stream['bit_rate'])

        # Determine sample format (required)
        if 'sample_fmt' in stream:
            # Use the shared mapping function to convert the format string to a numeric value
            properties['sample_format'] = map_sample_format(stream['sample_fmt'])
        else:
            # Fallback to determining based on codec type
            if 'codec_name' not in stream:
                raise ValueError("Codec information missing")

            codec_name = stream['codec_name'].lower()
            # Default to 8 for most audio codecs except raw PCM types
            properties['sample_format'] = 1 if codec_name.startswith('pcm_') else 8

        # Map codec name to Movavi codec ID (required) using the shared mapping function
        if 'codec_name' not in stream:
            raise ValueError("Codec name information missing")

        codec_name = stream['codec_name']
        properties['codec_id'] = map_codec_id(codec_name)

        return properties

    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Error running ffprobe: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error parsing ffprobe output: {e}")
    except ValueError as e:
        # Re-raise ValueError exceptions
        raise
    except Exception as e:
        raise RuntimeError(f"Error in get_detailed_audio_properties: {str(e)}")
