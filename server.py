from flask import Flask, request, jsonify
import json

app = Flask(__name__)

with open("licenses.json") as f:
    keys = json.load(f)

@app.route("/verify",methods=["POST"])
def verify():

    data = request.json
    key = data["key"]
    hwid = data["hwid"]

    if key not in keys:
        return jsonify({"status":"INVALID"})

    if keys[key] == "":
        keys[key] = hwid
        with open("licenses.json","w") as f:
            json.dump(keys,f,indent=4)
        return jsonify({"status":"VALID"})

    if keys[key] == hwid:
        return jsonify({"status":"VALID"})

    return jsonify({"status":"HWID_MISMATCH"})


app.run(host="0.0.0.0",port=5000)