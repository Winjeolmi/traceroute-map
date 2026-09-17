from scapy.all import IP, ICMP, sr1
import sys # build-packet.py traceroute <destination IP> <max_hops>
import time

if len(sys.argv) != 4:
    print("Please provide valid command line arguments")
    exit(0)

dst = sys.argv[2]
max_hops = int(sys.argv[3])

for i in range(1, max_hops+1):
    pkt = IP(dst = "8.8.8.8", ttl=i)/ICMP()
    result = sr1(pkt, timeout = 2, verbose=0)
    
    if result == None:
        continue

    print("Hop #%d: %s" % (i, result.src))

    if result.type == 0:
        break