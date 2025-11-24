import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from flask import request, jsonify
from backend_reisbureau.connect_with_db import get_connection

load_dotenv()


def start():
    """
    Entry point for the /julian route.

    - Always: returns list of all users (for dropdown).
    - If ?user_id=<id> is provided: also returns trips + reviews for that user.
    """
    user_id = request.args.get("user_id", type=int)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Get all users for the dropdown
        cursor.execute("""
            SELECT
                user_id,
                username,
                full_name,
                home_airport_id
            FROM Users
            ORDER BY username;
        """)
        users = cursor.fetchall()

        trips = []
        reviews = []

        # 2. If a specific user was selected, get their trips + reviews
        if user_id is not None:
            # --- Trips for this user ---
            trips_sql = """
                SELECT
                    t.trip_id,
                    t.user_id,
                    t.departure_date,
                    t.return_date,
                    t.purpose,
                    t.total_price,
                    t.currency_code,
                    dep_air.airport_id        AS departure_airport_id,
                    dep_air.iata_code         AS departure_airport_code,
                    dep_city.city_id          AS departure_city_id,
                    dep_city.name             AS departure_city_name,
                    arr_air.airport_id        AS arrival_airport_id,
                    arr_air.iata_code         AS arrival_airport_code,
                    arr_city.city_id          AS arrival_city_id,
                    arr_city.name             AS arrival_city_name,
                    dest_city.city_id         AS main_destination_city_id,
                    dest_city.name            AS main_destination_city_name,
                    al.airline_id             AS primary_airline_id,
                    al.name                   AS primary_airline_name
                FROM UserTrips t
                JOIN Airports dep_air
                    ON t.departure_airport_id = dep_air.airport_id
                JOIN Airports arr_air
                    ON t.arrival_airport_id = arr_air.airport_id
                LEFT JOIN Cities dep_city
                    ON dep_air.city_id = dep_city.city_id
                LEFT JOIN Cities arr_city
                    ON arr_air.city_id = arr_city.city_id
                LEFT JOIN Cities dest_city
                    ON t.main_destination_city_id = dest_city.city_id
                LEFT JOIN Airlines al
                    ON t.primary_airline_id = al.airline_id
                WHERE t.user_id = %s
                ORDER BY t.departure_date DESC, t.trip_id DESC;
            """
            cursor.execute(trips_sql, (user_id,))
            trips = cursor.fetchall()

            # --- Reviews for this user ---
            reviews_sql = """
                SELECT
                    r.review_id,
                    r.trip_id,
                    r.airline_id,
                    r.airport_id,
                    r.city_id,
                    r.rating,
                    r.review_title,
                    r.review_text,
                    r.created_at,
                    r.travel_date,
                    al.name      AS airline_name,
                    ap.iata_code AS airport_code,
                    ci.name      AS city_name
                FROM Reviews r
                LEFT JOIN Airlines al
                    ON r.airline_id = al.airline_id
                LEFT JOIN Airports ap
                    ON r.airport_id = ap.airport_id
                LEFT JOIN Cities ci
                    ON r.city_id = ci.city_id
                WHERE r.user_id = %s
                ORDER BY r.travel_date DESC, r.review_id DESC;
            """
            cursor.execute(reviews_sql, (user_id,))
            reviews = cursor.fetchall()

        # 3. Build JSON response
        response = {
            "users": users,
            "selected_user_id": user_id,
            "trips": trips,
            "reviews": reviews,
        }
        return jsonify(response)

    except Error as e:
        # Simple error response for now
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
