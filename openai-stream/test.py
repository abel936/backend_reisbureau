
from flask import Flask, request, Response
from openai import OpenAI
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

def some_function(data):
    question = data.get("question", "")

    def generate():
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}],
            stream=True
        )
            
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


    return Response(generate(), content_type="text/plain")

@app.route("/")
def main():
    return "some home page this is"

@app.route("/ask", methods=["POST"])
def ask():
    return some_function(request.get_json())
    
if __name__ == "__main__":
    app.run(debug=True)
