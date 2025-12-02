import os
import json
import hashlib
import pyodbc
import requests
from flask import request, jsonify, session
from connect_with_db import get_connection
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def rows_to_dicts(cursor, rows):
    """Convert pyodbc rows to list[dict] using cursor.description. (JV)"""
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def hash_password_with_salt(password: str, salt: bytes) -> bytes:
    """
    Hashes the password with the given salt using SHA-256. (JV)
    Must match SQL:
    HASHBYTES('SHA2_256', salt + CONVERT(VARBINARY(4000), plain_password NVARCHAR))
    """
    # NVARCHAR in SQL Server is UTF-16LE under the hood
    password_bytes = password.encode("utf-16le")
    return hashlib.sha256(salt + password_bytes).digest()

def hash_password(password: str) -> bytes:
    """
    Hash a password using SHA-256 without salt. (Currently unused.) (JV)
    Example password hashing: SHA-256.
    Assumes password_hash in the DB is stored as VARBINARY with the raw bytes.
    You can update the Users table values later to match this scheme.
    """
    return hashlib.sha256(password.encode("utf-8")).digest()


def login():
    """
    Handles user login requests. (JV)
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

        # Look up user by username to fetch stored password hash and salt
        cursor.execute(
            """
            SELECT
                user_id,
                username,
                full_name,
                password_hash,
                password_salt
            FROM Users
            WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()

        # Check if user exists, throw error if not
        if row is None:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401

        db_user_id, db_username, db_full_name, db_password_hash, db_password_salt = row

        # Check password
        expected_hash = hash_password_with_salt(password, db_password_salt)

        # check if hashes match, if not, return error (Make sure the error is same as username incorrect, as to not give hints)
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
    Handles user logout requests. Removes user info from session. (JV)
    POST /julian/logout

    Clears the logged-in user from the session.
    """
    session.pop("user_id", None)
    session.pop("username", None)
    return jsonify({"success": True})


def start():
    """
    Entry point for GET /julian (JV)
    Returns the logged-in user's info, trips, and reviews for the dashboard.

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

def ai_recommendation():
    """
    Handles AI travel recommendation requests. (JV)
    POST /julian/ai_recommendation
    Body JSON:
    {
      "include_trips": true/false,
      "include_reviews": true/false,
      "extra_notes": "optional free text from user",
      "distance_preference": "far" | "new" | "been_before" | null
    }

    Returns:
    {
      "success": true/false,
      "recommendation": "text from model",
      "error": "...optional..."
    }
    """

    current_user_id = session.get("user_id")
    if current_user_id is None:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    include_trips = bool(data.get("include_trips", True))
    include_reviews = bool(data.get("include_reviews", True))
    extra_notes = (data.get("extra_notes") or "").strip()
    distance_pref = data.get("distance_preference")

    # Normalize / validate distance preference, must be one of the valid options or None
    valid_prefs = {"far", "new", "been_before"}
    if distance_pref not in valid_prefs:
        distance_pref = None

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1) Basic user info
        cursor.execute(
            """
            SELECT
                users.user_id,
                users.username,
                users.full_name,
                users.home_airport_id,
                airports.name as home_airport_name
            FROM Users
            LEFT JOIN Airports
                ON users.home_airport_id = airports.airport_id
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
                "home_airport_name": user_row[4],
            }

        trips = []
        reviews = []

        # 2) Optionally load trips
        if include_trips:
            trips_sql = """
                SELECT
                    t.trip_id,
                    t.user_id,
                    t.departure_date,
                    t.return_date,
                    t.purpose,
                    t.total_price,
                    t.currency_code,
                    dep_air.iata_code AS departure_airport_code,
                    dep_city.name     AS departure_city_name,
                    arr_air.iata_code AS arrival_airport_code,
                    arr_city.name     AS arrival_city_name,
                    dest_city.name    AS main_destination_city_name,
                    al.name           AS primary_airline_name
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

        # 3) Optionally load reviews
        if include_reviews:
            reviews_sql = """
                SELECT
                    r.review_id,
                    r.trip_id,
                    r.rating,
                    r.review_title,
                    r.review_text,
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

    except Exception as e:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
        return jsonify({"success": False, "error": f"DB error: {e}"}), 500

    # 4) Build context object for the AI
    context = {
        "user": user_info,
        "trips": trips if include_trips else [],
        "reviews": reviews if include_reviews else [],
        "preferences": {
            "include_trips": include_trips,
            "include_reviews": include_reviews,
            "distance_preference": distance_pref,
            "extra_notes": extra_notes,
        },
    }

    # 5) Call OpenAI / ChatGPT
    try:
        # Convert context to JSON string (datetimes -> strings)
        context_json = json.dumps(context, default=str, indent=2)

        system_prompt = (
            "You are an AI travel recommendation engine for a travel website. "
            "You receive a JSON object describing a single user's past trips, reviews, "
            "and some preferences. Your job is to generate a friendly, concrete travel "
            "recommendation for this user. You may suggest 1–3 specific destinations.\n\n"
            "Constraints:\n"
            "- Start with a short 1–2 sentence summary.\n"
            "- Then give bullet points: why this fits their habits, what they'll like, "
            "and what could be new for them.\n"
            "- Respect the distance_preference if provided: "
            "'far' = long-haul, 'new' = different than previous destinations, "
            "'been_before' = places similar to or including places they've visited.\n"
            "Try to listen to any extra notes left by the user to the best of your ability.\n"
            "However, if the notes are vague, contradictory, or clearly impossible, \n"
            "use your best judgment to provide a reasonable recommendation.\n"
            "- Use a helpful, enthusiastic but not cheesy tone.\n"
        )

        user_message = (
            "Here is the user's data in JSON format:\n"
            "```json\n"
            f"{context_json}\n"
            "```\n\n"
            "Using this information, recommend 1–3 destination ideas and explain your reasoning."
        )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4o" etc.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.8,
            max_tokens=600,
        )

        # Extract recommendation text
        recommendation_text = completion.choices[0].message.content


        return jsonify(
            {
                "success": True,
                "recommendation": recommendation_text,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": f"OpenAI error: {e}"}), 500
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except pyodbc.ProgrammingError:
                pass
        if conn is not None:
            try:
                conn.close()
            except pyodbc.ProgrammingError:
                pass

def speech_token():
    """
    Handles requests for Azure Speech tokens. (JV)
    GET /julian/speech-token

    Returns a short-lived Azure Speech token + region so the frontend
    can call the Speech SDK without exposing the subscription key.
    """
    speech_key = os.getenv("SPEECH_KEY")
    speech_region = os.getenv("SPEECH_REGION")

    if not speech_key or not speech_region:
        return jsonify({"error": "Speech service is not configured"}), 500

    try:
        # Azure issueToken endpoint
        url = f"https://{speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            "Ocp-Apim-Subscription-Key": speech_key,
            "Content-Length": "0",
        }

        # POST with empty body
        resp = requests.post(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            return jsonify(
                {
                    "error": "Failed to obtain speech token",
                    "status": resp.status_code,
                    "details": resp.text,
                }
            ), 500

        token = resp.text

        return jsonify({"token": token, "region": speech_region})

    except Exception as e:
        return jsonify({"error": f"Could not obtain speech token: {e}"}), 500