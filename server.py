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


# =============================
# VERIFY LICENSE (ใช้กับโปรแกรม)
# =============================
@app.route("/verify", methods=["POST"])
def verify():

    data = request.json

    if not data:
        return jsonify({"status": "ERROR"})

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "ERROR"})

    licenses = load_licenses()

    if key not in licenses:
        return jsonify({"status": "INVALID"})

    # bind hwid ครั้งแรก
    if licenses[key] == "":
        licenses[key] = hwid
        save_licenses(licenses)
        return jsonify({"status": "VALID"})

    # hwid ตรง
    if licenses[key] == hwid:
        return jsonify({"status": "VALID"})

    # hwid ไม่ตรง
    return jsonify({"status": "HWID_MISMATCH"})


# =============================
# ดู license ทั้งหมด
# =============================
@app.route("/licenses")
def show_licenses():
    licenses = load_licenses()
    return jsonify(licenses)


# =============================
# เช็ค key ผ่าน browser
# =============================
@app.route("/check")
def check_key():

    key = request.args.get("key")

    if not key:
        return "NO KEY PROVIDED"

    licenses = load_licenses()

    if key not in licenses:
        return "INVALID KEY"

    if licenses[key] == "":
        return f"{key} : NOT USED"

    return f"{key} : USED BY HWID {licenses[key]}"


# =============================
# หน้า Home
# =============================
@app.route("/")
def home():
    return """
    License Server Online<br><br>

    ตรวจสอบ Key:<br>
    /check?key=YOURKEY<br><br>

    ดู License ทั้งหมด:<br>
    /licenses
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
