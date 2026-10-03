from datetime import date, datetime
from typing import Any, Dict, List, Optional
from google.cloud import firestore
from src.core.database import get_db


class JobNotFound(Exception):
    """Raised when a job is not found."""
    pass


def create_job(data: Dict[str, Any]) -> str:
    db = get_db()
    jobs_ref = db.collection("jobs")
    doc_ref = jobs_ref.document()

    job_data = dict(data)
    if isinstance(job_data.get("expires_at"), (date, datetime)):
        job_data["expires_at"] = job_data["expires_at"].isoformat()
    elif job_data.get("expires_at") is None:
        job_data["expires_at"] = None

    if "apply_url" in job_data:
        job_data["apply_url"] = str(job_data["apply_url"])

    job_data.setdefault("active", True)
    job_data.setdefault("source", "admin")
    job_data["created_at"] = firestore.SERVER_TIMESTAMP
    job_data["updated_at"] = firestore.SERVER_TIMESTAMP

    doc_ref.set(job_data)
    return doc_ref.id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("jobs").document(job_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def update_job(job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise JobNotFound(f"Job with id {job_id} not found.")

    update_data = {k: v for k, v in data.items() if v is not None}
    if "expires_at" in update_data:
        if isinstance(update_data["expires_at"], (date, datetime)):
            update_data["expires_at"] = update_data["expires_at"].isoformat()
    if "apply_url" in update_data:
        update_data["apply_url"] = str(update_data["apply_url"])

    update_data["updated_at"] = firestore.SERVER_TIMESTAMP
    doc_ref.update(update_data)

    return get_job(job_id)


def set_active(job_id: str, active: bool) -> Dict[str, Any]:
    return update_job(job_id, {"active": active})


def delete_job(job_id: str) -> None:
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise JobNotFound(f"Job with id {job_id} not found.")
    doc_ref.delete()


def list_jobs(
    job_type: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    include_inactive: bool = False
) -> Dict[str, Any]:
    db = get_db()
    query = db.collection("jobs")

    if not include_inactive:
        query = query.where(filter=firestore.FieldFilter("active", "==", True))

    if job_type:
        query = query.where(filter=firestore.FieldFilter("job_type", "==", job_type))

    if category:
        query = query.where(filter=firestore.FieldFilter("category", "==", category))

    # Fetch at most 500 documents
    docs = query.limit(500).stream()

    today_str = date.today().isoformat()
    matched_jobs = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # 1. Filter expired jobs in Python unless include_inactive
        expires_at = data.get("expires_at")
        if not include_inactive and expires_at:
            exp_date_str = str(expires_at)[:10]
            if exp_date_str < today_str:
                continue

        # 2. Location case-insensitive substring match
        if location:
            loc_val = data.get("location", "").lower()
            if location.lower() not in loc_val:
                continue

        # 3. Query string match against title, company, description
        if q:
            q_lower = q.lower()
            title = data.get("title", "").lower()
            company = data.get("company", "").lower()
            description = data.get("description", "").lower()
            if (q_lower not in title) and (q_lower not in company) and (q_lower not in description):
                continue

        matched_jobs.append(data)

    # Sort by created_at descending in Python
    def get_sort_key(item):
        ca = item.get("created_at")
        if ca is None:
            return ""
        if isinstance(ca, (datetime, date)):
            return ca.isoformat()
        return str(ca)

    matched_jobs.sort(key=get_sort_key, reverse=True)

    total = len(matched_jobs)
    paginated_items = matched_jobs[offset: offset + limit]

    return {
        "items": paginated_items,
        "total": total
    }
