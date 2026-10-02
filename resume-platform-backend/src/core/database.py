import functools
from google.cloud import firestore
from src.core.config import settings


@functools.lru_cache(maxsize=1)
def get_db() -> firestore.Client:
    return firestore.Client(project=settings.GCP_PROJECT_ID)
