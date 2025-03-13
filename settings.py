import os

HOST_API_URL = os.environ['HOST_API_URL']
HOST_API_TOKEN = os.environ['HOST_API_TOKEN']
BUCKET_VIDEO = os.environ['BUCKET_VIDEO']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR_MOVIES = os.path.join(BASE_DIR, "movies")
BASE_DIR_SETS = os.path.join(BASE_DIR_MOVIES, "sets")
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
