from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

LICENSE_FILE = "licenses.json"

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w") as f:
            json.dump({}, f)
        return {}

    with open(LICENSE_FILE, "r") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/verify", methods=["POST"])
def verify():

    data = request.json

    if not data:
        return jsonify({"status": "ERROR", "message": "No data"})

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "ERROR", "message": "Missing key or hwid"})

    licenses = load_licenses()

    if key not in licenses:
        return jsonify({"status": "INVALID", "message": "Key not found"})

    # bind hwid ครั้งแรก
    if licenses[key] == "":
        licenses[key] = hwid
        save_licenses(licenses)
        return jsonify({"status": "VALID", "message": "Key activated"})

    # hwid ตรง
    if licenses[key] == hwid:
        return jsonify({"status": "VALID", "message": "Key verified"})

    # hwid ไม่ตรง
    return jsonify({"status": "HWID_MISMATCH", "message": "Key already used on another PC"})


# ดู licenses ทั้งหมด
@app.route("/licenses")
def show_licenses():
    licenses = load_licenses()
    return jsonify(licenses)


# เช็ค key ผ่าน browser
@app.route("/check/<key>")
def check_key(key):

    licenses = load_licenses()

    if key not in licenses:
        return jsonify({
            "key": key,
            "status": "NOT_FOUND"
        })

    if licenses[key] == "":
        return jsonify({
            "key": key,
            "status": "NOT_USED"
        })

    return jsonify({
        "key": key,
        "status": "USED",
        "hwid": licenses[key]
    })


# หน้าเว็บหลัก
@app.route("/")
def home():

    licenses = load_licenses()

    html = "<h1>License Server Online</h1>"
    html += "<h2>Keys</h2>"

    for key, hwid in licenses.items():

        status = "NOT USED" if hwid == "" else "USED"

        html += f"<p><b>{key}</b> - {status} - {hwid}</p>"

    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
