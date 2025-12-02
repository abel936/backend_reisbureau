from connect_with_db import get_connection
from flask import request
from openai import OpenAI
import os
from dotenv import load_dotenv

#query om alle luchthavens op te halen voor vertrek dropdown
def start():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""  SELECT 
                        iata_code, name, latitude, longitude
                        FROM dbo.Airports
                   ;""")
    rows = cursor.fetchall()
    keys = [i[0] for i in cursor.description]
    data = [dict(zip(keys, row)) for row in rows]
    cursor.close()
    connection.close()
    return data

#query om beschikbare aankomstluchthavens op te halen, met laagste prijs
def get_destinations_from_departure():
    payload = request.get_json()
    iata_code = payload.get("iata_code")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT
            a2.iata_code,
            a2.name,
            a2.latitude,
            a2.longitude,
            MIN(f.base_price) AS min_price
        FROM dbo.Flights f
        JOIN dbo.Airports a1 ON f.departure_airport_id = a1.airport_id
        JOIN dbo.Airports a2 ON f.arrival_airport_id   = a2.airport_id
        WHERE a1.iata_code = ?
            AND f.status = 'SCHEDULED'
        GROUP BY
            a2.iata_code,
            a2.name,
            a2.latitude,
            a2.longitude;
    """, (iata_code,))
    rows = cursor.fetchall()
    keys = [col[0] for col in cursor.description]
    data = [dict(zip(keys, row)) for row in rows]
    cursor.close()
    connection.close()
    return data

#toevoegen luchthaven
# def add_airport():
#     data = request.get_json() or {}
#     name            = data.get("name")
#     iata_code       = data.get("iata_code")
#     latitude        = data.get("latitude")
#     longitude       = data.get("longitude")
#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute("""
#         INSERT INTO dbo.Airports (
#             name,
#             iata_code,
#             latitude,
#             longitude
#         )
#         VALUES (?, ?, ?, ?);
#     """, (
#         name,
#         iata_code,
#         latitude,
#         longitude
#     ))

#     conn.commit()
#     cursor.close()
#     conn.close()

#     return {
#         "message": "Luchthaven toegevoegd",
#         "airport": {
#             "name": name,
#             "iata_code": iata_code,
#             "latitude": latitude,
#             "longitude": longitude
#         }
#     }