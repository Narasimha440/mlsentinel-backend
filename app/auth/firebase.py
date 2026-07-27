import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

security = HTTPBearer()

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")