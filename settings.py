import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

HOST_API_URL = os.environ['HOST_API_URL']
HOST_API_TOKEN = os.environ['HOST_API_TOKEN']
BUCKET_VIDEO = os.environ['BUCKET_VIDEO']
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR_MOVIES = Path(BASE_DIR / "movies")
BASE_DIR_SETS = Path(BASE_DIR_MOVIES / "sets")
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
WORKERS = 20
