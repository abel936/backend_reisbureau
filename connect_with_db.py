import os
#import mysql.connector
import pyodbc
from dotenv import load_dotenv

load_dotenv()

#def get_cursor():
#  myconn = mysql.connector.connect(
#    host= os.getenv("AZURE_MYSQL_SERVER"),
#    user= os.getenv("AZURE_MYSQL_USER"),
#    password= os.getenv("AZURE_MYSQL_PASSWORD"),
#    database= os.getenv("AZURE_MYSQL_DATABASE")
#  )
#  cursor = myconn.cursor(dictionary=True)
#  return myconn, cursor

#myconn, mycursor = get_cursor()
#mycursor.execute("""SELECT * FROM club""")
#output = mycursor.fetchall()

#print(output)

def get_connection():
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver   = os.getenv("AZURE_SQL_DRIVER", "{ODBC Driver 18 for SQL Server}")
    encrypt  = os.getenv("AZURE_SQL_ENCRYPT", "yes")
    trust    = os.getenv("AZURE_SQL_TRUST_CERT", "no")
    timeout  = os.getenv("AZURE_SQL_TIMEOUT", "30")

    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password};"
        f"Encrypt={encrypt};TrustServerCertificate={trust};"
        f"Connection Timeout={timeout};"
    )
    return pyodbc.connect(conn_str)