import hashlib
from flask import request, jsonify, session
from connect_with_db import get_connection


def rows_to_dicts(cursor, rows):
    """Convert pyodbc rows to list[dict] using cursor.description."""
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def hash_password(password: str) -> bytes:
    """
    Example password hashing: SHA-256.
    Assumes password_hash in the DB is stored as VARBINARY with the raw bytes.
    You can update the Users table values later to match this scheme.
    """
    return hashlib.sha256(password.encode("utf-8")).digest()


def login():
    """
    POST /julian/login
    Body: { "username": "...", "password": "..." }

    If valid:
      - stores user_id in session["user_id"]
      - returns basic user info
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Look up user by username
        cursor.execute(
            """
            SELECT
                user_id,
                username,
                full_name,
                password_hash
            FROM Users
            WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()

        if row is None:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401

        db_user_id, db_username, db_full_name, db_password_hash = row

        # Check password
        expected_hash = hash_password(password)

        # db_password_hash from pyodbc is already bytes for VARBINARY
        if db_password_hash != expected_hash:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401

        # Success: store in session
        session["user_id"] = db_user_id
        session["username"] = db_username

        return jsonify(
            {
                "success": True,
                "user": {
                    "user_id": db_user_id,
                    "username": db_username,
                    "full_name": db_full_name,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def logout():
    """
    POST /julian/logout

    Clears the logged-in user from the session.
    """
    session.pop("user_id", None)
    session.pop("username", None)
    return jsonify({"success": True})


def start():
    """
    Entry point for GET /julian

    - Requires a logged-in user (session["user_id"]).
    - Returns:
        - the logged in user's basic info
        - that user's trips
        - that user's reviews
    """
    current_user_id = session.get("user_id")

    if current_user_id is None:
        # Not logged in
        return jsonify({"error": "Not authenticated"}), 401

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Get the logged-in user's info (for display)
        cursor.execute(
            """
            SELECT
                user_id,
                username,
                full_name,
                home_airport_id
            FROM Users
            WHERE user_id = ?
            """,
            (current_user_id,),
        )
        user_row = cursor.fetchone()
        user_info = None
        if user_row:
            user_info = {
                "user_id": user_row[0],
                "username": user_row[1],
                "full_name": user_row[2],
                "home_airport_id": user_row[3],
            }

        # 2. Get trips for this user
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
            WHERE t.user_id = ?
            ORDER BY t.departure_date DESC, t.trip_id DESC;
        """
        cursor.execute(trips_sql, (current_user_id,))
        trip_rows = cursor.fetchall()
        trips = rows_to_dicts(cursor, trip_rows)

        # 3. Get reviews for this user
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
            WHERE r.user_id = ?
            ORDER BY r.travel_date DESC, r.review_id DESC;
        """
        cursor.execute(reviews_sql, (current_user_id,))
        review_rows = cursor.fetchall()
        reviews = rows_to_dicts(cursor, review_rows)

        # 4. Build JSON response
        response = {
            "user": user_info,
            "trips": trips,
            "reviews": reviews,
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()