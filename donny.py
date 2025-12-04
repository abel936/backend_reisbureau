from connect_with_db import get_connection
from flask import request
import os
from dotenv import load_dotenv
import json

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

load_dotenv()
DOCINT_ENDPOINT = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
DOCINT_API_KEY = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")
DOCINT_MODEL_ID = os.getenv("DOCUMENTINTELLIGENCE_MODEL_ID")

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

# =======================
# Document Intelligence integratie
# =======================

DOCINT_ENDPOINT = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
DOCINT_API_KEY = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")
DOCINT_MODEL_ID = os.getenv("DOCUMENTINTELLIGENCE_MODEL_ID")


def _get_field_value(field):
    """Hulpfunctie om veilig de waarde uit een Document Intelligence field te halen."""
    if field is None:
        return None
    return getattr(field, "value", None) or field.content


def analyze_ticket(image_bytes: bytes) -> dict:
    """
    Stuurt een vliegticket (image bytes) naar Azure Document Intelligence
    en geeft een dict terug met de velden van jouw custom model.
    Verwachte velden:
    PassengerName, DepartureCity, DepartureIATA, ArrivalCity, ArrivalIATA,
    Gate, Carrier, FlightNr, Class, BoardingTime, Luggage, Seat,
    DateOfFlight, TicketNr.
    """
    client = DocumentIntelligenceClient(
        endpoint=DOCINT_ENDPOINT,
        credential=AzureKeyCredential(DOCINT_API_KEY),
    )

    poller = client.begin_analyze_document(
        model_id=DOCINT_MODEL_ID,
        body=image_bytes,
    )
    result = poller.result()

    if not result.documents:
        raise ValueError("Geen document herkend in ticket.")

    doc = result.documents[0]
    f = doc.fields

    parsed = {
        "PassengerName": _get_field_value(f.get("PassengerName")),
        "DepartureCity": _get_field_value(f.get("DepartureCity")),
        "DepartureIATA": _get_field_value(f.get("DepartureIATA")),
        "ArrivalCity": _get_field_value(f.get("ArrivalCity")),
        "ArrivalIATA": _get_field_value(f.get("ArrivalIATA")),
        "Gate": _get_field_value(f.get("Gate")),
        "Carrier": _get_field_value(f.get("Carrier")),
        "FlightNr": _get_field_value(f.get("FlightNr")),
        "Class": _get_field_value(f.get("Class")),
        "BoardingTime": _get_field_value(f.get("BoardingTime")),
        "Luggage": _get_field_value(f.get("Luggage")),
        "Seat": _get_field_value(f.get("Seat")),
        "DateOfFlight": _get_field_value(f.get("DateOfFlight")),
        "TicketNr": _get_field_value(f.get("TicketNr")),
    }

    return parsed


def checkin():
    """
    Route-handler voor /donny/checkin.
    Verwacht een multipart/form-data request met key 'file' (ticketafbeelding).
    Leest het ticket uit met Document Intelligence en geeft de data direct terug.
    Er wordt niets opgeslagen in de database.
    """
    if "file" not in request.files:
        return {"error": "Upload een bestand via form-data onder key 'file'."}, 400

    file = request.files["file"]
    image_bytes = file.read()

    extracted = analyze_ticket(image_bytes)

    return {
        "message": "Ticket succesvol uitgelezen",
        "data": extracted,
    }



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