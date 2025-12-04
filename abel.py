from connect_with_db import get_connection
from flask import Flask, request, Response, abort
from math import radians, sin, cos, sqrt, atan2
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from MLmodel import predict_capacity_percentage

# Load environment variables and initialize client globally
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants
EMISSION_FACTOR = 3.203
PASSENGER_FACTOR = 0.0365

def execute_query(query: str, params: tuple = ()):
    """
    Execute an SQL query and return results. Handles DB errors and connection cleanup.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                if rows: 
                    return rows 
                return abort(404, "QUERY yields no results")
    except Exception as e:
        abort(500, f"Database error: {e}")


def get_all_airports_we_can_depart_from():
    """
    Get all airports flight have/will depart from
    """
    rows = execute_query("""
        SELECT DISTINCT(ai.airport_id), ai.name 
        FROM flights fl
        LEFT JOIN airports ai ON ai.airport_id = fl.departure_airport_id
    """)
    return [{"airportID": row[0], "airportName": row[1]} for row in rows]

def get_all_airline_names():
    """
    Get all airline names
    """
    rows = execute_query("""
        select distinct(airline_id), name from airlines    
    """)
    return [{"airlineID": row[0], "airlineName": row[1]} for row in rows]


def get_all_arrival_airports_departing_from(data):
    """
    Get all airports flights have/will arrive at based on departure airport
    """
    selected_airport = int(data.get('fly_from'))
    rows = execute_query("""
        SELECT DISTINCT(ai.airport_id), ai.name
        FROM airports ai
        JOIN flights fl ON fl.arrival_airport_id = ai.airport_id
        WHERE fl.departure_airport_id = ?
    """, (selected_airport,))
    return [{"airportID": row[0], "airportName": row[1]} for row in rows]


def get_coordinates(airport_id):
    """
    Get coordinates of an airport based on its ID
    """
    rows = execute_query("""
        SELECT latitude, longitude FROM Airports WHERE airport_id = ?
    """, (airport_id,))
    return [{"latitude": row[0], "longitude": row[1]} for row in rows][0]


def compute_distance_between_airports(coord1, coord2):
    """
    Based on two sets of coordinates, compute the distance.
    Take into consideration the curvature of the earth
    """
    R = 6371.0
    lat1, lon1 = map(radians, [float(coord1['latitude']), float(coord1['longitude'])])
    lat2, lon2 = map(radians, [float(coord2['latitude']), float(coord2['longitude'])])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def create_departure_datetime(departure_date, departure_time):
    """
    Return datetime variable for departure date and time
    """
    if departure_date:
        # Combine date and time into one string
        departure_str = f"{departure_date} {departure_time}"
        
        # Parse into a datetime object
        departure_datetime = datetime.strptime(departure_str, "%Y-%m-%d %H:%M")
    else:
        departure_datetime = None
    return departure_datetime


def match_with_db(fly_from_id, fly_to_id, departure_datetime, flight_number, airline_name):
    """
    Check if the input variables can be linked to an entry in our DB.
    If query yields resutls, return the capacity of the FIRST row.
    """

    query = """
    SELECT CAST(ROUND((seats_total - seats_available)*100.0/seats_total, 2) AS DECIMAL(5,2)) AS fill_percentage
    FROM flights fl
    LEFT JOIN airlines ail ON fl.airline_id = ail.airline_id
    WHERE departure_airport_id = ?
    AND arrival_airport_id = ?
    """

    # Dynamic conditions
    params = [fly_from_id, fly_to_id]
    if departure_datetime:
        query += " AND CONVERT(DATE, scheduled_departure) = CONVERT(DATE, ?)"
        params.append(departure_datetime)
    if flight_number:
        query += " AND flight_number = ?"
        params.append(flight_number)
    if airline_name:
        query += " AND ail.name = ?"
        params.append(airline_name)

    try:
        query_result = execute_query(query, tuple(params))
        print(f"=========================={params}, {query}, {query_result}")
        return float(query_result[0][0])
    except:
        return None



def compute_emissions(data):
    fly_from_id = int(data.get("fly_from"))
    fly_to_id = int(data.get("fly_to"))
    departure_date = data.get("departure_date") or ""
    departure_time = data.get("departure_time") or "12:00"
    airline_name = data.get("airline_name") or ""
    flight_number = data.get("flight_number") or ""
    departure_datetime = create_departure_datetime(departure_date, departure_time)

    departure_airport = execute_query("""select name from airports where airport_id = ?""", (fly_from_id,))[0][0]
    arrival_airport = execute_query("""select name from airports where airport_id = ?""", (fly_to_id,))[0][0]

    flight_is_in_db = match_with_db(fly_from_id, fly_to_id, departure_datetime, flight_number, airline_name)

    if not flight_is_in_db:
        PERCENTAGE_FILLED = predict_capacity_percentage(flight_number, departure_datetime, airline_name, departure_airport, arrival_airport)
        filled_perspective = "Deze vlucht staat niet in onze database, vandaar dat we een voorspelling doen van capaciteit obv geleverde gegevens gebruikmakende van automatische ML."
    else:
        PERCENTAGE_FILLED = flight_is_in_db
        filled_perspective = "Deze gegevens leverde een match met een (of meerdere) vluchten in onze database. Bijbehorende data is gebruikt voor het berekenen van capaciteit."

    fly_from_coo = get_coordinates(fly_from_id)
    fly_to_coo = get_coordinates(fly_to_id)

    FILLED_FACTOR = 100 / PERCENTAGE_FILLED
    distance = compute_distance_between_airports(fly_from_coo, fly_to_coo)
    emissions = round(distance * PASSENGER_FACTOR * FILLED_FACTOR * EMISSION_FACTOR, 2)

    # Streaming response
    
    def generate():
    # Emissie en capaciteit netjes in HTML
        yield f"""
        <div style="font-family: Arial; line-height: 1.6;">
            <h2 style="color:#2c3e50;">Resultaat van uw berekening</h2>
            <p><strong>Emissie:</strong> <span style="color:#3fa9f5; font-size:18px;">{emissions} kg CO₂</span></p>
            <p><strong>Capaciteit:</strong> {PERCENTAGE_FILLED}%</p>
            <p style="color:#7f8c8d; font-size:14px;">
                {filled_perspective}<br>
                <em>Let op:</em> Deze waarde is exclusief extra klimaatimpact zoals <abbr title="Relative Forcing Index">RFI</abbr>.
            </p>
            <hr style="margin:15px 0;">
        """

        # ChatGPT-perspectief streamen
        prompt = f"""
        Je bent een chatbot die mensen helpt de milieu-impact van vliegen begrijpelijk en invoelbaar te maken voor een gemiddelde Nederlandse volwassene.

        Je krijgt het totale aantal emissies in kilogram CO₂ voor één passagier: {emissions} kg.

        Maak een kort, toegankelijk en beeldend stukje tekst (2 (korte) zinnen) met deze instructies:

        1. Schat hoeveel bomen nodig zijn om deze CO₂ in EEN! (1) jaar te absorberen. Maak er een rond getal van.
        2. Gebruik hiervoor de aanname dat één volwassen boom gemiddeld 20 kg CO₂ per jaar opneemt.
        3. Presenteer het aantal benodigde bomen GROOT en ROOD.
        4. Noem expliciet de gebruikte aanname.
        5. Zorg dat de vergelijking begrijpelijk, concreet en beeldend is.

        Lever alleen de uiteindelijke tekst, zonder uitleg over je berekeningen.
        Simpele styling nodig die mogelijk is in een innerHTML, en gebruik emoijis.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

        # Sluit div
        yield "</div>"

    return Response(generate(), content_type="text/plain")


def start():
    """
    This function returns the output on the /abel page
    """
    return "this is the start function"