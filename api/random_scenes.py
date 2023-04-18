import random
import re
from datetime import timedelta

MAX_SECONDS = 1


class RandomScenes:
    def __init__(self, duration, output_file):
        self.duration = duration
        self.output_file = output_file
        self.pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d+')

    def scenes(self):
        """
        >>> rs = RandomScenes(duration=10.5, output_file="")
        >>> rs.scenes()
        [('0:00:00', '0:00:01'), ('0:00:01', '0:00:01'), ('0:00:02', '0:00:01'), ('0:00:03', '0:00:01'), ('0:00:04', '0:00:01'), ('0:00:05', '0:00:01'), ('0:00:06', '0:00:01'), ('0:00:07', '0:00:01'), ('0:00:08', '0:00:01'), ('0:00:09', '0:00:01')]
        """
        return [(f"{timedelta(seconds=sec)}", "0:00:01") for sec in range(int(self.duration))[:60*50]]

    def run(self):
        scenes = self.scenes()
        indexes = list(range(len(scenes)))
        random.shuffle(indexes)
        total_time = 0
        end_list = []

        for index in indexes:
            item = scenes[index]
            end_list.append(item)
            total_time += 1

            if total_time >= 120:
                break

        end_list = [(start, duration) for start, duration in sorted(end_list, key=lambda x: x[0])]

        with open(self.output_file, "w") as file_:
            for item in end_list:
                file_.write(f"{item[0]},{item[1]}\n")
