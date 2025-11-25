from connect_with_db import get_connection
from decimal import Decimal

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
    for row in rows:
        row_dict = dict(zip(keys, row))
        for key in ['latitude', 'longitude']:
            if isinstance(row_dict[key], Decimal):
                row_dict[key] = float(row_dict[key])
        data.append(row_dict)
    return data

print(start())