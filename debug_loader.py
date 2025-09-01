#!/usr/bin/env python3
import os
import asyncio
import random
import ipaddress

# Test the exact country/IP logic
RANDOMIZE_VISITOR_COUNTRIES = True

COUNTRY_IP_RANGES = {
    'United States': {
        'probability': 0.35,  
        'ip_ranges': ['173.252.0.0/16']  # Just one range for simplicity
    },
    'Sweden': {
        'probability': 0.65,  # Make Sweden very likely for testing
        'ip_ranges': ['194.47.0.0/16']
    },
}

def choose_country_and_ip():
    """Choose a country based on realistic distribution and generate an IP from that country."""
    if not RANDOMIZE_VISITOR_COUNTRIES:
        return None, None
    
    print(f"DEBUG: RANDOMIZE_VISITOR_COUNTRIES = {RANDOMIZE_VISITOR_COUNTRIES}")
    
    rand = random.random()
    print(f"DEBUG: Random value = {rand}")
    current_prob = 0.0
    
    for country, config in COUNTRY_IP_RANGES.items():
        current_prob += config['probability']
        print(f"DEBUG: Checking {country}, current_prob = {current_prob}")
        if rand < current_prob:
            print(f"DEBUG: Selected country: {country}")
            # Choose random IP range from this country
            ip_range = random.choice(config['ip_ranges'])
            print(f"DEBUG: Selected IP range: {ip_range}")
            # Generate random IP within the chosen range
            network = ipaddress.ip_network(ip_range)
            print(f"DEBUG: Network: {network}, num_addresses = {network.num_addresses}")
            # Get a random IP from the network (avoiding network and broadcast addresses)
            random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
            print(f"DEBUG: Generated IP: {random_ip}")
            return country, str(random_ip)
    
    print("DEBUG: Fallback to US")
    # Fallback to US if probabilities don't add up
    us_range = random.choice(COUNTRY_IP_RANGES['United States']['ip_ranges'])
    network = ipaddress.ip_network(us_range)
    random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
    return 'United States', str(random_ip)

async def test_visit():
    """Simulate a minimal visit function"""
    print("Starting test visit...")
    
    # Test country/IP selection
    country, visitor_ip = choose_country_and_ip()
    print(f"Selected: {country} -> {visitor_ip}")
    
    # Just print what would be sent to Matomo
    params = {
        'idsite': 1,
        'rec': 1,
        'url': 'http://example.com/test',
        'action_name': 'Test Page'
    }
    
    if visitor_ip:
        params['cip'] = visitor_ip
        
    print(f"Would send to Matomo: {params}")

async def main():
    print("Testing country randomization...")
    for i in range(3):
        print(f"\n--- Test {i+1} ---")
        await test_visit()

if __name__ == "__main__":
    asyncio.run(main())