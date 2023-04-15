import os

HOST_API_URL = os.environ['HOST_API_URL']
HOST_API_TOKEN = os.environ['HOST_API_TOKEN']
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
AVAILABLE_SYMBOLS = '[^a-zA-Z0-9_]'
os.environ["PATH"] += os.pathsep + "/opt/homebrew/Cellar/ffmpeg/5.1.2_6/bin"
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"
BUCKET_VIDEO = os.environ.get("BUCKET_VIDEO")
VOICE_API = os.environ.get("VOICE_API")
