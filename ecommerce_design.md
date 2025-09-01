# Ecommerce Tracking Design for Trafficinator

## Matomo Ecommerce Parameters
- `idgoal=0` - Required for ecommerce orders
- `ec_id` - Unique order ID (required)
- `ec_items` - JSON array of items (required) 
- `revenue` - Total order value (required)
- `ec_st` - Subtotal (optional)
- `ec_tx` - Tax amount (optional)

## Product Categories & Items
- Electronics (smartphones, laptops, tablets)
- Clothing (shirts, pants, shoes)
- Books (fiction, technical, educational)
- Home & Garden (furniture, appliances, tools)
- Sports (equipment, clothing, accessories)

## Purchase Flow Types
1. **Single Item Purchase** (60% of orders)
2. **Multi-Item Purchase** (35% of orders) 
3. **High-Value Purchase** (5% of orders)

## Realistic Order Patterns
- Order values: $10-$500 (weighted toward $20-$100)
- Tax rates: 8-12% depending on country
- Shipping: $0 (free), $5.99, $9.99, $15.99
- Order IDs: UUID format for uniqueness

## Configuration Options
- `ECOMMERCE_PROBABILITY` - % of visits that make a purchase
- `ECOMMERCE_ORDER_VALUE_MIN/MAX` - Price range
- `ECOMMERCE_ITEMS_MIN/MAX` - Items per order
- `ECOMMERCE_TAX_RATE` - Tax percentage
- `ECOMMERCE_SHIPPING_COST` - Shipping options