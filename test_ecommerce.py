#!/usr/bin/env python3
import os
import json

# Set environment variables for testing
os.environ['ECOMMERCE_PROBABILITY'] = '1.0'  # Force ecommerce orders
os.environ['ECOMMERCE_ORDER_VALUE_MIN'] = '20.00'
os.environ['ECOMMERCE_ORDER_VALUE_MAX'] = '200.00'
os.environ['ECOMMERCE_ITEMS_MIN'] = '1'
os.environ['ECOMMERCE_ITEMS_MAX'] = '3'
os.environ['ECOMMERCE_TAX_RATE'] = '0.08'
os.environ['ECOMMERCE_SHIPPING_RATES'] = '0,9.99'

# Import after setting environment variables
import sys
sys.path.append('./matomo-load-baked')
from loader import generate_ecommerce_order, ECOMMERCE_PRODUCTS

def test_ecommerce_order_generation():
    """Test ecommerce order generation"""
    print("Testing ecommerce order generation...")
    
    for i in range(5):
        print(f"\n--- Test Order {i+1} ---")
        
        order = generate_ecommerce_order()
        if order:
            order_id, items_json, revenue, subtotal, tax, shipping = order
            items = json.loads(items_json)
            
            print(f"Order ID: {order_id}")
            print(f"Revenue: ${revenue}")
            print(f"Subtotal: ${subtotal}")
            print(f"Tax: ${tax}")
            print(f"Shipping: ${shipping}")
            print(f"Items ({len(items)}):")
            
            for item in items:
                sku, name, category, price, qty = item
                print(f"  - {qty}x {name} ({sku}) - {category} @ ${price} each")
            
            # Verify calculations
            calculated_subtotal = sum(item[3] * item[4] for item in items)
            calculated_tax = round((calculated_subtotal + shipping) * 0.08, 2)
            calculated_revenue = round(calculated_subtotal + shipping + calculated_tax, 2)
            
            print(f"Verification:")
            print(f"  Subtotal: ${calculated_subtotal} (expected: ${subtotal})")
            print(f"  Tax: ${calculated_tax} (expected: ${tax})")
            print(f"  Revenue: ${calculated_revenue} (expected: ${revenue})")
            
            assert abs(calculated_subtotal - subtotal) < 0.01, "Subtotal mismatch"
            assert abs(calculated_tax - tax) < 0.01, "Tax mismatch"
            assert abs(calculated_revenue - revenue) < 0.01, "Revenue mismatch"
            print("  ✓ All calculations correct")
        else:
            print("No order generated (should not happen with 100% probability)")

def test_product_database():
    """Test product database structure"""
    print("\nTesting product database...")
    
    total_products = 0
    for category, products in ECOMMERCE_PRODUCTS.items():
        print(f"{category}: {len(products)} products")
        total_products += len(products)
        
        # Verify product structure
        for product in products:
            assert 'sku' in product, f"Missing SKU in {category}"
            assert 'name' in product, f"Missing name in {category}"
            assert 'price' in product, f"Missing price in {category}"
            assert product['price'] > 0, f"Invalid price in {category}: {product['price']}"
    
    print(f"Total products: {total_products}")
    print("✓ Product database structure valid")

if __name__ == "__main__":
    test_product_database()
    test_ecommerce_order_generation()
    print("\n✓ All ecommerce tests passed!")