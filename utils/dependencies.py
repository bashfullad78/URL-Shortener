from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from utils.auth_helpers import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_id = decode_token(token)
        return user_id
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")