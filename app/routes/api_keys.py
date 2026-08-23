import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.api_key import APIKey
from app.models.project import Project
from app.auth.firebase import verify_firebase_token

router = APIRouter()


class CreateKeyRequest(BaseModel):
    label: str = "Untitled key"


@router.get("/api-keys")
def list_keys(db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    """
    Lists this user's API keys. The full key is never returned here —
    only a masked preview, since the raw key is only shown once at creation.
    """
    keys = db.query(APIKey).filter(APIKey.firebase_uid == user["uid"], APIKey.revoked == False).all()
    return {
        "keys": [
            {
                "id": k.id,
                "label": k.label,
                "preview": f"{k.key[:8]}...{k.key[-4:]}",
                "created_at": k.created_at.isoformat(),
            }
            for k in keys
        ]
    }


@router.post("/api-keys")
def create_key(req: CreateKeyRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    """
    Generates a new API key for the authenticated user. The raw key is
    returned ONLY in this response — the frontend must show it once and
    warn the user to copy it, since it can't be retrieved again after this.
    """
    new_key = "mls_" + secrets.token_hex(24)
    entry = APIKey(key=new_key, firebase_uid=user["uid"], label=req.label)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "label": entry.label,
        "key": new_key,  # full key, shown once
        "created_at": entry.created_at.isoformat(),
    }


@router.delete("/api-keys/{key_id}")
def revoke_key(key_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    key_entry = db.query(APIKey).filter(APIKey.id == key_id, APIKey.firebase_uid == user["uid"]).first()

    if not key_entry:
        raise HTTPException(status_code=404, detail="API key not found")

    key_entry.revoked = True
    db.commit()
    return {"success": True, "message": "API key revoked"}