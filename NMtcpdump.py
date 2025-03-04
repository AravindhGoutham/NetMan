#!/usr/bin/env python3

from scapy.all import rdpcap, IPv6, Ether, ICMPv6EchoRequest
def eui64_to_mac(eui64):
    eui64_parts = eui64.split(":")
    if len(eui64_parts) != 4:
        return None

    # Convert EUI-64 format back to MAC address
    mac = [
        eui64_parts[0][:2], eui64_parts[0][2:4],
        eui64_parts[1][:2], eui64_parts[2][2:4],
        eui64_parts[3][:2], eui64_parts[3][2:4]
    ]
    # Flip the 7th bit of the first byte using hex() and zfill(2)
    flipped_byte = int(mac[0], 16) ^ 0x02  # XOR with 0x02 to toggle the U/L bit
    mac[0] = hex(flipped_byte)[2:].zfill(2)  # Convert back to a two-character hex string
    return ":".join(mac)
# Load the pcap file
packets = rdpcap("capture.pcap")
# Dictionary to store extracted MAC addresses
r2_r3_macs = {}
# Parse packets and extract ICMPv6 Echo Requests
for pkt in packets:
    if pkt.haslayer(IPv6) and pkt.haslayer(ICMPv6EchoRequest):
        src_ipv6 = pkt[IPv6].src  # Extract source IPv6
        # Extract the last 64 bits (EUI-64 part)
        eui64 = ":".join(src_ipv6.split(":")[-4:])
        # Convert EUI-64 to MAC address
        mac_address = eui64_to_mac(eui64)
        if mac_address:
            r2_r3_macs[src_ipv6] = mac_address
            print(f"Extracted: IPv6={src_ipv6} -> MAC={mac_address}")
# Print the final extracted MAC addresses
print("\nExtracted MAC addresses for R2-F0/0 and R3-F0/0:")
if r2_r3_macs:
    for ipv6, mac in r2_r3_macs.items():
        print(f"IPv6: {ipv6} -> MAC: {mac}")
else:
    print("No matching MAC addresses found. Check pcap file and ICMPv6 requests.")
