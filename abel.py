from connect_with_db import get_connection
from flask import abort, jsonify
from math import radians, sin, cos, sqrt, atan2
from openai import OpenAI
import os
from dotenv import load_dotenv, dotenv_values 
load_dotenv() 

# accessing and printing value
print(os.getenv("MY_KEY"))

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
    """compute the distance between two sets of coordinates taking into consideration
    the curvature of the earth"""
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
    return distance

def perspective_emission_chatGPT(emissions_in_kg):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    Je bent een chatbot die mensen helpt de milieu-impact van vliegen begrijpelijk en invoelbaar te maken voor een gemiddelde Nederlandse volwassene.

    Je krijgt het totale aantal emissies in kilogram CO₂ voor één passagier: {emissions_in_kg} kg.

    Maak een kort, toegankelijk en beeldend stukje tekst (2 zinnen) met deze instructies:

    1. Schat hoeveel bomen nodig zijn om deze CO₂ in één jaar te absorberen.
    2. Gebruik hiervoor de aanname dat één volwassen boom gemiddeld 20 kg CO₂ per jaar opneemt.
    3. Presenteer het aantal benodigde bomen GROOT en ROOD.
    4. Noem expliciet de gebruikte aanname (20 kg per boom per jaar).
    5. Zorg dat de vergelijking begrijpelijk, concreet en beeldend is.

    Gebruik eenvoudige HTML-opmaak (zoals <b> voor vetgedrukt) en vermijd speciale tekens die innerHTML kunnen breken
    Lever alleen de uiteindelijke tekst, zonder uitleg over je berekeningen.
    We praten hier al tegen deze passigier, dus betrek het op diegene.
    """

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.95,  # meer vrijheid!
        max_tokens=300
    )

    return completion.choices[0].message.content


def compute_emissions(data):
    fly_from_id = data.get("fly_from")
    fly_to_id = data.get("fly_to")
    fly_from_coo = get_coordinates(int(fly_from_id))
    fly_to_coo = get_coordinates(int(fly_to_id))
    
    distance = compute_distance_between_airports(fly_from_coo[0], fly_to_coo[0])
    emissions = round(distance * 0.0365 * 3.203, 2)
    perspective = perspective_emission_chatGPT(emissions)

    return {"emissions": emissions, "perspective": perspective}


def start():
    """This function returns the output on the /abel page"""
    return "this is the start function"