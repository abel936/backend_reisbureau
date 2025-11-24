from connect_with_db import get_cursor

def start():
    myconn, mycursor = get_cursor()
    mycursor.execute("""
    SELECT * FROM online_criminaliteit
    WHERE ﻿Onderwerp LIKE "%Totaal slachtoffers%"
    """)
    data = mycursor.fetchall()

    return data