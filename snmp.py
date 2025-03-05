#!/usr/bin/env python3

import json
import time
import matplotlib.pyplot as plt
from easysnmp import Session

routers = {
    "R1": "7.0.0.1",
    "R2": "40.0.0.6",
    "R3": "40.0.0.4",
    "R4": "25.0.0.1",
    "R5": "40.0.0.1"
}

snmp_version = 3

# SNMPv3 Credentials - Define SNMPv3 credentials
snmp_user = "aravindh"
auth_protocol = "SHA"
auth_password = "aravindh"
priv_protocol = "AES128"
priv_password = "aravindh"

# SNMP OIDs
oid_ipv4 = "1.3.6.1.2.1.4.20.1.1"  # OID for IPv4 addresses
oid_ipv6 = "1.3.6.1.2.1.4.34.1.3.2.16"  # OID for IPv6 addresses
oid_ifstatus = "1.3.6.1.2.1.2.2.1.8"  # OID for interface status (up/down)
oid_ifname = "1.3.6.1.2.1.31.1.1.1.1"  # OID for interface names
oid_cpu_util = "1.3.6.1.4.1.9.2.1.58.0"  # OID for CPU utilization

# Function to create an SNMP session for communication with the router
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
        return session  # Return the session object if successful
    except Exception as e:
        print(f"[ERROR] Failed to create SNMP session for {target}: {e}")  # Error handling
        return None

# Function to perform an SNMP walk for a given OID and return results as a dictionary
def snmp_walk(session, oid):
    try:
        return {entry.oid: entry.value for entry in session.walk(oid)}  # SNMP walk result as dictionary
    except Exception as e:
        print(f"[ERROR] SNMP Walk failed for OID {oid}: {e}")
        return {}

# Function to format the IPv6 address from the OID suffix
def format_ipv6_address(oid_suffix):
    ipv6_parts = oid_suffix.split(".")[-16:]  # Extract last 16 parts of the OID for IPv6
    ipv6_hex = [f"{int(part):02x}" for part in ipv6_parts]  # Convert each part to hex
    ipv6_address = ":".join(["".join(ipv6_hex[i:i+2]) for i in range(0, 16, 2)])  # Format as IPv6
    return ipv6_address  # Return the formatted IPv6 address

# Function to fetch data from all routers
def fetch_router_data():
    network_data = {}  # Dictionary to store network data
    interface_status = {}  # Dictionary to store interface status (Up/Down)

    for router, ip in routers.items():
        print(f"Fetching SNMP data from {router} ({ip})")

        session = create_snmp_session(ip)  # Create SNMP session for the router
        if not session:
            continue

        ipv4_addresses = snmp_walk(session, oid_ipv4)  #IPv4 addresses
        ipv6_addresses = snmp_walk(session, oid_ipv6)  #IPv6 addresses
        if_status = snmp_walk(session, oid_ifstatus)  #interface statuses
        if_names = snmp_walk(session, oid_ifname)  #interface names
        network_data[router] = {"addresses": {}}  # Initialize network data for this router
        interface_status[router] = {}  # Initialize interface status for this router

        # Process IPv4 addresses
        for oid, addr in ipv4_addresses.items():
            interface_idx = oid.split(".")[-1]  # Get interface index from the OID
            interface_name = if_names.get(f"iso.3.6.1.2.1.31.1.1.1.1.{interface_idx}", f"Interface-{interface_idx}")  # Get interface name
            network_data[router]["addresses"].setdefault(interface_name, {})["v4"] = addr  # Store IPv4 address

        # Process IPv6 addresses (supporting multiple IPv6 addresses per interface)
        for oid, addr in ipv6_addresses.items():
            oid_parts = oid.split(".")  # Split OID to extract interface index and address
            if len(oid_parts) > 16:
                interface_idx = oid_parts[-17]  # Extract interface index for IPv6
                interface_name = if_names.get(f"iso.3.6.1.2.1.31.1.1.1.1.{interface_idx}", f"Interface-{interface_idx}")  # Get interface name
                ipv6_addr = format_ipv6_address(oid)  # Format the IPv6 address from OID

                # Ensure multiple IPv6 addresses are stored as a list
                if "v6" not in network_data[router]["addresses"].setdefault(interface_name, {}):
                    network_data[router]["addresses"][interface_name]["v6"] = []

                network_data[router]["addresses"][interface_name]["v6"].append(ipv6_addr)  # Store IPv6 address

        # Process interface status
        for oid, status in if_status.items():
            interface_idx = oid.split(".")[-1]  # Extract interface index from OID
            interface_name = if_names.get(f"iso.3.6.1.2.1.31.1.1.1.1.{interface_idx}", f"Interface-{interface_idx}")  # Get interface name
            interface_status[router][interface_name] = "Up" if status == "1" else "Down"  # Store status as "Up" or "Down"

    return network_data, interface_status  # Return the collected network data and interface statuses

# Function to save collected network data and interface statuses to a JSON file
def save_data_to_json(router_info, interface_status):
    filename = "Router-info.json"  #output file name
    with open(filename, "w") as f:
        json.dump({"network": router_info, "interface_status": interface_status}, f, indent=4)  # Write to file in JSON format
    print(f"Data saved to {filename}")

# Function to monitor and plot CPU utilization
def monitor_cpu_util():
    cpu_data = []  # List to store CPU usage data
    timestamps = []  # List to store corresponding timestamps

    print("Monitoring CPU Utilization for 2 minutes...")  # Start monitoring message

    session = create_snmp_session(routers["R1"])  # Create SNMP session for R1
    if not session:  # If session creation fails, return from function
        return

    start_time = time.time()  # Record the start time
    while time.time() - start_time < 120:  # Monitor for 2 minutes
        try:
            cpu_usage = session.get(oid_cpu_util).value  # Fetch CPU usage
            usage = int(cpu_usage)  # Convert CPU usage to integer
            cpu_data.append(usage)  # Add CPU usage to data list
            timestamps.append(time.time() - start_time)  # Add current timestamp to list
            print(f"CPU Usage: {usage}%")  # Print the current CPU usage
        except Exception as e:
            print(f"[WARNING] Failed to retrieve CPU data: {e}")  # Handle errors in fetching CPU data
        time.sleep(5)  # Wait for 5 seconds before the next measurement

    # Plot and save the graph of CPU utilization
    plt.figure(figsize=(10, 5))  # Create a figure with specified size
    plt.plot(timestamps, cpu_data, marker='o', linestyle='-', color='b', label="CPU Usage")  # Plot the data
    plt.xlabel("Time (seconds)")  # Label for X-axis
    plt.ylabel("CPU Utilization (%)")  # Label for Y-axis
    plt.title("CPU Utilization of R1")  # Title for the plot
    plt.legend()  # Show legend for the plot
    plt.grid()  # Add grid to the plot

    filename = "cpu_utilization.jpg"  # Define output file name
    plt.savefig(filename)  # Save the plot as an image
    print(f"CPU utilization graph saved as {filename}")  # Confirmation message

# Main Execution
network_data, interface_status = fetch_router_data()  # Fetch the network data and interface statuses
save_data_to_json(network_data, interface_status)  # Save the collected data to a JSON file
monitor_cpu_util()  # Monitor and plot CPU utilization
