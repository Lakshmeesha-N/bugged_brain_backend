from typing import Any, Dict, List, Optional
from google.cloud import firestore
from src.core.database import get_db


def save_resume(
    uid: str,
    template_id: str,
    content: Dict[str, Any],
    job_id: Optional[str] = None
) -> str:
    db = get_db()
    resumes_ref = db.collection("users").document(uid).collection("resumes")
    doc_ref = resumes_ref.document()

    data = {
        "template_id": template_id,
        "job_id": job_id,
        "content": content,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(data)
    return doc_ref.id


def get_resume(uid: str, resume_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("users").document(uid).collection("resumes").document(resume_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def list_resumes(uid: str) -> List[Dict[str, Any]]:
    db = get_db()
    docs = db.collection("users").document(uid).collection("resumes").stream()
    resumes = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        resumes.append(data)
    return resumes


def delete_resume(uid: str, resume_id: str) -> None:
    db = get_db()
    db.collection("users").document(uid).collection("resumes").document(resume_id).delete()
