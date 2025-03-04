#!/usr/bin/env python3

import re
from netmiko import ConnectHandler
import time

r4_details = {
    'device_type': 'cisco_ios',
    'host': '25.0.0.1',
    'username': 'admin',
    'password': 'admin'
}

print("Connecting to R4")
r4_conn = ConnectHandler(**r4_details)
r4_conn.enable()

output = r4_conn.send_command("show ipv6 neighbors")
print("R4 neighbor output:", output)

#MAC address of R5 Fa0/0
r5_mac = "ca05.4c8c.0000"

# Extract all IPv6 addresses along with their associated MAC addresses
neighbor_entries = re.findall(r'([\da-fA-F:]+)\s+\d+\s+([\da-fA-F.]+)\s+\w+\s+\S+', output)

r5_ipv6 = None
for ipv6, mac in neighbor_entries:
    if mac.lower() == r5_mac.lower():
        r5_ipv6 = ipv6
        break

if not r5_ipv6:
    print("ERROR: Could not determine R5's IPv6 address from R4.")
    r4_conn.disconnect()
    exit(1)

print(f"Found R5 IPv6 address: {r5_ipv6}")
r4_conn.disconnect()

# R5 connection using the IPv6 address
r5_details = {
    'device_type': 'cisco_ios',
    'host': r5_ipv6,
    'username': 'admin',
    'password': 'admin',
}

print(f"Connecting to R5 using IPv6 address {r5_ipv6}")
try:
    r5 = ConnectHandler(**r5_details)
    r5.enable()

    r2_mac = "ca02.4c31.0000"
    r3_mac = "ca03.4c50.0000"

    # Define DHCP pool configurations:
    dhcp_commands = [
        # Static DHCP binding for R2-F0/0
        "ip dhcp pool R2_POOL",
        " host 40.0.0.2 255.255.255.0",
        " hardware-address " + r2_mac,
        " exit",
        # Static DHCP binding for R3-F0/0
        "ip dhcp pool R3_POOL",
        " host 40.0.0.3 255.255.255.0",
        " hardware-address " + r3_mac,
        " exit",
        # Dynamic DHCP pool for R4-Fa0/0
        "ip dhcp pool R4_POOL",
        " network 40.0.0.0 255.255.255.0",
        " default-router 40.0.0.1",
        " exit"
    ]

    print("Configuring DHCP pools on R5")
    dhcp_config_output = r5.send_config_set(dhcp_commands)
    print("DHCP configuration output:", dhcp_config_output)

    # Allow some time for DHCP clients to request and receive addresses
    time.sleep(10)

    # Retrieve the current DHCP binding table
    dhcp_binding_output = r5.send_command("show ip dhcp binding")
    print("DHCP Binding Table:", dhcp_binding_output)

    # Extract IPv4 addresses from the DHCP binding output using regex
    dhcp_ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', dhcp_binding_output)
    print("List of DHCPv4 Client IP Addresses:")
    for ip in dhcp_ips:
        print(ip)

    r5.disconnect()

except Exception as e:
    print(f"Failed to connect to R5: {e}")
