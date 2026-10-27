from fastapi import APIRouter, HTTPException, Depends
from models.schemas import AnalyticsSummary, DailyAnalyticsPoint
from utils.dependencies import get_current_user
from database import get_connection

router = APIRouter()

@router.get("/urls/{url_id}/analytics/summary", response_model=AnalyticsSummary)
def get_summary(url_id: int, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM urls WHERE id = %s AND user_id = %s", (url_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="URL not found")

    cursor.execute(
        "SELECT COUNT(*), MIN(clicked_at), MAX(clicked_at) FROM clicks WHERE url_id = %s",
        (url_id,)
    )
    row = cursor.fetchone()
    conn.close()

    return {
        "url_id": url_id,
        "total_clicks": row[0],
        "first_click": row[1],
        "last_click": row[2],
    }

@router.get("/urls/{url_id}/analytics/daily", response_model=list[DailyAnalyticsPoint])
def get_daily(url_id: int, user_id: int = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM urls WHERE id = %s AND user_id = %s", (url_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="URL not found")

    cursor.execute(
        "SELECT DATE(clicked_at), COUNT(*) FROM clicks WHERE url_id = %s GROUP BY DATE(clicked_at) ORDER BY DATE(clicked_at)",
        (url_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"date": row[0], "clicks": row[1]} for row in rows]