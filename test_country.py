#!/usr/bin/env python3
import random
import ipaddress

# Copy the exact logic from the loader.py
COUNTRY_IP_RANGES = {
    'United States': {
        'probability': 0.35,
        'ip_ranges': [
            '173.252.0.0/16',
            '74.125.0.0/16',
            '208.67.0.0/16',
            '192.30.252.0/22',
            '199.232.0.0/16',
            '23.0.0.0/8',
            '104.16.0.0/12',
            '142.250.0.0/15',
        ]
    },
    'Germany': {
        'probability': 0.10,
        'ip_ranges': [
            '78.46.0.0/15',
            '5.9.0.0/16',
            '136.243.0.0/16',
            '88.198.0.0/16',
            '46.4.0.0/16',
            '80.156.0.0/16',
        ]
    },
    'Sweden': {
        'probability': 0.03,
        'ip_ranges': [
            '194.47.0.0/16',
            '81.230.0.0/16',
            '78.72.0.0/15',
        ]
    },
}

def choose_country_and_ip():
    """Test the exact logic from the function"""
    print("Testing choose_country_and_ip()...")
    
    rand = random.random()
    print(f"Random value: {rand}")
    current_prob = 0.0
    
    for country, config in COUNTRY_IP_RANGES.items():
        current_prob += config['probability']
        print(f"Checking {country}: current_prob = {current_prob}")
        if rand < current_prob:
            print(f"Selected country: {country}")
            # Choose random IP range from this country
            ip_range = random.choice(config['ip_ranges'])
            print(f"Selected IP range: {ip_range}")
            # Generate random IP within the chosen range
            network = ipaddress.ip_network(ip_range)
            print(f"Network: {network}, num_addresses: {network.num_addresses}")
            # Get a random IP from the network (avoiding network and broadcast addresses)
            random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
            print(f"Generated IP: {random_ip}")
            return country, str(random_ip)
    
    # Fallback to US if probabilities don't add up
    print("Fallback to US")
    us_range = random.choice(COUNTRY_IP_RANGES['United States']['ip_ranges'])
    network = ipaddress.ip_network(us_range)
    random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
    return 'United States', str(random_ip)

# Test the function multiple times
for i in range(5):
    print(f"\n--- Test {i+1} ---")
    try:
        country, ip = choose_country_and_ip()
        print(f"Result: {country} -> {ip}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()