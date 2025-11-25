from connect_with_db import get_connection
from flask import abort, request, jsonify
from app import app


# New route for arrivals
@app.route("/arrivals", methods=["GET", "POST"])
def arrivals_route():
    return "test"
    # airport = request.args.get("airport")
    # if not airport:
    #     return jsonify({"error": "Missing airport parameter"}), 400
    # arrivals = get_all_arrival_airports_departing_from(airport)
    # return jsonify(arrivals)



def get_all_airports_we_can_depart_from():
    """get all airports from which flights have left"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    select distinct(ai.airport_id), ai.name from flights fl
                    left join airports ai
                    on ai.airport_id = fl.departure_airport_id
                """)
                rows = cur.fetchall()
                output = [{"airportID": row[0], "airportName": row[1]} for row in rows]
    except Exception as e:
        abort(500, f"DB error: {e}")
    return output

def get_all_arrival_airports_departing_from():
    return "hoi"

def get_all_arrival_airports_departing_from__2(airport):
    """based on a given airport, return all airports that the flight can land, based on flight data"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT ai.name
                    FROM airports ai
                    JOIN flights fl ON fl.arrival_airport_id = ai.airport_id
                    WHERE fl.departure_airport_id = (
                        SELECT airport_id FROM airports WHERE name = %s
                    )
                """, (airport,))
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
    except Exception as e:
        abort(500, f"DB error: {e}")
    return [row[0] for row in rows]

def start():
    """This function returns the output on the /abel page"""
    return "this is the start function"



print(start())