# Traceroute Map

A local web app that runs a live traceroute to any hostname or IP address and plots each hop on an interactive map as it is discovered. The traceroute engine is written from scratch with raw ICMP packets (Scapy), not a wrapper around the system `traceroute` command.

![Demo](docs/demo.gif)
<!-- Record a short screen capture of a live trace and save it as docs/demo.gif -->

## Features

- **Custom traceroute engine.** Sends ICMP Echo Requests with an increasing TTL and reads the ICMP replies to discover each router on the path.
- **Live streaming.** Hops are sent to the browser one at a time using Server-Sent Events (SSE), so the page updates while the trace is still running.
- **IP geolocation.** Each public hop is geolocated (latitude, longitude, city, country, ISP) through the ip-api.com free API.
- **Animated map.** Leaflet draws a marker for each geolocated hop, extends a path line between them, and pans the camera along the route.
- **Paced animation.** A client-side queue separates when hops arrive from when they are drawn, so the animation stays smooth even when several hops arrive at once.
- **Hop table.** A sidebar lists every hop (TTL, IP, location, round-trip time), including hops that cannot be placed on the map.
- **Graceful handling of unplottable hops.** Private IPs and timeouts still appear in the table and are skipped on the map without breaking the path.
- **User input.** Type any hostname or IP into the input box and click Trace. Starting a new trace clears the previous markers, path, and table.
- **RTT measurement.** Each hop's round-trip time is measured in milliseconds.
- **Stops at the destination.** The trace ends when the destination replies (ICMP Echo Reply) or the hop limit (30) is reached.

## How it works

### Traceroute mechanism

Every IP packet carries a TTL (Time To Live) field. Each router decrements it by 1, and a router that receives a packet with TTL 0 drops it and sends back an ICMP **Time Exceeded** message (Type 11). The sender can read the source address of that reply to learn who the router is.

1. Send a probe with TTL = 1. The first router drops it and replies. That is hop 1.
2. Send a probe with TTL = 2. The second router replies. That is hop 2.
3. Keep going until the destination replies with an ICMP **Echo Reply** (Type 0), which means the packet survived the whole path.

If no reply arrives within 1 second, the hop is recorded as a timeout (`ip: null`).

### Data flow

```
Browser (Leaflet + EventSource)
        |  GET /api/trace/stream?target=<host>
        v
Flask route (app.py)
        |  for each hop from the generator:
        |    1. run_traceroute()  -> {ttl, ip, rtt_ms}      (traceroute.py, Scapy)
        |    2. geolocate_ip()    -> {lat, lon, city, ...}  (geolocate.py, ip-api.com)
        |    3. send as an SSE "hop" event
        v
Browser queue -> timer draws one hop per tick -> marker + path line + table row
        |
        v  SSE "done" event -> stop the stream and clear the timer
```

### Design decisions

- **A generator in the tracer.** `run_traceroute()` uses `yield` so each hop is available the moment it is found, instead of waiting for the full trace.
- **SSE instead of WebSockets or polling.** The data only flows from server to browser, which is exactly what SSE is for. It needs no extra libraries, and the browser reconnects on its own.
- **An explicit `done` event.** When the server closes an SSE connection, the browser's `EventSource` automatically reconnects, which would restart the trace forever. Sending a final `done` event lets the client close the connection on purpose.
- **A frontend animation queue.** The server sends the real timing, and the browser decides how to present it. A single timer drains the queue at a steady pace, so the raw data pipeline stays unmodified.
- **One event per hop with the location attached.** Geolocation data is added to the hop before it is sent, so the frontend never has to match separate events together. `geo` is always valid JSON (`null` when unavailable).

## Project structure

```
traceroute-map/
├── app.py              # Flask app: serves the page and the SSE endpoint
├── traceroute.py       # Scapy traceroute generator (run_traceroute)
├── geolocate.py        # IP geolocation and private-IP check
├── templates/
│   └── index.html      # Page, Leaflet map, hop table, and frontend logic
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9 or newer
- Administrator/root access (raw sockets are required to send ICMP packets)
- Internet access (map tiles and the geolocation API)
- On Windows: [Npcap](https://npcap.com/), which Scapy needs for packet handling

Python packages: `flask`, `scapy`, `requests`

## Setup

```bash
git clone https://github.com/<your-username>/traceroute-map.git
cd traceroute-map
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

Raw sockets need elevated privileges.

**macOS / Linux**
```bash
sudo venv/bin/python3 app.py
```

**Windows** (terminal opened as Administrator)
```powershell
python app.py
```

Then open **http://127.0.0.1:5001**, enter a hostname or IP address (for example `google.com` or `8.8.8.8`), and click **Trace**.

**Troubleshooting**
- *"Access denied" or the page does not load on macOS:* the app uses port 5001 because macOS AirPlay Receiver can occupy port 5000. If 5001 is also taken, change the port in the last line of `app.py`. Using `127.0.0.1` instead of `localhost` can also help.
- *`PermissionError` from Scapy:* the app was not started with `sudo` or as Administrator.
- *Many hops show `*` and the trace never reaches the destination:* see the limitations below.

## API

### `GET /api/trace/stream?target=<hostname-or-ip>`

Streams a trace as `text/event-stream`. Returns HTTP 400 with `{"error": "missing target parameter"}` if `target` is missing.

