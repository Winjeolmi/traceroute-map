from scapy.all import IP, ICMP

pkt = IP(dst="8.8.8.8", ttl=1)/ICMP()
pkt.show()