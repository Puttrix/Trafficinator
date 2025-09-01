#!/usr/bin/env python3
import os
import random
import ipaddress

# Exactly mirror the code from loader.py
RANDOMIZE_VISITOR_COUNTRIES = os.environ.get("RANDOMIZE_VISITOR_COUNTRIES", "true").lower() == "true"

# Use only a subset to make debugging easier
COUNTRY_IP_RANGES = {
    'United States': {
        'probability': 0.5,  # 50% US traffic
        'ip_ranges': [
            '173.252.0.0/16',    # Facebook range (for variety)
            '74.125.0.0/16',     # Google range
        ]
    },
    'Sweden': {
        'probability': 0.5,  # 50% Swedish traffic  
        'ip_ranges': [
            '194.47.0.0/16',     # Telia Sweden
        ]
    },
}

def choose_country_and_ip():
    """Choose a country based on realistic distribution and generate an IP from that country.
    
    Returns:
        tuple: (country_name, ip_address) or (None, None) if disabled
    """
    print(f"DEBUG: RANDOMIZE_VISITOR_COUNTRIES={RANDOMIZE_VISITOR_COUNTRIES}")
    
    if not RANDOMIZE_VISITOR_COUNTRIES:
        print("DEBUG: Country randomization disabled, returning None, None")
        return None, None
    
    print("DEBUG: Starting country selection...")
    rand = random.random()
    print(f"DEBUG: rand={rand}")
    current_prob = 0.0
    
    for country, config in COUNTRY_IP_RANGES.items():
        current_prob += config['probability']
        print(f"DEBUG: country={country}, current_prob={current_prob}")
        if rand < current_prob:
            print(f"DEBUG: Selected country: {country}")
            # Choose random IP range from this country
            ip_range = random.choice(config['ip_ranges'])
            print(f"DEBUG: Selected IP range: {ip_range}")
            
            # Generate random IP within the chosen range
            network = ipaddress.ip_network(ip_range)
            print(f"DEBUG: Network: {network}, num_addresses={network.num_addresses}")
            
            # Get a random IP from the network (avoiding network and broadcast addresses)
            try:
                random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
                print(f"DEBUG: Generated IP: {random_ip}")
                return country, str(random_ip)
            except Exception as e:
                print(f"ERROR generating IP: {e}")
                return None, None
    
    # Fallback to US if probabilities don't add up
    print("DEBUG: Fallback to US")
    us_range = random.choice(COUNTRY_IP_RANGES['United States']['ip_ranges'])
    network = ipaddress.ip_network(us_range)
    random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
    return 'United States', str(random_ip)

# Test the function
print("Testing choose_country_and_ip()...")
try:
    country, ip = choose_country_and_ip()
    print(f"RESULT: country={country}, ip={ip}")
except Exception as e:
    print(f"EXCEPTION: {e}")
    import traceback
    traceback.print_exc()