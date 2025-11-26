from connect_with_db import get_connection
from flask import abort, jsonify
from math import radians, sin, cos, sqrt, atan2


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

def get_coordinates(airport_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    select latitude, longitude from Airports where airport_id = ?
                """, (airport_id,))
                rows = cur.fetchall()
                output = [{"latitude": row[0], "longitude": row[1]} for row in rows]
    except Exception as e:
        abort(500, f"DB error: {e}")
    return output


def compute_distance_between_airports(coord1, coord2):
    # Radius of Earth in kilometers
    R = 6371.0

    lat1, lon1 = int(coord1['latitude']), int(coord1['longitude'])
    lat2, lon2 = int(coord2['latitude']), int(coord2['longitude'])

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return f"{distance:.2f}"

def compute_emissions(data):
    fly_from_id = data.get("fly_from")
    fly_to_id = data.get("fly_to")
    fly_from_coo = get_coordinates(int(fly_from_id))
    fly_to_coo = get_coordinates(int(fly_to_id))
    
    distance = compute_distance_between_airports(fly_from_coo[0], fly_to_coo[0])
    print(f"===================== {distance}")
    return data

def start():
    """This function returns the output on the /abel page"""
    return "this is the start function"

print(start())