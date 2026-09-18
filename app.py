from flask import Flask, request
from traceroute import run_traceroute

app = Flask(__name__)

@app.route("/")
def home():
    return "Hi"


@app.route("/api/trace")
def trace():
    target = request.args.get("target")

    if target is None:
        return {"error": "missing target parameter"}, 400

    hops = run_traceroute(target, 15)
    return hops


if __name__ == "__main__":
    app.run(debug = True, port = 5000)