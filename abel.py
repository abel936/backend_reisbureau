from connect_with_db import get_connection
from flask import abort, jsonify


def get_all_airports_we_can_depart_from():
    """get all airports from which flights have departed"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT(ai.airport_id), ai.name 
                    FROM flights fl
                    LEFT JOIN airports ai
                    ON ai.airport_id = fl.departure_airport_id
                """)
                rows = cur.fetchall()
                output = [{"airportID": row[0], "airportName": row[1]} for row in rows]
    except Exception as e:
        abort(500, f"DB error: {e}")
    return output

def get_all_arrival_airports_departing_from(data):
    """based on a given airport, return all airports that the flight can arrive, based on flight data"""
    selected_airport = int(data.get('fly_from'))
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT(ai.airport_id), ai.name
                    FROM airports ai
                    JOIN flights fl ON fl.arrival_airport_id = ai.airport_id
                    WHERE fl.departure_airport_id = ?
                """, (selected_airport,))
                rows = cur.fetchall()
                output = [{"airportID": row[0], "airportName": row[1]} for row in rows]
    except Exception as e:
        abort(500, f"DB error: {e}")
    return output

def start():
    """This function returns the output on the /abel page"""
    return "this is the start function"



print(start())