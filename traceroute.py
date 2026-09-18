from scapy.all import IP, ICMP, sr1
import time # To calculate execution time

def run_traceroute(dest_ip, max_hops):
    # List of hop dictionaries to return
    hops = []

    # For i from 1 to max hops
    for i in range(1, max_hops+1):
        # Build a packet with ttl = i, ttl will increment by 1 every loop
        pkt = IP(dst = dest_ip, ttl=i)/ICMP()

        start_time = time.perf_counter()
        # Send and receive the packet
        result = sr1(pkt, timeout = 2, verbose=0)
        end_time = time.perf_counter()

        # Calculate the total execution time
        exec_time = end_time - start_time

        # If we reach an unreachable node, append None
        if result == None:
            hop_data = {"ttl": i, "ip": None, "rtt_ms": None}
        # Else create a hop dictionary
        else:
            hop_data = {"ttl": i, "ip": result.src, "rtt_ms": round(exec_time * 1000, 2)}

        hops.append(hop_data)

        # If we reached the destination break the loop
        if result is not None and result.type == 0:
            break

    return hops