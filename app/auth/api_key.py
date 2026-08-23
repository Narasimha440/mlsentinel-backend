from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.api_key import APIKey

def verify_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)) -> str:

    key_entry = db.query(APIKey).filter(APIKey.key == x_api_key, APIKey.revoked == False).first()

    if not key_entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key"
        )

    return {"firebase_uid": key_entry.firebase_uid, "default_ml_model_id": key_entry.default_ml_model_id}

