from flask import Flask, request, jsonify
import json

app = Flask(__name__)

LICENSE_FILE = "licenses.json"

def load_licenses():
    with open(LICENSE_FILE, "r") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/verify", methods=["POST"])
def verify():

    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    licenses = load_licenses()

    if key not in licenses:
        return jsonify({"status": "INVALID"})

    if licenses[key] == "":
        licenses[key] = hwid
        save_licenses(licenses)
        return jsonify({"status": "VALID"})

    if licenses[key] == hwid:
        return jsonify({"status": "VALID"})

    return jsonify({"status": "HWID_MISMATCH"})


@app.route("/")
def home():
    return "License Server Online"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)