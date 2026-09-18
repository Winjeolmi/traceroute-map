import requests

# Returns a dictionary of location information
def geolocate_ip(ip):
    # Check first if the IP is private
    if check_public_ip(ip) is False:
        return None

    # Create URL to the IP geolocation website
    url = "http://ip-api.com/json/" + ip
    response = requests.get(url)
    data = response.json()

    # Retrieve needed information from the json
    location_info = {"lat": data["lat"],
                     "lon": data["lon"],
                     "city": data["city"], 
                     "country": data["country"],
                     "isp": data["isp"]}

    # Return the dictionary
    return location_info

# Checks through IP address to see if it is a public or private address
def check_public_ip(ip):
    # Split the IP address by the .
    ip_part1 = ip.split(".")[0]
    ip_part2 = int(ip.split(".")[1])

    # List of private IP address ranges:
    # 10.0.0.0 – 10.255.255.255
    # 172.16.0.0 – 172.31.255.255
    # 192.168.0.0 – 192.168.255.255
    # 127.0.0.0 – 127.255.255.255
    if (ip.startswith("10.") or 
        ip.startswith("127.") or 
        ip.startswith("192.168.") or 
        (ip_part1 == "172" and 16 <= ip_part2 and ip_part2 <= 31)): 
        return False
    else:
        return True
