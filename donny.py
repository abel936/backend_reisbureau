from connect_with_db import get_connection
from decimal import Decimal

#basic query voor data luchthavens
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

#beschikbare aankomstluchthavens vanaf vertrekluchthaven
def get_destinations_from_departure(iata_code):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            a2.iata_code,
            a2.name,
            a2.latitude,
            a2.longitude
        FROM dbo.Flights f
        JOIN dbo.Airports a1 ON f.departure_airport_id = a1.id
        JOIN dbo.Airports a2 ON f.arrival_airport_id   = a2.id
        WHERE a1.iata_code = ?;
    """, (iata_code,))
    rows = cursor.fetchall()
    keys = [col[0] for col in cursor.description]
    data = [dict(zip(keys, row)) for row in rows]
    cursor.close()
    connection.close()
    return data