**`hop` event** (one per hop):
```
event: hop
data: {"ttl": 3, "ip": "24.155.250.113", "rtt_ms": 28.99,
       "geo": {"lat": 31.1, "lon": -97.3, "city": "Temple", "country": "United States", "isp": "..."}}
```

`ip`, `rtt_ms`, and `geo` are `null` for timeouts. `geo` is `null` for private IPs. A failed geolocation lookup is not handled yet (see Known limitations).

**`done` event** (sent once after the final hop):
```
event: done
data: {}
```

## Known limitations

Some of these come from how the internet and IP geolocation work. Others are gaps in the current code. Several were found while testing the app.

### Geolocation accuracy

- **Locations are approximate.** A geolocation database knows which network block an IP belongs to and where the owning organization registered it. It does not know where a device physically sits. Accuracy is typically city level at best, and often only region or country.
- **ISP hops land in nearby cities.** On a residential connection, the first public hop often geolocates to the ISP's regional facility rather than the user's actual city. For example, a Dallas-area connection can show a hop in Temple, TX.
- **Anycast addresses have no single location.** Services such as Google DNS (`8.8.8.8`) announce the same IP from many data centers, and routing sends each packet to a nearby one. A trace can end in Virginia while the address is commonly associated with Mountain View, CA. Both can be true at once.
- **Paid databases do not fix this.** Commercial databases such as MaxMind GeoLite2 can improve accuracy somewhat but have the same underlying limits.
- **The free API has a rate limit** (about 45 requests per minute) and is only served over HTTP, not HTTPS. This is acceptable for a local project, but it is another reason this should not be exposed publicly as is.

### Traceroute behavior

- **Private IPs are not plottable.** Hops in private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) and loopback (`127.0.0.0/8`) have no geographic location. They show in the table but not on the map. Home routers and university networks produce several of these at the start of a trace.
- **The private-IP check is hand-written** and does not cover every reserved range, such as carrier-grade NAT (`100.64.0.0/10`) or link-local (`169.254.0.0/16`). Such hops are sent to the geolocation API, which rejects them, and because failed lookups are not handled (see below) they can break the stream.
- **Timeouts (`*`) are normal.** Many routers and firewalls drop ICMP or rate-limit their replies for security reasons, so some hops never answer. Traces to distant international hosts can show long runs of timeouts and may never reach the destination within 30 hops. The system `traceroute` command behaves the same way on the same paths.
- **Paths vary.** Load balancing and routing changes mean two traces to the same target can take different routes.
- **One probe per hop.** Unlike the system `traceroute`, which sends three probes per hop by default, this sends one, so a single dropped or delayed reply shows as a timeout or an unusual RTT.
- **RTT includes local overhead.** Timing is measured around the Scapy send/receive call, so it includes some local processing time on top of the network round trip.
- **ICMP only.** There is no UDP or TCP probe mode, so paths that filter ICMP cannot be traced differently.
- **IPv4 only.**

### Application

- **Starting a new trace while one is running** clears the markers, path, and table, but the previous server-side trace may continue until it finishes.
- **Invalid or unreachable targets** are not handled with a friendly error message in the page. An unresolvable hostname can make the stream error out, and because the page has no `onerror` handler, the browser may keep retrying the connection.
- **The target is not validated or URL-encoded** in the browser before being sent.
- **Failed geolocation lookups are not handled.** `geolocate_ip` does not check the API's `status` field, so a failed lookup (a reserved IP range, a rate limit) raises a `KeyError` and ends the stream early without a `done` event, so the browser may reconnect and restart the trace.
- **Geolocation lookups have no timeout, retry, or cache,** so a slow API call can stall a trace.
- **No automated tests.**

## Security and responsible use

- **Local use only.** The app sends raw packets and needs root/administrator access. Do not expose it to the public internet. A public version would let strangers trigger probes from your machine, and would need authentication, rate limiting, and input validation first.
- **Trace only networks you are allowed to probe.** A traceroute to a normal public host is harmless, but you should not use this to scan or flood networks you do not own or have permission to test.
- **Debug mode is on** (`debug=True`) for development convenience. Turn it off before running anywhere other than your own machine.

## Possible future work

- Show a clear "No response" label for timeouts and "Private IP" for private addresses in the table
- Replace the hand-written private-IP check with Python's `ipaddress` module
- Add a timeout, error handling, and an in-memory cache to the geolocation lookup
- Resolve hostnames server-side and return a clear error for invalid targets
- Close the previous `EventSource` when a new trace starts
- Reverse DNS on each hop (router hostnames often include airport or city codes)
- Flag hops whose location is physically impossible given the measured RTT
- Marker popups, latency color-coding, and clicking a table row to jump to its marker
- Multiple probes per hop with min/avg RTT
- UDP and TCP probe modes
- Arrowheads on the path line
- Unit tests with `pytest`
- Move the inline JavaScript and CSS into `static/`

## Tech stack

Python, Flask, Scapy, Requests, Server-Sent Events, JavaScript, Leaflet.js, OpenStreetMap tiles, ip-api.com

## Acknowledgments

- Map tiles by [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors
- Geolocation data from [ip-api.com](https://ip-api.com)
- Maps rendered with [Leaflet](https://leafletjs.com)