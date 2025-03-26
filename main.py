import glob
import json
import re
from pathlib import Path

from api.get_meta_data import GetMetaData
from clients.aws import AWSS3Client
from settings import BASE_DIR_SETS, BUCKET_VIDEO


async def upload_set(_set):
    # Create file mappings using a loop
    file_mappings = []
    full_path_set = BASE_DIR_SETS / _set
    # First get all files with a dash prefix
    all_files = glob.glob(str(full_path_set / "*.*"))

    # Then filter out the ones with fps patterns you want to exclude
    filtered_files = [
        Path(f) for f in all_files if not re.search(r".*-\d+fps\.mp4$", f)
    ]

    for file_path in filtered_files:
        s3_key = f"sets/{_set}/{file_path.name}"
        file_mappings.append((file_path, s3_key))

    client = AWSS3Client(file_mappings, BUCKET_VIDEO)
    await client.upload_files()


async def handler(json_file_path: Path):
    with json_file_path.open("r") as file:
        data = json.load(file)
    await GetMetaData(data=data).run()
