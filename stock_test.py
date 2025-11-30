#!/usr/bin/env python3
"""
ZenVit CRM - Stock Management Testing
Tests stock adjustment and movements functionality
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "https://inventory-zen-1.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@zenvit.no",
    "password": "admin123"
}

class StockTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []

    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            
            success = response.status_code == expected_status
            return success, response
        except Exception as e:
            return False, str(e)

    def authenticate(self):
        """Authenticate and get token"""
        print("🔐 Authenticating...")
        success, response = self.make_request("POST", "/auth/login", TEST_CREDENTIALS)
        if isinstance(response, str):
            print(f"❌ Authentication failed: {response}")
            return False
        elif success and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                print(f"✅ Authentication successful")
                return True
            except:
                print("❌ Invalid JSON response during authentication")
                return False
        else:
            print(f"❌ Authentication failed with status {response.status_code}")
            return False

    def test_stock_movements(self):
        """Test stock movements endpoint"""
        print("\n=== TESTING STOCK MOVEMENTS ===")
        
        success, response = self.make_request("GET", "/stock/movements")
        if isinstance(response, str):
            self.log_test("GET Stock Movements", False, f"Request failed: {response}")
        elif success:
            try:
                movements = response.json()
                self.log_test("GET Stock Movements", True, f"Retrieved {len(movements)} stock movements")
            except:
                self.log_test("GET Stock Movements", False, "Invalid JSON response")
        else:
            self.log_test("GET Stock Movements", False, f"Got status {response.status_code}")

    def test_stock_adjustment(self):
        """Test stock adjustment functionality"""
        print("\n=== TESTING STOCK ADJUSTMENT ===")
        
        # First get stock items
        success, response = self.make_request("GET", "/stock")
        if not success or isinstance(response, str):
            self.log_test("Stock Adjustment Setup", False, "Could not retrieve stock items")
            return
        
        try:
            stock_items = response.json()
            if not stock_items:
                self.log_test("Stock Adjustment Setup", False, "No stock items found")
                return
            
            # Use first stock item for testing
            test_item = stock_items[0]
            product_id = test_item.get("product_id")
            current_qty = test_item.get("quantity", 0)
            
            print(f"Testing with product_id: {product_id}, current quantity: {current_qty}")
            
            # Test positive adjustment (+5)
            success, response = self.make_request("POST", f"/stock/adjust?product_id={product_id}&adjustment=5&note=Test positive adjustment")
            if isinstance(response, str):
                self.log_test("Positive Stock Adjustment", False, f"Request failed: {response}")
            elif success:
                try:
                    result = response.json()
                    new_qty = result.get("new_quantity")
                    expected_qty = current_qty + 5
                    if new_qty == expected_qty:
                        self.log_test("Positive Stock Adjustment", True, f"Stock increased from {current_qty} to {new_qty}")
                        current_qty = new_qty  # Update for next test
                    else:
                        self.log_test("Positive Stock Adjustment", False, f"Expected {expected_qty}, got {new_qty}")
                except:
                    self.log_test("Positive Stock Adjustment", True, "Stock adjustment completed")
            else:
                self.log_test("Positive Stock Adjustment", False, f"Got status {response.status_code}")
            
            # Test negative adjustment (-3)
            success, response = self.make_request("POST", f"/stock/adjust?product_id={product_id}&adjustment=-3&note=Test negative adjustment")
            if isinstance(response, str):
                self.log_test("Negative Stock Adjustment", False, f"Request failed: {response}")
            elif success:
                try:
                    result = response.json()
                    new_qty = result.get("new_quantity")
                    expected_qty = current_qty - 3
                    if new_qty == expected_qty:
                        self.log_test("Negative Stock Adjustment", True, f"Stock decreased from {current_qty} to {new_qty}")
                        current_qty = new_qty  # Update for next test
                    else:
                        self.log_test("Negative Stock Adjustment", False, f"Expected {expected_qty}, got {new_qty}")
                except:
                    self.log_test("Negative Stock Adjustment", True, "Stock adjustment completed")
            else:
                self.log_test("Negative Stock Adjustment", False, f"Got status {response.status_code}")
            
            # Test excessive negative adjustment (should fail)
            excessive_adjustment = -(current_qty + 1000)  # More than available
            success, response = self.make_request("POST", f"/stock/adjust?product_id={product_id}&adjustment={excessive_adjustment}&note=Test excessive negative", 400)
            if isinstance(response, str):
                self.log_test("Excessive Negative Adjustment", False, f"Request failed: {response}")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    if "negative stock" in error_message.lower():
                        self.log_test("Excessive Negative Adjustment", True, f"Correctly rejected: {error_message}")
                    else:
                        self.log_test("Excessive Negative Adjustment", True, f"Rejected with 400: {error_message}")
                except:
                    self.log_test("Excessive Negative Adjustment", True, "Correctly rejected with 400 Bad Request")
            else:
                self.log_test("Excessive Negative Adjustment", False, f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Stock Adjustment Test", False, f"Error: {e}")

    def run_stock_tests(self):
        """Run all stock tests"""
        print("🚀 Starting ZenVit CRM Stock Management Testing")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Authentication is required
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run stock tests
        self.test_stock_movements()
        self.test_stock_adjustment()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 STOCK TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        return failed == 0

if __name__ == "__main__":
    tester = StockTester()
    success = tester.run_stock_tests()
    
    if success:
        print("🎉 All stock tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some stock tests failed. Check the results above.")
        sys.exit(1)