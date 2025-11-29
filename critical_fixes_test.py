#!/usr/bin/env python3
"""
Critical Fixes Testing for ZenVit CRM Backend
Tests the specific BSON ObjectId fixes and Stock Adjustment API
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://crm-central-24.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@zenvit.no",
    "password": "admin123"
}

class CriticalFixesTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        self.created_order_id = None
        self.created_purchase_id = None

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
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if response_data and not success:
            print(f"    Response: {response_data}")

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
                print("❌ Authentication failed: Invalid JSON response")
                return False
        else:
            print(f"❌ Authentication failed: Status {response.status_code}")
            return False

    def get_first_customer(self):
        """Get first customer for testing"""
        success, response = self.make_request("GET", "/customers")
        if success and isinstance(response, requests.Response):
            try:
                customers = response.json()
                if customers:
                    return customers[0]
            except:
                pass
        return None

    def get_first_product(self):
        """Get first product for testing"""
        success, response = self.make_request("GET", "/products")
        if success and isinstance(response, requests.Response):
            try:
                products = response.json()
                if products:
                    return products[0]
            except:
                pass
        return None

    def get_first_supplier(self):
        """Get first supplier for testing"""
        success, response = self.make_request("GET", "/suppliers")
        if success and isinstance(response, requests.Response):
            try:
                suppliers = response.json()
                if suppliers:
                    return suppliers[0]
            except:
                pass
        return None

    def get_product_stock(self, product_id):
        """Get current stock for a product"""
        success, response = self.make_request("GET", "/stock")
        if success and isinstance(response, requests.Response):
            try:
                stock_items = response.json()
                for item in stock_items:
                    if item.get("product_id") == product_id:
                        return item.get("quantity", 0)
            except:
                pass
        return 0

    def test_order_creation_fix(self):
        """Test 1: Order creation (BSON ObjectId fix)"""
        print("\n=== TEST 1: ORDER CREATION (BSON ObjectId Fix) ===")
        
        # Get required data
        customer = self.get_first_customer()
        product = self.get_first_product()
        
        if not customer or not product:
            self.log_test("Order Creation - Data Setup", False, "Could not get customer or product data")
            return False
        
        print(f"Using customer: {customer.get('name', 'Unknown')}")
        print(f"Using product: {product.get('name', 'Unknown')}")
        
        # Get initial stock
        initial_stock = self.get_product_stock(product["id"])
        print(f"Initial stock for {product.get('name', 'Unknown')}: {initial_stock}")
        
        # Create order
        order_data = {
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                    "sale_price": product.get("price", 299.0),
                    "discount": 0
                }
            ],
            "channel": "Direct",
            "shipping_paid_by_customer": 99,
            "shipping_cost": 50,
            "payment_method": "Card",
            "notes": "Test order for BSON ObjectId fix verification"
        }
        
        success, response = self.make_request("POST", "/orders", order_data, 201)
        
        if isinstance(response, str):
            self.log_test("Order Creation", False, f"Request failed: {response}")
            return False
        elif success:
            try:
                created_order = response.json()
                self.created_order_id = created_order.get("id")
                order_total = created_order.get("order_total", 0)
                profit = created_order.get("profit", 0)
                customer_name = created_order.get("customer_name", "Unknown")
                
                self.log_test("Order Creation", True, 
                    f"Order created successfully - ID: {self.created_order_id[:8]}..., "
                    f"Customer: {customer_name}, Total: {order_total} kr, Profit: {profit} kr")
                
                # Verify stock reduction
                new_stock = self.get_product_stock(product["id"])
                expected_stock = initial_stock - 2
                
                if new_stock == expected_stock:
                    self.log_test("Stock Reduction Verification", True, 
                        f"Stock correctly reduced from {initial_stock} to {new_stock}")
                else:
                    self.log_test("Stock Reduction Verification", False, 
                        f"Stock not reduced correctly. Expected: {expected_stock}, Got: {new_stock}")
                
                return True
                
            except Exception as e:
                self.log_test("Order Creation", False, f"JSON parsing error: {e}")
                return False
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", f"Status {response.status_code}")
            except:
                error_msg = f"Status {response.status_code}"
            
            self.log_test("Order Creation", False, f"Failed with {error_msg}")
            return False

    def test_purchase_creation_fix(self):
        """Test 2: Purchase creation (BSON ObjectId fix)"""
        print("\n=== TEST 2: PURCHASE CREATION (BSON ObjectId Fix) ===")
        
        # Get required data
        supplier = self.get_first_supplier()
        product = self.get_first_product()
        
        if not supplier or not product:
            self.log_test("Purchase Creation - Data Setup", False, "Could not get supplier or product data")
            return False
        
        print(f"Using supplier: {supplier.get('name', 'Unknown')}")
        print(f"Using product: {product.get('name', 'Unknown')}")
        
        # Create purchase
        purchase_data = {
            "supplier_id": supplier["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 10
                }
            ],
            "notes": "Test purchase for BSON ObjectId fix verification"
        }
        
        success, response = self.make_request("POST", "/purchases", purchase_data, 201)
        
        if isinstance(response, str):
            self.log_test("Purchase Creation", False, f"Request failed: {response}")
            return False
        elif success:
            try:
                created_purchase = response.json()
                self.created_purchase_id = created_purchase.get("id")
                total_amount = created_purchase.get("total_amount", 0)
                supplier_name = created_purchase.get("supplier_name", "Unknown")
                
                self.log_test("Purchase Creation", True, 
                    f"Purchase created successfully - ID: {self.created_purchase_id[:8]}..., "
                    f"Supplier: {supplier_name}, Total: {total_amount} kr")
                
                return True
                
            except Exception as e:
                self.log_test("Purchase Creation", False, f"JSON parsing error: {e}")
                return False
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", f"Status {response.status_code}")
            except:
                error_msg = f"Status {response.status_code}"
            
            self.log_test("Purchase Creation", False, f"Failed with {error_msg}")
            return False

    def test_purchase_receiving(self):
        """Test 3: Purchase receiving"""
        print("\n=== TEST 3: PURCHASE RECEIVING ===")
        
        if not self.created_purchase_id:
            self.log_test("Purchase Receiving", False, "No purchase ID available (previous test failed)")
            return False
        
        # Get product for stock verification
        product = self.get_first_product()
        if not product:
            self.log_test("Purchase Receiving - Data Setup", False, "Could not get product data")
            return False
        
        # Get stock before receiving
        stock_before = self.get_product_stock(product["id"])
        print(f"Stock before receiving: {stock_before}")
        
        # Receive purchase
        success, response = self.make_request("PUT", f"/purchases/{self.created_purchase_id}/receive")
        
        if isinstance(response, str):
            self.log_test("Purchase Receiving", False, f"Request failed: {response}")
            return False
        elif success:
            try:
                received_purchase = response.json()
                status = received_purchase.get("status", "Unknown")
                
                if status == "Received":
                    self.log_test("Purchase Status Update", True, "Purchase status changed to 'Received'")
                    
                    # Verify stock increase
                    stock_after = self.get_product_stock(product["id"])
                    expected_stock = stock_before + 10
                    
                    if stock_after == expected_stock:
                        self.log_test("Stock Increase Verification", True, 
                            f"Stock correctly increased from {stock_before} to {stock_after}")
                    else:
                        self.log_test("Stock Increase Verification", False, 
                            f"Stock not increased correctly. Expected: {expected_stock}, Got: {stock_after}")
                    
                    return True
                else:
                    self.log_test("Purchase Status Update", False, f"Status not updated correctly. Got: {status}")
                    return False
                
            except Exception as e:
                self.log_test("Purchase Receiving", False, f"JSON parsing error: {e}")
                return False
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", f"Status {response.status_code}")
            except:
                error_msg = f"Status {response.status_code}"
            
            self.log_test("Purchase Receiving", False, f"Failed with {error_msg}")
            return False

    def test_stock_movements_api(self):
        """Test 4: Stock Movements API"""
        print("\n=== TEST 4: STOCK MOVEMENTS API ===")
        
        # Test GET /api/stock/movements
        success, response = self.make_request("GET", "/stock/movements")
        
        if isinstance(response, str):
            self.log_test("Stock Movements GET", False, f"Request failed: {response}")
            return False
        elif success:
            try:
                movements = response.json()
                self.log_test("Stock Movements GET", True, 
                    f"Retrieved {len(movements)} stock movements (not 405 Method Not Allowed)")
                return True
            except Exception as e:
                self.log_test("Stock Movements GET", False, f"JSON parsing error: {e}")
                return False
        else:
            if response.status_code == 405:
                self.log_test("Stock Movements GET", False, "Returns 405 Method Not Allowed - endpoint missing")
            else:
                self.log_test("Stock Movements GET", False, f"Failed with status {response.status_code}")
            return False

    def test_stock_adjustment_api(self):
        """Test 5: Stock Adjustment API"""
        print("\n=== TEST 5: STOCK ADJUSTMENT API ===")
        
        # Get product for testing
        product = self.get_first_product()
        if not product:
            self.log_test("Stock Adjustment - Data Setup", False, "Could not get product data")
            return False
        
        product_id = product["id"]
        product_name = product.get("name", "Unknown")
        
        # Get initial stock
        initial_stock = self.get_product_stock(product_id)
        print(f"Initial stock for {product_name}: {initial_stock}")
        
        # Test positive adjustment (+5) - using query parameters
        endpoint = f"/stock/adjust?product_id={product_id}&adjustment=5&note=Test adjustment"
        
        success, response = self.make_request("POST", endpoint)
        
        if isinstance(response, str):
            self.log_test("Stock Adjustment POST", False, f"Request failed: {response}")
            return False
        elif success:
            try:
                result = response.json()
                previous_qty = result.get("previous_quantity")
                new_qty = result.get("new_quantity")
                
                if previous_qty == initial_stock and new_qty == initial_stock + 5:
                    self.log_test("Stock Adjustment POST", True, 
                        f"Stock adjusted correctly from {previous_qty} to {new_qty}")
                    
                    # Verify actual stock change
                    current_stock = self.get_product_stock(product_id)
                    if current_stock == new_qty:
                        self.log_test("Stock Adjustment Verification", True, 
                            f"Stock correctly updated to {current_stock}")
                        return True
                    else:
                        self.log_test("Stock Adjustment Verification", False, 
                            f"Stock not updated correctly. Expected: {new_qty}, Got: {current_stock}")
                        return False
                else:
                    self.log_test("Stock Adjustment POST", False, 
                        f"Incorrect quantities. Previous: {previous_qty}, New: {new_qty}")
                    return False
                
            except Exception as e:
                self.log_test("Stock Adjustment POST", False, f"JSON parsing error: {e}")
                return False
        else:
            if response.status_code == 405:
                self.log_test("Stock Adjustment POST", False, "Returns 405 Method Not Allowed - endpoint missing")
            else:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", f"Status {response.status_code}")
                except:
                    error_msg = f"Status {response.status_code}"
                
                self.log_test("Stock Adjustment POST", False, f"Failed with {error_msg}")
            return False

    def test_negative_stock_adjustment(self):
        """Test 6: Negative stock adjustment"""
        print("\n=== TEST 6: NEGATIVE STOCK ADJUSTMENT ===")
        
        # Get product for testing
        product = self.get_first_product()
        if not product:
            self.log_test("Negative Stock Adjustment - Data Setup", False, "Could not get product data")
            return False
        
        product_id = product["id"]
        product_name = product.get("name", "Unknown")
        
        # Get current stock
        current_stock = self.get_product_stock(product_id)
        print(f"Current stock for {product_name}: {current_stock}")
        
        # Test negative adjustment (-3)
        adjustment_data = {
            "product_id": product_id,
            "adjustment": -3,
            "note": "Test negative adjustment"
        }
        
        success, response = self.make_request("POST", "/stock/adjust", adjustment_data)
        
        if isinstance(response, str):
            self.log_test("Negative Stock Adjustment", False, f"Request failed: {response}")
            return False
        elif success:
            try:
                result = response.json()
                previous_qty = result.get("previous_quantity")
                new_qty = result.get("new_quantity")
                
                if previous_qty == current_stock and new_qty == current_stock - 3:
                    self.log_test("Negative Stock Adjustment", True, 
                        f"Negative adjustment works correctly from {previous_qty} to {new_qty}")
                    return True
                else:
                    self.log_test("Negative Stock Adjustment", False, 
                        f"Incorrect quantities. Previous: {previous_qty}, New: {new_qty}")
                    return False
                
            except Exception as e:
                self.log_test("Negative Stock Adjustment", False, f"JSON parsing error: {e}")
                return False
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", f"Status {response.status_code}")
            except:
                error_msg = f"Status {response.status_code}"
            
            self.log_test("Negative Stock Adjustment", False, f"Failed with {error_msg}")
            return False

    def test_excessive_negative_adjustment(self):
        """Test 7: Excessive negative adjustment (should return 400)"""
        print("\n=== TEST 7: EXCESSIVE NEGATIVE ADJUSTMENT ===")
        
        # Get product for testing
        product = self.get_first_product()
        if not product:
            self.log_test("Excessive Negative Adjustment - Data Setup", False, "Could not get product data")
            return False
        
        product_id = product["id"]
        product_name = product.get("name", "Unknown")
        
        # Get current stock
        current_stock = self.get_product_stock(product_id)
        print(f"Current stock for {product_name}: {current_stock}")
        
        # Test excessive negative adjustment (-999999)
        adjustment_data = {
            "product_id": product_id,
            "adjustment": -999999,
            "note": "Test excessive negative adjustment"
        }
        
        success, response = self.make_request("POST", "/stock/adjust", adjustment_data, 400)
        
        if isinstance(response, str):
            self.log_test("Excessive Negative Adjustment", False, f"Request failed: {response}")
            return False
        elif success:
            self.log_test("Excessive Negative Adjustment", True, 
                "Correctly returned 400 Bad Request for excessive negative adjustment")
            return True
        else:
            if response.status_code == 500:
                self.log_test("Excessive Negative Adjustment", False, 
                    "Returns 500 Internal Server Error instead of 400 Bad Request")
            else:
                self.log_test("Excessive Negative Adjustment", False, 
                    f"Unexpected status code: {response.status_code}")
            return False

    def run_critical_tests(self):
        """Run all critical fix tests"""
        print("🚀 Starting ZenVit CRM Critical Fixes Testing")
        print(f"Backend URL: {self.base_url}")
        print(f"Test Credentials: {TEST_CREDENTIALS['email']}")
        print("=" * 60)
        
        # Authentication is required
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run critical tests in order
        test_results = []
        
        test_results.append(self.test_order_creation_fix())
        test_results.append(self.test_purchase_creation_fix())
        test_results.append(self.test_purchase_receiving())
        test_results.append(self.test_stock_movements_api())
        test_results.append(self.test_stock_adjustment_api())
        test_results.append(self.test_negative_stock_adjustment())
        test_results.append(self.test_excessive_negative_adjustment())
        
        # Print summary
        self.print_summary()
        
        # Return overall success
        return all(test_results)

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 CRITICAL FIXES TEST SUMMARY")
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
        
        # Determine if critical fixes are successful
        critical_tests = [
            "Order Creation",
            "Purchase Creation", 
            "Stock Adjustment POST"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if any(ct in result["test"] for ct in critical_tests) 
                            and "✅ PASS" in result["status"])
        
        if critical_passed >= 2:  # At least 2 of 3 critical fixes working
            print("✅ CRITICAL FIXES STATUS: SUCCESSFUL")
            print("The BSON ObjectId fixes appear to be working!")
        else:
            print("❌ CRITICAL FIXES STATUS: FAILED")
            print("The BSON ObjectId fixes still need work.")

if __name__ == "__main__":
    tester = CriticalFixesTester()
    success = tester.run_critical_tests()
    
    if success:
        print("🎉 All critical tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some critical tests failed. Check the results above.")
        sys.exit(1)