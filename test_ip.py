#!/usr/bin/env python3
import ipaddress
import random

# Test some of the IP ranges from the code to see if there are issues
test_ranges = [
    '173.252.0.0/16',
    '78.46.0.0/15', 
    '51.140.0.0/14',
    '142.0.0.0/8',
    '163.172.0.0/16'
]

for ip_range in test_ranges:
    try:
        network = ipaddress.ip_network(ip_range)
        print(f"{ip_range}: num_addresses = {network.num_addresses}")
        print(f"  network_address = {network.network_address}")
        print(f"  broadcast_address = {network.broadcast_address}")
        print(f"  range for random: 1 to {network.num_addresses - 2}")
        
        # Try generating a random IP
        if network.num_addresses > 2:
            random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
            print(f"  sample IP: {random_ip}")
        else:
            print(f"  ERROR: Network too small for random IP generation!")
        print()
    except Exception as e:
        print(f"Error with {ip_range}: {e}")