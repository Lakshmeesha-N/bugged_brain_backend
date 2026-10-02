from typing import Optional
from src.core.database import get_db


def get_profile(uid: str) -> Optional[dict]:
    db = get_db()
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None


def save_profile(uid: str, data: dict) -> dict:
    db = get_db()
    db.collection("users").document(uid).set(data, merge=True)
    return data


def delete_profile(uid: str) -> None:
    db = get_db()
    db.collection("users").document(uid).delete()
