from connect_with_db import get_connection

def start():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""SELECT CONVERT(DATE, scheduled_departure) AS vertrekdatum, CONVERT(TIME, dbo.Flights.scheduled_departure) AS vertrektijd, CONVERT(TIME, dbo.Flights.scheduled_arrival) AS aankomsttijd, c.name AS bestemmingsland, dbo.Flights.base_price AS standaardprijs, CAST(ROUND(0.3 * dbo.Flights.base_price, 2) AS DECIMAL(10,2)) AS last_minute_prijs
FROM dbo.Flights, dbo.Countries c, dbo.Airports ap
WHERE CONVERT(DATE, scheduled_departure) >= CAST(GETDATE() AS DATE)  -- vandaag
AND CONVERT(DATE, scheduled_departure) < DATEADD(WEEK, 4, CAST(GETDATE() AS DATE))  -- 4 weken vanaf vandaag
AND dbo.Flights.arrival_airport_id = ap.airport_id
AND c.country_id = ap.country_id;
""")
    rows = cursor.fetchall()
    keys = [i[0] for i in cursor.description]
    
    data = []
    for row in rows:
        row_dict = dict(zip(keys, row))
        # Tijd omzetten naar string
        row_dict['vertrektijd'] = row_dict['vertrektijd'].strftime("%H:%M:%S")
        row_dict['aankomsttijd'] = row_dict['aankomsttijd'].strftime("%H:%M:%S")
        data.append(row_dict)
    return data

# print(start())