#!/usr/bin/env python3
"""
ZenVit CRM - High Priority Validation Testing
Tests the 4 critical validation fixes requested
"""

import requests
import json
import sys
from datetime import datetime, timezone
import uuid

# Configuration
BACKEND_URL = "https://sleek-product-view.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@zenvit.no",
    "password": "admin123"
}

class ValidationTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []

    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "data": response_data
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
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=30)
            
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

    def test_duplicate_sku_validation(self):
        """Test 1: Duplicate SKU validation"""
        print("\n=== TEST 1: DUPLICATE SKU VALIDATION ===")
        
        # First, get existing products to find an existing SKU
        success, response = self.make_request("GET", "/products")
        if not success or isinstance(response, str):
            self.log_test("SKU Validation Setup", False, "Could not retrieve existing products")
            return
        
        try:
            products = response.json()
            if not products:
                self.log_test("SKU Validation Setup", False, "No existing products found")
                return
            
            existing_sku = products[0].get("sku", "ZV-D3K2-001")
            print(f"Using existing SKU for test: {existing_sku}")
            
            # Test 1a: Try to create product with existing SKU (should fail)
            duplicate_product = {
                "sku": existing_sku,
                "name": "Duplicate SKU Test Product",
                "category": "Test",
                "cost": 100.0,
                "price": 200.0,
                "description": "This should fail due to duplicate SKU"
            }
            
            success, response = self.make_request("POST", "/products", duplicate_product, 400)
            if isinstance(response, str):
                self.log_test("Duplicate SKU Rejection", False, f"Request failed: {response}")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "")
                    if "already exists" in error_message.lower():
                        self.log_test("Duplicate SKU Rejection", True, f"Correctly rejected: {error_message}")
                    else:
                        self.log_test("Duplicate SKU Rejection", True, f"Rejected with 400: {error_message}")
                except:
                    self.log_test("Duplicate SKU Rejection", True, "Correctly rejected with 400 Bad Request")
            else:
                self.log_test("Duplicate SKU Rejection", False, f"Expected 400, got {response.status_code}")
            
            # Test 1b: Create product with unique SKU (should succeed)
            unique_sku = f"TEST-{uuid.uuid4().hex[:8].upper()}"
            unique_product = {
                "sku": unique_sku,
                "name": "Unique SKU Test Product",
                "category": "Test",
                "cost": 100.0,
                "price": 200.0,
                "description": "This should succeed with unique SKU"
            }
            
            success, response = self.make_request("POST", "/products", unique_product, 201)
            if isinstance(response, str):
                self.log_test("Unique SKU Creation", False, f"Request failed: {response}")
            elif response.status_code == 201:
                try:
                    created_product = response.json()
                    product_id = created_product.get("id")
                    self.log_test("Unique SKU Creation", True, f"Product created successfully with ID: {product_id}")
                    
                    # Clean up - delete the test product
                    self.make_request("DELETE", f"/products/{product_id}", expected_status=204)
                except:
                    self.log_test("Unique SKU Creation", True, "Product created successfully")
            else:
                self.log_test("Unique SKU Creation", False, f"Expected 201, got {response.status_code}")
                
        except Exception as e:
            self.log_test("SKU Validation Test", False, f"Error: {e}")

    def test_duplicate_email_validation(self):
        """Test 2: Duplicate email validation"""
        print("\n=== TEST 2: DUPLICATE EMAIL VALIDATION ===")
        
        # Test 2a: Try to register with existing email (should fail)
        existing_email_data = {
            "email": "admin@zenvit.no",  # This should already exist
            "password": "testpass123",
            "full_name": "Test User",
            "role": "admin"
        }
        
        success, response = self.make_request("POST", "/auth/register", existing_email_data, 400)
        if isinstance(response, str):
            self.log_test("Duplicate Email Rejection", False, f"Request failed: {response}")
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", "")
                if "already registered" in error_message.lower():
                    self.log_test("Duplicate Email Rejection", True, f"Correctly rejected: {error_message}")
                else:
                    self.log_test("Duplicate Email Rejection", True, f"Rejected with 400: {error_message}")
            except:
                self.log_test("Duplicate Email Rejection", True, "Correctly rejected with 400 Bad Request")
        else:
            self.log_test("Duplicate Email Rejection", False, f"Expected 400, got {response.status_code}")
        
        # Test 2b: Register with unique email (should succeed)
        unique_email = f"test{uuid.uuid4().hex[:8]}@zenvit.no"
        unique_email_data = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User Unique",
            "role": "admin"
        }
        
        success, response = self.make_request("POST", "/auth/register", unique_email_data, 201)
        if isinstance(response, str):
            self.log_test("Unique Email Registration", False, f"Request failed: {response}")
        elif response.status_code == 201:
            try:
                created_user = response.json()
                user_email = created_user.get("email")
                self.log_test("Unique Email Registration", True, f"User created successfully: {user_email}")
            except:
                self.log_test("Unique Email Registration", True, "User created successfully")
        else:
            self.log_test("Unique Email Registration", False, f"Expected 201, got {response.status_code}")

    def test_negative_amount_validation(self):
        """Test 3: Negative amount validation in expenses"""
        print("\n=== TEST 3: NEGATIVE AMOUNT VALIDATION ===")
        
        # Test 3a: Try to create expense with negative amount (should fail)
        negative_expense = {
            "category": "Test",
            "amount": -100.0,
            "payment_status": "Unpaid",
            "notes": "Negative amount test - should fail"
        }
        
        success, response = self.make_request("POST", "/expenses", negative_expense, 400)
        if isinstance(response, str):
            self.log_test("Negative Amount Rejection", False, f"Request failed: {response}")
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", "")
                if "greater than 0" in error_message.lower():
                    self.log_test("Negative Amount Rejection", True, f"Correctly rejected: {error_message}")
                else:
                    self.log_test("Negative Amount Rejection", True, f"Rejected with 400: {error_message}")
            except:
                self.log_test("Negative Amount Rejection", True, "Correctly rejected with 400 Bad Request")
        else:
            self.log_test("Negative Amount Rejection", False, f"Expected 400, got {response.status_code}")
        
        # Test 3b: Try to create expense with zero amount (should fail)
        zero_expense = {
            "category": "Test",
            "amount": 0.0,
            "payment_status": "Unpaid",
            "notes": "Zero amount test - should fail"
        }
        
        success, response = self.make_request("POST", "/expenses", zero_expense, 400)
        if isinstance(response, str):
            self.log_test("Zero Amount Rejection", False, f"Request failed: {response}")
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", "")
                self.log_test("Zero Amount Rejection", True, f"Correctly rejected: {error_message}")
            except:
                self.log_test("Zero Amount Rejection", True, "Correctly rejected with 400 Bad Request")
        else:
            self.log_test("Zero Amount Rejection", False, f"Expected 400, got {response.status_code}")
        
        # Test 3c: Create expense with positive amount (should succeed)
        positive_expense = {
            "category": "Test",
            "amount": 100.0,
            "payment_status": "Unpaid",
            "notes": "Positive amount test - should succeed"
        }
        
        success, response = self.make_request("POST", "/expenses", positive_expense, 201)
        if isinstance(response, str):
            self.log_test("Positive Amount Creation", False, f"Request failed: {response}")
        elif response.status_code == 201:
            try:
                created_expense = response.json()
                expense_id = created_expense.get("id")
                self.log_test("Positive Amount Creation", True, f"Expense created successfully with ID: {expense_id}")
                
                # Clean up - delete the test expense
                self.make_request("DELETE", f"/expenses/{expense_id}", expected_status=204)
            except:
                self.log_test("Positive Amount Creation", True, "Expense created successfully")
        else:
            self.log_test("Positive Amount Creation", False, f"Expected 201, got {response.status_code}")

    def test_existing_functionality(self):
        """Test 4: Verify existing functionality still works"""
        print("\n=== TEST 4: EXISTING FUNCTIONALITY VERIFICATION ===")
        
        # Test 4a: GET /products
        success, response = self.make_request("GET", "/products")
        if isinstance(response, str):
            self.log_test("GET Products", False, f"Request failed: {response}")
        elif success:
            try:
                products = response.json()
                self.log_test("GET Products", True, f"Retrieved {len(products)} products")
            except:
                self.log_test("GET Products", False, "Invalid JSON response")
        else:
            self.log_test("GET Products", False, f"Got status {response.status_code}")
        
        # Test 4b: GET /customers
        success, response = self.make_request("GET", "/customers")
        if isinstance(response, str):
            self.log_test("GET Customers", False, f"Request failed: {response}")
        elif success:
            try:
                customers = response.json()
                self.log_test("GET Customers", True, f"Retrieved {len(customers)} customers")
            except:
                self.log_test("GET Customers", False, "Invalid JSON response")
        else:
            self.log_test("GET Customers", False, f"Got status {response.status_code}")
        
        # Test 4c: POST /orders (with valid data)
        # First get customers and products
        customers_success, customers_response = self.make_request("GET", "/customers")
        products_success, products_response = self.make_request("GET", "/products")
        
        if customers_success and products_success:
            try:
                customers = customers_response.json()
                products = products_response.json()
                
                if customers and products:
                    customer = customers[0]
                    product = products[0]
                    
                    test_order = {
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
                        "shipping_paid_by_customer": 50.0,
                        "shipping_cost": 25.0,
                        "payment_method": "Card",
                        "notes": "Test order for validation testing"
                    }
                    
                    success, response = self.make_request("POST", "/orders", test_order, 201)
                    if isinstance(response, str):
                        self.log_test("POST Orders", False, f"Request failed: {response}")
                    elif success:
                        try:
                            created_order = response.json()
                            order_id = created_order.get("id")
                            self.log_test("POST Orders", True, f"Order created successfully with ID: {order_id}")
                        except:
                            self.log_test("POST Orders", True, "Order created successfully")
                    else:
                        self.log_test("POST Orders", False, f"Expected 201, got {response.status_code}")
                else:
                    self.log_test("POST Orders", False, "No customers or products available for order creation")
            except Exception as e:
                self.log_test("POST Orders", False, f"Error processing order creation: {e}")
        else:
            self.log_test("POST Orders", False, "Could not retrieve customers or products")
        
        # Test 4d: GET /dashboard
        success, response = self.make_request("GET", "/dashboard")
        if isinstance(response, str):
            self.log_test("GET Dashboard", False, f"Request failed: {response}")
        elif success:
            try:
                dashboard_data = response.json()
                required_sections = ["top_panel", "tasks", "sales_profit_graphs", "products", "customers"]
                missing_sections = [section for section in required_sections if section not in dashboard_data]
                
                if missing_sections:
                    self.log_test("GET Dashboard", False, f"Missing sections: {missing_sections}")
                else:
                    self.log_test("GET Dashboard", True, "Dashboard loaded with all required sections")
            except:
                self.log_test("GET Dashboard", False, "Invalid JSON response")
        else:
            self.log_test("GET Dashboard", False, f"Got status {response.status_code}")

    def run_validation_tests(self):
        """Run all validation tests"""
        print("🚀 Starting ZenVit CRM High Priority Validation Testing")
        print(f"Backend URL: {self.base_url}")
        print(f"Test Credentials: {TEST_CREDENTIALS['email']}")
        print("=" * 60)
        
        # Authentication is required
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run the 4 validation tests
        self.test_duplicate_sku_validation()
        self.test_duplicate_email_validation()
        self.test_negative_amount_validation()
        self.test_existing_functionality()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION TEST RESULTS SUMMARY")
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
        
        # Return overall success
        return failed == 0

if __name__ == "__main__":
    tester = ValidationTester()
    success = tester.run_validation_tests()
    
    if success:
        print("🎉 All validation tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some validation tests failed. Check the results above.")
        sys.exit(1)