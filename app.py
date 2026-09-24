from flask import Flask, request, Response, render_template
from traceroute import run_traceroute
from geolocate import geolocate_ip
import json

app = Flask(__name__)

# Base route
@app.route("/")
def home():
    return render_template("index.html")

# Route for traceroute as it comes
@app.route("/api/trace/stream")
def trace_stream():
    target = request.args.get("target")

    # Check if destination ip is input
    if target is None:
        return {"error": "missing target parameter"}, 400

    # Run traceroute
    def event_stream():
        for hop in run_traceroute(target, 30):
            # If the IP is private or not found set geo to None
            if hop["ip"] is None:
                geo = None
            # If the IP is found, append the geolocation information to hop
            else:
                geo = geolocate_ip(hop["ip"])

            hop["geo"] = geo

            # Return hop
            yield f"event: hop\ndata: {json.dumps(hop)}\n\n"

        yield f"event: done\ndata: {{}}\n\n"

    return Response(event_stream(), mimetype = "text/event-stream")

if __name__ == "__main__":
    app.run(debug = True, port = 5000)