from flask import request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
from connect_with_db import get_connection


def start():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""SELECT CONVERT(DATE, scheduled_departure) AS vertrekdatum, CONVERT(TIME, dbo.Flights.scheduled_departure) AS vertrektijd, CONVERT(TIME, dbo.Flights.scheduled_arrival) AS aankomsttijd, c.name AS bestemmingsland, dbo.Flights.base_price AS standaardprijs, CAST(ROUND(0.6 * dbo.Flights.base_price, 2) AS DECIMAL(10,2)) AS last_minute_prijs, dbo.Flights.seats_available AS aantal_beschikbare_plekken
FROM dbo.Flights, dbo.Countries c, dbo.Airports ap
WHERE CONVERT(DATE, scheduled_departure) >= CAST(GETDATE() AS DATE)  -- vandaag
AND CONVERT(DATE, scheduled_departure) < DATEADD(WEEK, 4, CAST(GETDATE() AS DATE))  -- 4 weken vanaf vandaag
AND dbo.Flights.arrival_airport_id = ap.airport_id
AND c.country_id = ap.country_id;
""")
    
    rows = cursor.fetchall()
    keys = [i[0] for i in cursor.description]
    
    # (BB) volgorde wijzigen
    preferred_order = [
        "vertrekdatum",
        "vertrektijd",
        "aankomsttijd",
        "bestemmingsland",
        "standaardprijs",
        "last_minute_prijs",
        "aantal_beschikbare_plekken"
    ]


    data = []
    for row in rows:
        row_dict = dict(zip(keys, row))

        # (BB) Tijd omzetten naar string
        row_dict['vertrekdatum'] = row_dict['vertrekdatum'].strftime("%Y-%m-%d")
        row_dict['vertrektijd'] = row_dict['vertrektijd'].strftime("%H:%M:%S")
        row_dict['aankomsttijd'] = row_dict['aankomsttijd'].strftime("%H:%M:%S")
        
        # (BB) reorder de volgorde
        ordered_row = {key: row_dict[key] for key in preferred_order if key in row_dict}
        
        data.append(ordered_row)
    return {
        "columns": preferred_order,
        "rows": data
    }