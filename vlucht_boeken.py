from connect_with_db import get_connection
from flask import Flask, request, Response, abort
from math import radians, sin, cos, sqrt, atan2
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from MLmodel import predict_capacity_percentage


def execute_query(query: str, params: tuple = ()):
    """
    Execute an SQL query and return results. Handles DB errors and connection cleanup.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                if rows: 
                    return rows 
                return abort(404, "QUERY yields no results")
    except Exception as e:
        abort(500, f"Database error: {e}")


def get_all_airports_we_can_depart_from():
    """
    Get all airports where future flights depart from
    """
    rows = execute_query("""
        SELECT DISTINCT(ai.airport_id), ai.name 
        FROM flights fl
        LEFT JOIN airports ai ON ai.airport_id = fl.departure_airport_id
        WHERE DATEDIFF(day, GETDATE(), CONVERT(date, scheduled_departure)) > 0;
    """)
    return [{"airportID": row[0], "airportName": row[1]} for row in rows]


def get_all_arrival_airports_departing_from(data):
    """
    Get all airports flights will arrive at based on future departures
    """
    selected_airport = int(data.get('fly_from'))
    rows = execute_query("""
        SELECT DISTINCT(ai.airport_id), ai.name
        FROM airports ai
        JOIN flights fl ON fl.arrival_airport_id = ai.airport_id
        WHERE (fl.departure_airport_id = ?)
        AND (DATEDIFF(day, GETDATE(), CONVERT(date, scheduled_departure)) > 0);
    """, (selected_airport,))
    return [{"airportID": row[0], "airportName": row[1]} for row in rows]


def get_departure_dates(data):
    """
    Get all dates one can fly from <fly_from> to <fly_to>
    """
    fly_from_id = int(data.get('fly_from'))
    fly_to_id = int(data.get('fly_to'))

    query = """
    SELECT CONVERT(date, scheduled_departure) as scheduled_departure
    FROM flights fl
    LEFT JOIN airlines ail ON fl.airline_id = ail.airline_id
    WHERE departure_airport_id = ?
    AND arrival_airport_id = ?
    ORDER BY scheduled_departure DESC;
    """

    # Dynamic conditions
    params = [fly_from_id, fly_to_id]
    
    try:
        query_result = execute_query(query, tuple(params))
        output = [{"departure_date": row[0].isoformat()} for row in query_result]
        print(f"==================={output}")
        return output

    except:
        return None