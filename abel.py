from connect_with_db import get_connection
from flask import abort

def get_info():
    """some function that returns info from db"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT(name) from dbo.Airports;
                """)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
    except Exception as e:
        abort(500, f"DB error: {e}")
    return cols

def start():
    """This function returns the output on the /abel page"""
    return get_info()

start()