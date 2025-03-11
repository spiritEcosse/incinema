import json
from pathlib import Path

from api.get_meta_data import GetMetaData


async def handler(json_file_path: Path):
    with json_file_path.open("r") as file:
        data = json.load(file)
    await GetMetaData(data=data).run()
