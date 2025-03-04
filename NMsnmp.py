#!/usr/bin/env python3

import json
import time
import matplotlib.pyplot as plt
from easysnmp import Session

# SNMP Configuration
routers = {
    "R1": "7.0.0.1",
    "R2": "40.0.0.6",
    "R3": "40.0.0.4",
    "R4": "25.0.0.1",
    "R5": "40.0.0.1"
}

snmp_version = 3  # Using SNMPv3

# SNMPv3 Credentials
snmp_user = "aravindh"
auth_protocol = "SHA"
auth_password = "aravindh"
priv_protocol = "AES128"
priv_password = "aravindh"

# SNMP OIDs
oid_ipv4 = "1.3.6.1.2.1.4.20.1.1"
oid_ipv6 = "1.3.6.1.2.1.4.34.1.3.2.16"
oid_ifstatus = "1.3.6.1.2.1.2.2.1.8"
oid_ifname = "1.3.6.1.2.1.31.1.1.1.1"
oid_cpu_util = "1.3.6.1.4.1.9.2.1.58.0"


def create_snmp_session(target):
    try:
        session = Session(
            hostname=target,
            version=3,
            security_level="authPriv",
            security_username=snmp_user,
            auth_protocol=auth_protocol,
            auth_password=auth_password,
            privacy_protocol=priv_protocol,
            privacy_password=priv_password
        )
        return session
    except Exception as e:
        print(f"[ERROR] Failed to create SNMP session for {target}: {e}")
        return None


def snmp_walk(session, oid):
    """Perform an SNMP Walk and return results as a dictionary."""
    try:
        return {entry.oid: entry.value for entry in session.walk(oid)}
    except Exception as e:
        print(f"[ERROR] SNMP Walk failed for OID {oid}: {e}")
        return {}


def format_ipv6_address(oid_suffix):
    ipv6_parts = oid_suffix.split(".")[-16:]
    ipv6_hex = [f"{int(part):02x}" for part in ipv6_parts]
    ipv6_address = ":".join(["".join(ipv6_hex[i:i+2]) for i in range(0, 16, 2)])
    return ipv6_address


def fetch_router_data():
    network_data = {}
    interface_status = {}

    for router, ip in routers.items():
        print(f"Fetching SNMP data from {router} ({ip})")

        session = create_snmp_session(ip)
        if not session:
            continue

        ipv4_addresses = snmp_walk(session, oid_ipv4)
        ipv6_addresses = snmp_walk(session, oid_ipv6)
        if_status = snmp_walk(session, oid_ifstatus)
        if_names = snmp_walk(session, oid_ifname)

        network_data[router] = {"addresses": {}}
        interface_status[router] = {}

        # Process IPv4 addresses
        for oid, addr in ipv4_addresses.items():
            interface_idx = oid.split(".")[-1]
            interface = if_names.get(interface_idx, f"Interface-{interface_idx}")
            network_data[router]["addresses"].setdefault(interface, {})["v4"] = addr

        # Process IPv6 addresses (supporting multiple IPv6 addresses per interface)
        for oid, addr in ipv6_addresses.items():
            oid_parts = oid.split(".")
            if len(oid_parts) > 16:
                interface_idx = oid_parts[-17]

                interface = if_names.get(interface_idx, f"Interface-{interface_idx}")
                ipv6_addr = format_ipv6_address(oid)

                # Ensure multiple IPv6 addresses are stored as a list
                if "v6" not in network_data[router]["addresses"].setdefault(interface, {}):
                    network_data[router]["addresses"][interface]["v6"] = []

                network_data[router]["addresses"][interface]["v6"].append(ipv6_addr)

        # Process interface status
        for oid, status in if_status.items():
            interface_idx = oid.split(".")[-1]
            interface = if_names.get(interface_idx, f"Interface-{interface_idx}")
            interface_status[router][interface] = "Up" if status == "1" else "Down"

    return network_data, interface_status


def save_data_to_json(network_data, interface_status):
    filename = "network_data.json"
    with open(filename, "w") as f:
        json.dump({"network": network_data, "interface_status": interface_status}, f, indent=4)
    print(f"Data saved to {filename}")


def monitor_cpu_util():
    cpu_data = []
    timestamps = []

    print("Monitoring CPU Utilization for 2 minutes...")

    session = create_snmp_session(routers["R1"])
    if not session:
        return

    start_time = time.time()
    while time.time() - start_time < 120:  # Run for 2 minutes
        try:
            cpu_usage = session.get(oid_cpu_util).value
            usage = int(cpu_usage)
            cpu_data.append(usage)
            timestamps.append(time.time() - start_time)
            print(f"CPU Usage: {usage}%")
        except Exception as e:
            print(f"[WARNING] Failed to retrieve CPU data: {e}")
        time.sleep(5)

    # Plot and save the graph
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, cpu_data, marker='o', linestyle='-', color='b', label="CPU Usage")
    plt.xlabel("Time (seconds)")
    plt.ylabel("CPU Utilization (%)")
    plt.title("CPU Utilization of R1")
    plt.legend()
    plt.grid()

    filename = "cpu_utilization.jpg"
    plt.savefig(filename)
    print(f"CPU utilization graph saved as {filename}")


# Main Execution
network_data, interface_status = fetch_router_data()
save_data_to_json(network_data, interface_status)
monitor_cpu_util()
