import ipaddress

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from models.schemas import MessageResponse, URLCreate, URLOut
from database import get_connection
from utils.rate_limit import URL_CREATE_LIMIT, limiter, user_or_ip_key
from utils.shortener import create_unique_short_code
from utils.dependencies import get_current_user

router = APIRouter()


def _client_ip(request: Request):
    """Client IP for click recording, or None when unavailable.

    ASGI servers always provide a real address, but test transports (and some
    proxies) report names like "testclient" that the INET column rejects.
    """
    host = request.client.host if request.client else None
    if not host:
        return None
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return None
    return host

@router.post("/urls", response_model=URLOut)
@limiter.limit(URL_CREATE_LIMIT, key_func=user_or_ip_key)
def create_short_url(
    url: URLCreate,
    request: Request,
    response: Response,
    user_id: int = Depends(get_current_user),
):
    conn = get_connection()
    cursor = conn.cursor()
    code = create_unique_short_code(conn)
    cursor.execute(
        "INSERT INTO urls (user_id, original_url, short_code) "
        "VALUES (%s, %s, %s) "
        "RETURNING id, short_code, original_url, click_count, created_at",
        (user_id, url.original_url, code),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return {
        "id": row[0],
        "short_code": row[1],
        "original_url": row[2],
        "click_count": row[3],
        "created_at": row[4],
    }

@router.get("/urls", response_model=list[URLOut])
def get_urls(user_id: int = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, short_code, original_url, click_count, created_at "
        "FROM urls WHERE user_id = %s",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "short_code": row[1],
            "original_url": row[2],
            "click_count": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]

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
        (url_id, request.headers.get("user-agent"), _client_ip(request))
    )
    cursor.execute("UPDATE urls SET click_count = click_count + 1 WHERE id = %s", (url_id,))

    conn.commit()
    conn.close()
    return RedirectResponse(url=original_url)

@router.delete("/urls/{url_id}", response_model=MessageResponse)
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