#!/usr/bin/env python3
"""
Debug specific API issues
"""

import requests
import json

BACKEND_URL = "https://crm-central-24.preview.emergentagent.com/api"
TEST_CREDENTIALS = {"email": "admin@zenvit.no", "password": "admin123"}

def debug_orders_and_purchases():
    # Login first
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_CREDENTIALS)
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get customers and products
    customers_response = requests.get(f"{BACKEND_URL}/customers", headers=headers)
    products_response = requests.get(f"{BACKEND_URL}/products", headers=headers)
    
    if customers_response.status_code != 200 or products_response.status_code != 200:
        print("❌ Failed to get customers or products")
        return
    
    customers = customers_response.json()
    products = products_response.json()
    
    if not customers or not products:
        print("❌ No customers or products available")
        return
    
    print(f"✅ Found {len(customers)} customers and {len(products)} products")
    
    # Test order creation with detailed error info
    customer = customers[0]
    product = products[0]
    
    order_data = {
        "customer_id": customer["id"],
        "items": [
            {
                "product_id": product["id"],
                "quantity": 1,
                "sale_price": product.get("price", 299.0),
                "discount": 0
            }
        ],
        "channel": "Direct",
        "shipping_paid_by_customer": 99.0,
        "shipping_cost": 50.0,
        "payment_method": "Card",
        "notes": "Debug test order"
    }
    
    print(f"\n🔍 Testing order creation with customer: {customer['name']}, product: {product['name']}")
    
    order_response = requests.post(f"{BACKEND_URL}/orders", headers=headers, json=order_data)
    print(f"Order response status: {order_response.status_code}")
    
    if order_response.status_code != 201:
        print(f"Order response text: {order_response.text}")
    else:
        print("✅ Order created successfully")
        order_id = order_response.json().get("id")
        if order_id:
            # Test order status update
            status_response = requests.put(f"{BACKEND_URL}/orders/{order_id}/status?status=Shipped", headers=headers)
            print(f"Order status update: {status_response.status_code}")
    
    # Test purchase creation
    suppliers_response = requests.get(f"{BACKEND_URL}/suppliers", headers=headers)
    if suppliers_response.status_code != 200:
        print("❌ Failed to get suppliers")
        return
    
    suppliers = suppliers_response.json()
    if not suppliers:
        print("❌ No suppliers available")
        return
    
    supplier = suppliers[0]
    
    purchase_data = {
        "supplier_id": supplier["id"],
        "items": [
            {
                "product_id": product["id"],
                "quantity": 10
            }
        ],
        "notes": "Debug test purchase"
    }
    
    print(f"\n🔍 Testing purchase creation with supplier: {supplier['name']}")
    
    purchase_response = requests.post(f"{BACKEND_URL}/purchases", headers=headers, json=purchase_data)
    print(f"Purchase response status: {purchase_response.status_code}")
    
    if purchase_response.status_code != 201:
        print(f"Purchase response text: {purchase_response.text}")
    else:
        print("✅ Purchase created successfully")
        purchase_id = purchase_response.json().get("id")
        if purchase_id:
            # Test purchase receive
            receive_response = requests.put(f"{BACKEND_URL}/purchases/{purchase_id}/receive", headers=headers)
            print(f"Purchase receive: {receive_response.status_code}")

if __name__ == "__main__":
    debug_orders_and_purchases()