from flask import Flask, request, render_template, jsonify
import logging
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")

logging.basicConfig(filename="flask_server.log", level=logging.INFO)

@app.route("/", methods=["GET"])
def index():
    logging.info(f"{datetime.now()} - GET /")
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    if request.is_json:
        data = request.get_json()
        msg = f"JSON Received: {data}"
    else:
        data = request.form
        msg = f"Form Data Received: {data}"
    
    logging.info(f"{datetime.now()} - POST /submit - {msg}")

    with open("form_data.txt", "a") as f:
        f.write(str(data) + "\n")

    return jsonify({"status": "success", "received": data})

@app.errorhandler(404)
def not_found(e):
    logging.warning(f"{datetime.now()} - 404 Error: {request.path}")
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)
