from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import abel, bente, donny, julian, esmee, vlucht_boeken
import os

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["null", "http://127.0.0.1:5500", "http://localhost:5500"])  # Enable CORS with credentials support

app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True   # REQUIRED or cookie is rejected
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

@app.route('/')
def home():
    return "This is the 'Reisbureau' home page."

@app.route("/abel", methods=["GET", "POST"])
def abel_route():
    result = abel.start()
    return result

@app.route("/abel/departureFrom", methods=["GET", "POST"])
def departure_from():
    result = abel.get_all_airports_we_can_depart_from()
    return result

@app.route("/abel/arrivalAt", methods=["GET", "POST"])
def arrival_at():
    result = abel.get_all_arrival_airports_departing_from(request.get_json())
    return result

@app.route("/abel/airlines", methods=["GET", "POST"])
def airlines():
    result = abel.get_all_airline_names()
    return result

@app.route("/abel/computeEmissions", methods=["GET", "POST"])
def compute_emissions():
    result = abel.compute_emissions(request.get_json())
    return result

@app.route("/bente", methods=["GET", "POST"])
def bente_route():
    result = bente.start()
    return result

@app.route("/donny", methods=["GET", "POST"])
def donny_route():
    result = donny.start()
    return result

@app.route("/donny/destinations", methods=["GET", "POST"])
def donny_destinations_route():
    result = donny.get_destinations_from_departure()
    return result

@app.route("/donny/checkin", methods=["GET", "POST"])
def donny_checkin_route():
    result = donny.checkin()
    return result

@app.route("/julian", methods=["GET"])
def julian_route():
    return julian.start()

@app.route("/julian/login", methods=["POST"])
def julian_login():
    return julian.login()

@app.route("/julian/logout", methods=["POST"])
def julian_logout():
    return julian.logout()

@app.route("/julian/ai_recommendation", methods=["POST"])
def julian_ai_recommendation_route():
    return julian.ai_recommendation()

@app.route("/julian/speech-token", methods=["GET"])
def julian_speech_token():
    return julian.speech_token()

@app.route("/julian/session", methods=["GET"])
def julian_session_route():
    return julian.session_status()

@app.route("/esmee", methods=["GET", "POST"])
def esmee_route():
    result = esmee.start()
    return result

@app.route("/vlucht_boeken/departureFrom", methods=["GET", "POST"])
def VB_departure_from():
    result = vlucht_boeken.get_all_airports_we_can_depart_from()
    return result

@app.route("/vlucht_boeken/arrivalAt", methods=["GET", "POST"])
def VB_arrival_at():
    result = vlucht_boeken.get_all_arrival_airports_departing_from(request.get_json())
    return result

@app.route("/vlucht_boeken/departureDate", methods=["GET", "POST"])
def VB_departure_date():
    result = vlucht_boeken.get_departure_dates(request.get_json())
    return result

if __name__ == '__main__':  
    app.run(debug=True, port=5001)