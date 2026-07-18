from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from models.schemas import URLCreate, URLOut
from database import get_connection
from utils.shortener import create_unique_short_code
from utils.dependencies import get_current_user

router = APIRouter()
@router.post("/urls")
def create_short_url(url: URLCreate, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    code = create_unique_short_code()
    cursor.execute("INSERT INTO urls (user_id, original_url, short_code) VALUES (%s, %s, %s)", (user_id, url.original_url, code))
    conn.commit()
    conn.close()
    return {"short_code": code, "original_url": url.original_url}

@router.get("/urls")
def get_urls(user_id: int = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urls WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    urls = []
    for row in rows:
        urls.append({
            "id": row[0],
            "user_id": row[1],
            "original_url": row[2],
            "short_code": row[3],
            "click_count": row[4],
            "created_at": str(row[5])
        })
    return urls

@router.get("/{short_code}")
def redirect_url(short_code: str, request: Request):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, original_url FROM urls WHERE short_code = %s", (short_code,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Short URL not found")

    url_id, original_url = row

    cursor.execute(
        "INSERT INTO clicks (url_id, user_agent, ip_address) VALUES (%s, %s, %s)",
        (url_id, request.headers.get("user-agent"), request.client.host)
    )
    cursor.execute("UPDATE urls SET click_count = click_count + 1 WHERE id = %s", (url_id,))

    conn.commit()
    conn.close()
    return RedirectResponse(url=original_url)

@router.delete("/urls/{url_id}")
def delete_url(url_id: int, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM urls WHERE id = %s AND user_id = %s", (url_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="URL not found")

    cursor.execute("DELETE FROM urls WHERE id = %s", (url_id,))
    conn.commit()
    conn.close()
    return {"message": "URL deleted successfully"}