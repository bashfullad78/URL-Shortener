from fastapi import APIRouter, HTTPException
from models.schemas import UserCreate, UserLogin
from utils.auth_helpers import hash_password, verify_password, create_token
from database import get_connection

router = APIRouter(prefix="/auth")

@router.post("/register")
def register(user: UserCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)",
        (user.username, user.email, hashed)
    )
    conn.commit()
    conn.close()
    return {"message": "User registered successfully"}

@router.post("/login")
def login(user: UserLogin):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, hashed_password FROM users WHERE email = %s", (user.email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, hashed_password = row

    if not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user_id)
    return {"access_token": token, "token_type": "bearer"}