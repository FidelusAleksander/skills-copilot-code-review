"""
Announcement endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

def require_auth(username: str) -> Dict[str, Any]:
    """Dependency to require a valid signed-in user"""
    user = teachers_collection.find_one({"_id": username})
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

@router.get("", response_model=List[Dict[str, Any]])
def get_announcements(active_only: bool = False) -> List[Dict[str, Any]]:
    """Get all announcements, or only active ones if active_only is True"""
    now = datetime.utcnow().isoformat()
    query = {}
    if active_only:
        query = {
            "$or": [
                {"start_date": None},
                {"start_date": {"$lte": now}}
            ],
            "expiration_date": {"$gte": now}
        }
    anns = list(announcements_collection.find(query))
    for ann in anns:
        ann["id"] = str(ann.get("_id", ""))
        ann.pop("_id", None)
    return anns

@router.post("", response_model=Dict[str, Any])
def create_announcement(
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None,
    username: str = Depends(require_auth)
):
    """Create a new announcement (signed-in users only)"""
    if not expiration_date:
        raise HTTPException(status_code=400, detail="Expiration date required")
    ann = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username["username"]
    }
    result = announcements_collection.insert_one(ann)
    ann["id"] = str(result.inserted_id)
    return ann

@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    message: Optional[str] = None,
    expiration_date: Optional[str] = None,
    start_date: Optional[str] = None,
    username: str = Depends(require_auth)
):
    """Update an announcement (signed-in users only)"""
    update = {}
    if message is not None:
        update["message"] = message
    if expiration_date is not None:
        update["expiration_date"] = expiration_date
    if start_date is not None:
        update["start_date"] = start_date
    if not update:
        raise HTTPException(status_code=400, detail="No update fields provided")
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    ann = announcements_collection.find_one({"_id": announcement_id})
    ann["id"] = str(ann.get("_id", ""))
    ann.pop("_id", None)
    return ann

@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    username: str = Depends(require_auth)
):
    """Delete an announcement (signed-in users only)"""
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted"}
