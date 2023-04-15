#!/bin/bash

# e - script stops on error (return != 0)
# u - error if undefined variable
# o pipefail - script fails if one of piped command fails
# x - output each line (debug)
set -euox pipefail

cd fall

# Set the directory containing the videos
video_dir=$(pwd)

# Find all videos matching the "silence-*.mp4" pattern in the directory
videos=$(find "$video_dir" -name "silence-*.mp4")

# Create an empty list of processed videos and directories
processed_list=""

# Loop through each video and split it by frames
for video in $videos; do
    # Get the directory containing the video file
    dir=$(dirname "$video")
    # Get the file name without the ".mp4" extension and add "frames-" prefix
    name=frames-$(basename "$video" .mp4)

    # Split the video by frames using ffmpeg
    ffmpeg -i "$video" "$dir/$name/%06d.png" &

    # Add the processed video and directory to the list
    processed_list+="$video,$dir/$name\n"
done

# Wait for all background ffmpeg processes to finish
wait

# Print the list of processed videos and directories
echo -e "Processed videos and directories:\n$processed_list"
