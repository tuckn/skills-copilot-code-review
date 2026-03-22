"""
Announcement endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import ASCENDING

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    expiration_date: datetime
    start_date: Optional[datetime] = None


class AnnouncementUpdatePayload(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    expiration_date: datetime
    start_date: Optional[datetime] = None


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    start_date = document.get("start_date")
    expiration_date = document.get("expiration_date")

    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

    if isinstance(expiration_date, str):
        expiration_date = datetime.fromisoformat(
            expiration_date.replace("Z", "+00:00")
        )

    return {
        "id": str(document["_id"]),
        "message": document["message"],
        "start_date": start_date.isoformat() if start_date else None,
        "expiration_date": expiration_date.isoformat(),
    }


def _require_authenticated_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


@router.get("", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get active announcements for display in the UI"""
    now = datetime.now(timezone.utc)

    query = {
        "$and": [
            {"expiration_date": {"$gte": now}},
            {
                "$or": [
                    {"start_date": None},
                    {"start_date": {"$lte": now}}
                ]
            }
        ]
    }

    announcements = announcements_collection.find(query).sort("expiration_date", ASCENDING)
    return [_serialize_announcement(item) for item in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for management UI (requires teacher authentication)"""
    _require_authenticated_teacher(teacher_username)

    announcements = announcements_collection.find({}).sort("expiration_date", ASCENDING)
    return [_serialize_announcement(item) for item in announcements]


@router.post("", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement (requires teacher authentication)"""
    _require_authenticated_teacher(teacher_username)

    start_date = _normalize_datetime(payload.start_date) if payload.start_date else None
    expiration_date = _normalize_datetime(payload.expiration_date)

    if start_date and start_date >= expiration_date:
        raise HTTPException(status_code=400, detail="Start date must be before expiration date")

    result = announcements_collection.insert_one({
        "message": payload.message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
    })

    created = announcements_collection.find_one({"_id": result.inserted_id})
    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdatePayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement (requires teacher authentication)"""
    _require_authenticated_teacher(teacher_username)

    start_date = _normalize_datetime(payload.start_date) if payload.start_date else None
    expiration_date = _normalize_datetime(payload.expiration_date)

    if start_date and start_date >= expiration_date:
        raise HTTPException(status_code=400, detail="Start date must be before expiration date")

    from bson import ObjectId

    try:
        object_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")

    result = announcements_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "message": payload.message.strip(),
                "start_date": start_date,
                "expiration_date": expiration_date,
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": object_id})
    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement (requires teacher authentication)"""
    _require_authenticated_teacher(teacher_username)

    from bson import ObjectId

    try:
        object_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")

    result = announcements_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
