from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"

DATABASE_URL = "sqlite:///./data/attendance.db"
FACE_THRESHOLD = 0.80
