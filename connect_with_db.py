import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_cursor():
  myconn = mysql.connector.connect(
    host= os.getenv("AZURE_MYSQL_SERVER"),
    user= os.getenv("AZURE_MYSQL_USER"),
    password= os.getenv("AZURE_MYSQL_PASSWORD"),
    database= os.getenv("AZURE_MYSQL_DATABASE")
  )
  cursor = myconn.cursor(dictionary=True)
  return myconn, cursor

#myconn, mycursor = get_cursor()
#mycursor.execute("""SELECT * FROM club""")
#output = mycursor.fetchall()

#print(output)