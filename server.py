from flask import Flask, request, jsonify, render_template_string
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


@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>License Server</title>
    </head>
    <body style="font-family: Arial; text-align:center; margin-top:50px;">
        <h1>License Server</h1>

        <input id="key" placeholder="Enter License Key"><br><br>
        <input id="hwid" placeholder="Enter HWID"><br><br>

        <button onclick="check()">Verify</button>

        <h3 id="result"></h3>

        <script>
        function check(){
            fetch("/verify",{
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    key:document.getElementById("key").value,
                    hwid:document.getElementById("hwid").value
                })
            })
            .then(res=>res.json())
            .then(data=>{
                document.getElementById("result").innerText="Status: "+data.status
            })
        }
        </script>
    </body>
    </html>
    """)


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

    if licenses[key] == "":
        licenses[key] = hwid
        save_licenses(licenses)
        return jsonify({"status": "VALID"})

    if licenses[key] == hwid:
        return jsonify({"status": "VALID"})

    return jsonify({"status": "HWID_MISMATCH"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
