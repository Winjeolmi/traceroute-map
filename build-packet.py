from scapy.all import IP, ICMP, sr1
import sys # build-packet.py traceroute <destination IP> <max_hops>
import time # To calculate execution time
import socket

# Checks if command line arguments were entered correctly
if len(sys.argv) != 4:
    print("Please provide valid command line arguments")
    exit(0)

# Third argument is destination IP, check if valid domain name is input
try:
    dest_ip = socket.gethostbyname(sys.argv[2])
except socket.gaierror:
    print("Please enter a valid domain name")
    exit(0)

# Fourth argument is max hops
max_hops = int(sys.argv[3])

print("Resolving %s --> %s" % (sys.argv[2], dest_ip))

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

    # If we reach an unreachable node, continue
    if result == None:
        print(" *  *  *")
        continue

    # Print out result message
    print("Hop #%d: %s\t Elapsed time: %.2f ms" % (i, result.src, exec_time * 1000))

    # If we reached the destination break the loop
    if result.type == 0:
        break