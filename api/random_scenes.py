import random
import re
from datetime import timedelta


class RandomScenes:
    def __init__(self, duration_original, duration_audio, output_file):
        self.duration_original = int(duration_original)
        self.duration_audio = int(duration_audio)
        self.output_file = output_file
        self.pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d+')

    def format_seconds(self):
        # Add random seconds between 1 and 4
        seconds = random.randint(1, 4)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        return f"{hours}:{minutes:02d}:{seconds:02d}"

    def scenes(self):
        """
        Generate non-overlapping timestamps
        """
        timestamps = []
        current_position = 0

        while current_position < self.duration_original:
            # Convert current position to timestamp string
            start_time = str(timedelta(seconds=current_position))

            # Generate random duration (1-4 seconds)
            duration_str = self.format_seconds()
            duration_parts = duration_str.split(':')
            duration_seconds = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])

            # Move position forward by duration plus 1 second gap to avoid overlaps
            current_position += duration_seconds + 1

            # Only add if we're still within the original duration
            if current_position <= self.duration_original:
                timestamps.append((start_time, duration_str, duration_seconds))

        return timestamps

    def run(self):
        scenes = self.scenes()
        indexes = list(range(len(scenes)))
        random.shuffle(indexes)

        # Keep track of total duration of selected segments
        total_selected_duration = 0
        end_list = []

        # First pass: Select segments until we're close to the target duration
        for index in indexes:
            if total_selected_duration >= self.duration_audio:
                break

            item = scenes[index]
            start_time, duration_str, duration_seconds = item

            # Only add if it won't exceed the target duration
            if total_selected_duration + duration_seconds <= self.duration_audio:
                total_selected_duration += duration_seconds
                end_list.append((start_time, duration_str))

        # If we still need more duration, find an exact match for the remaining seconds
        # remaining_duration = self.duration_audio - total_selected_duration
        # if remaining_duration > 0:
        #     # Generate a segment with exact remaining duration
        #     dummy_start = str(timedelta(seconds=0))
        #     hours = remaining_duration // 3600
        #     minutes = (remaining_duration % 3600) // 60
        #     seconds = remaining_duration % 60
        #     exact_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
        #
        #     # Add this segment to our list
        #     end_list.append((dummy_start, exact_duration))
        #     total_selected_duration += remaining_duration

        # Sort by start time
        end_list = [(start, duration) for start, duration in sorted(end_list, key=lambda x: x[0])]

        with open(self.output_file, "w") as file_:
            for item in end_list:
                file_.write(f"{item[0]},{item[1]}\n")
