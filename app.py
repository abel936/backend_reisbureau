from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import abel, bente, donny, julian, esmee

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return "This is the 'Urban Myths' home page."

@app.route("/abel", methods=["GET", "POST"])
def abel_route():
    result = abel.start()
    return result

@app.route("/bente", methods=["GET", "POST"])
def bente_route():
    result = bente.start()
    return result

@app.route("/donny", methods=["GET", "POST"])
def donny_route():
    result = donny.start()
    return result

@app.route("/julian", methods=["GET", "POST"])
def julian_route():
    result = julian.start()
    return result

@app.route("/esmee", methods=["GET", "POST"])
def esmee_route():
    result = esmee.start()
    return result

if __name__ == '__main__':  
    app.run(debug=True)