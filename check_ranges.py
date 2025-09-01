#!/usr/bin/env python3
import ipaddress

# All IP ranges from the actual code
all_ranges = [
    # US ranges
    '173.252.0.0/16', '74.125.0.0/16', '208.67.0.0/16', '192.30.252.0/22',
    '199.232.0.0/16', '23.0.0.0/8', '104.16.0.0/12', '142.250.0.0/15',
    
    # Germany ranges  
    '78.46.0.0/15', '5.9.0.0/16', '136.243.0.0/16', '88.198.0.0/16',
    '46.4.0.0/16', '80.156.0.0/16',
    
    # UK ranges
    '51.140.0.0/14', '185.40.0.0/16', '86.0.0.0/12', '109.144.0.0/14',
    '2.96.0.0/11',
    
    # Canada ranges
    '142.0.0.0/8', '206.47.0.0/16', '24.0.0.0/13', '99.224.0.0/11',
    
    # France ranges
    '163.172.0.0/16', '51.15.0.0/16', '212.129.0.0/16', '90.0.0.0/9',
    
    # Australia ranges
    '203.0.0.0/8', '144.132.0.0/16', '101.160.0.0/11', '180.150.0.0/15',
    
    # Netherlands ranges
    '185.3.0.0/16', '146.185.0.0/16', '31.220.0.0/16', '213.154.0.0/16',
    
    # Japan ranges
    '103.4.0.0/14', '210.0.0.0/7', '133.0.0.0/8',
    
    # Sweden ranges
    '194.47.0.0/16', '81.230.0.0/16', '78.72.0.0/15',
    
    # Brazil ranges
    '200.0.0.0/7', '177.0.0.0/8', '191.0.0.0/8',
    
    # Other countries ranges
    '85.0.0.0/8', '195.0.0.0/8', '62.0.0.0/8', '91.0.0.0/8',
    '41.0.0.0/8', '1.0.0.0/8', '27.0.0.0/8', '36.0.0.0/8',
]

print(f"Checking {len(all_ranges)} IP ranges...")

problematic_ranges = []

for ip_range in all_ranges:
    try:
        network = ipaddress.ip_network(ip_range)
        if network.num_addresses <= 2:
            problematic_ranges.append(f"{ip_range}: Too small ({network.num_addresses} addresses)")
        elif network.num_addresses > 2**24:  # Very large ranges might be slow
            print(f"LARGE: {ip_range} has {network.num_addresses} addresses")
    except Exception as e:
        problematic_ranges.append(f"{ip_range}: ERROR - {e}")

if problematic_ranges:
    print("\nProblematic ranges found:")
    for issue in problematic_ranges:
        print(f"  {issue}")
else:
    print("\nAll IP ranges are valid and have sufficient addresses.")