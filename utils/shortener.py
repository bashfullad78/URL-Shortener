import random
import string
from database import get_connection

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def create_unique_short_code() -> str:
    conn = get_connection()
    cursor = conn.cursor()

    while True:
        code = generate_short_code()
        cursor.execute("SELECT id FROM urls WHERE short_code =%s", (code,))
        if not cursor.fetchone():
            conn.close()
            return code
