#!/usr/bin/env python3
"""
Check which endpoints exist and work
"""

import requests

BACKEND_URL = "https://inventory-zen-1.preview.emergentagent.com/api"
TEST_CREDENTIALS = {"email": "admin@zenvit.no", "password": "admin123"}

def check_endpoints():
    # Login first
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_CREDENTIALS)
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # List of endpoints to check
    endpoints = [
        ("GET", "/products", "Products list"),
        ("GET", "/stock", "Stock list"),
        ("POST", "/stock/adjust", "Stock adjustment"),
        ("GET", "/stock/movements", "Stock movements"),
        ("GET", "/customers", "Customers list"),
        ("GET", "/suppliers", "Suppliers list"),
        ("GET", "/orders", "Orders list"),
        ("GET", "/purchases", "Purchases list"),
        ("GET", "/tasks", "Tasks list"),
        ("GET", "/expenses", "Expenses list"),
        ("GET", "/dashboard", "Dashboard"),
        ("GET", "/reports/daily", "Daily report"),
        ("GET", "/reports/monthly", "Monthly report"),
        ("GET", "/search?q=test", "Search"),
        ("GET", "/automation/status", "Automation status"),
        ("POST", "/automation/check-low-stock", "Low stock check")
    ]
    
    print("🔍 Checking endpoint availability:")
    print("=" * 50)
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(f"{BACKEND_URL}{endpoint}", headers=headers, json={}, timeout=10)
            
            status = response.status_code
            if status == 200 or status == 201:
                print(f"✅ {description}: {status}")
            elif status == 404:
                print(f"❌ {description}: NOT FOUND (404)")
            elif status == 405:
                print(f"⚠️  {description}: METHOD NOT ALLOWED (405)")
            elif status == 422:
                print(f"⚠️  {description}: VALIDATION ERROR (422)")
            elif status == 500:
                print(f"🔥 {description}: SERVER ERROR (500)")
            else:
                print(f"⚠️  {description}: {status}")
                
        except Exception as e:
            print(f"❌ {description}: CONNECTION ERROR - {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    check_endpoints()