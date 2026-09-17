from scapy.all import IP, ICMP, sr1

max_hops = 20

for i in range(1, max_hops+1):
    pkt = IP(dst = "8.8.8.8", ttl=i)/ICMP()
    result = sr1(pkt, timeout = 2, verbose=0)
    
    if result == None:
        continue

    print("Hop #%d: %s" % (i, result.src))

    if result.type == 0:
        break