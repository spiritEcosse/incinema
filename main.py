# This is a sample Python script.
import json
import random
import sys
from datetime import datetime

from api.get_meta_data import GetMetaData


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def handler(event: dict, context: {}) -> dict:
    GetMetaData(event=event).run()
    return {}


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    file_cut, file_cut_duration = sys.argv[1], sys.argv[2]

    with open(file_cut, 'r') as file_:
        scenes = file_.read().splitlines()
    #scenes[0] = "00:00:00.0"
    scenes.pop(0)
    scenes_with_distance = []
    for s, e in zip(scenes, scenes[1:]):
        s = datetime.strptime(s, '%H:%M:%S.%f')
        e = datetime.strptime(e, '%H:%M:%S.%f')
        distance = e - s
        scenes_with_distance.append(
            (s, e, distance, distance.total_seconds())
        )

    indexes = list(range(len(scenes_with_distance)))
    random.shuffle(indexes)
    total_time = 0
    end_list = []

    for index in indexes:
        item = scenes_with_distance[index]
        if item[3] >= 2:
            end_list.append(item)
            total_time += item[3]

            if total_time >= 60:
                break

    end_list = [(s.strftime("%H:%M:%S.%f"), str(d)) for s, e, d, t in sorted(end_list, key=lambda x: x[0])]
    print(end_list, len(end_list), total_time)

    with open(file_cut_duration, "w") as file_:
        for item in end_list:
            file_.write(f"{item[0]},{item[1]}\n")
