from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# ใช้ DATABASE_URL จาก Render Environment
DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True


def get_license(key):
    cur = conn.cursor()
    cur.execute("SELECT hwid FROM licenses WHERE license_key=%s", (key,))
    return cur.fetchone()


def set_hwid(key, hwid):
    cur = conn.cursor()
    cur.execute(
        "UPDATE licenses SET hwid=%s WHERE license_key=%s",
        (hwid, key)
    )


@app.route("/verify", methods=["POST"])
def verify():

    data = request.json

    if not data:
        return jsonify({"status": "ERROR", "message": "No data"})

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "ERROR", "message": "Missing key or hwid"})

    result = get_license(key)

    if not result:
        return jsonify({"status": "INVALID", "message": "Key not found"})

    saved_hwid = result[0]

    # bind ครั้งแรก
    if saved_hwid is None or saved_hwid == "":
        set_hwid(key, hwid)
        return jsonify({"status": "VALID", "message": "Key activated"})

    # hwid ตรง
    if saved_hwid == hwid:
        return jsonify({"status": "VALID", "message": "Key verified"})

    # hwid ไม่ตรง
    return jsonify({
        "status": "HWID_MISMATCH",
        "message": "Key already used on another PC"
    })


@app.route("/licenses")
def show_licenses():

    cur = conn.cursor()
    cur.execute("SELECT license_key, hwid FROM licenses")

    rows = cur.fetchall()

    data = {}

    for row in rows:
        data[row[0]] = row[1]

    return jsonify(data)


@app.route("/check/<key>")
def check_key(key):

    result = get_license(key)

    if not result:
        return jsonify({
            "key": key,
            "status": "NOT_FOUND"
        })

    hwid = result[0]

    if hwid is None or hwid == "":
        return jsonify({
            "key": key,
            "status": "NOT_USED"
        })

    return jsonify({
        "key": key,
        "status": "USED",
        "hwid": hwid
    })


@app.route("/")
def home():

    cur = conn.cursor()
    cur.execute("SELECT license_key, hwid FROM licenses")

    rows = cur.fetchall()

    html = "<h1>License Server Online</h1>"
    html += "<h2>Keys</h2>"

    for key, hwid in rows:

        status = "NOT USED" if hwid is None or hwid == "" else "USED"

        html += f"<p><b>{key}</b> - {status} - {hwid}</p>"

    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)