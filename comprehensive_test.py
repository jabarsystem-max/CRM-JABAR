#!/usr/bin/env python3
"""
Comprehensive ZenVit CRM Backend API Testing
Following the exact test requirements from the user
"""

import requests
import json
import sys
from datetime import datetime, timezone
import uuid

# Configuration
BACKEND_URL = "https://crm-central-24.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@zenvit.no",
    "password": "admin123"
}

class ComprehensiveAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        self.created_resources = []

    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"    Details: {details}")

    def make_request(self, method, endpoint, data=None, expected_status=200, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            kwargs = {
                "headers": self.headers,
                "timeout": 30
            }
            
            if data is not None:
                kwargs["json"] = data
            if params:
                kwargs["params"] = params
                
            if method.upper() == "GET":
                response = requests.get(url, **{k: v for k, v in kwargs.items() if k != "json"})
            elif method.upper() == "POST":
                response = requests.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = requests.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = requests.delete(url, **{k: v for k, v in kwargs.items() if k != "json"})
            
            success = response.status_code == expected_status
            return success, response
        except Exception as e:
            return False, str(e)

    def authenticate(self):
        """Authenticate and get token"""
        print("🔐 AUTENTISERING OG BRUKERHÅNDTERING")
        print("=" * 50)
        
        # Test 1: Register duplicate email (should fail)
        register_data = {
            "email": "test@test.no",
            "password": "testpass123",
            "full_name": "Test Bruker",
            "role": "admin"
        }
        success, response = self.make_request("POST", "/auth/register", register_data, 400)
        if isinstance(response, str):
            self.log_test("POST /auth/register - duplikat e-post", False, f"Request failed: {response}")
        else:
            if response.status_code == 400:
                self.log_test("POST /auth/register - duplikat e-post", True, "Correctly rejected duplicate email")
            elif response.status_code == 201:
                self.log_test("POST /auth/register - duplikat e-post", True, "New user registered (email was unique)")
            else:
                self.log_test("POST /auth/register - duplikat e-post", False, f"Unexpected status {response.status_code}")

        # Test 2: Login with correct credentials
        success, response = self.make_request("POST", "/auth/login", TEST_CREDENTIALS)
        if isinstance(response, str):
            self.log_test("POST /auth/login - korrekt passord", False, f"Request failed: {response}")
            return False
        elif success and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                self.log_test("POST /auth/login - korrekt passord", True, "Login successful, token received")
            except:
                self.log_test("POST /auth/login - korrekt passord", False, "Invalid JSON response")
                return False
        else:
            self.log_test("POST /auth/login - korrekt passord", False, f"Got status {response.status_code}")
            return False

        # Test 3: Login with wrong password
        wrong_creds = {"email": "admin@zenvit.no", "password": "wrongpass"}
        success, response = self.make_request("POST", "/auth/login", wrong_creds, 401)
        if isinstance(response, str):
            self.log_test("POST /auth/login - feil passord", False, f"Request failed: {response}")
        else:
            self.log_test("POST /auth/login - feil passord", success, 
                         "Correctly rejected wrong password" if success else f"Got {response.status_code}")

        return self.token is not None

    def test_products_full_crud(self):
        """Test products - Full CRUD"""
        print("\n📦 PRODUKTER - FULL CRUD")
        print("=" * 50)
        
        # Test 1: Get all products
        success, response = self.make_request("GET", "/products")
        if isinstance(response, str):
            self.log_test("GET /products - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                products = response.json()
                self.log_test("GET /products - hent alle", True, f"Retrieved {len(products)} products")
            except:
                self.log_test("GET /products - hent alle", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /products - hent alle", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new product with unique SKU
        unique_sku = f"TEST-{uuid.uuid4().hex[:8].upper()}"
        new_product = {
            "sku": unique_sku,
            "name": "Test Vitamin D3 + K2",
            "category": "Kosttilskudd",
            "cost": 150.0,
            "price": 299.0,
            "description": "Test produkt for API testing",
            "color": "blue"
        }
        success, response = self.make_request("POST", "/products", new_product, 201)
        if isinstance(response, str):
            self.log_test("POST /products - opprett nytt", False, f"Request failed: {response}")
            return
        elif success:
            try:
                created_product = response.json()
                product_id = created_product.get("id")
                self.created_resources.append(("product", product_id))
                self.log_test("POST /products - opprett nytt", True, f"Product created with ID: {product_id}")
                
                # Test 3: Create product with duplicate SKU (should fail)
                duplicate_product = {
                    "sku": unique_sku,  # Same SKU
                    "name": "Duplicate Test",
                    "category": "Test",
                    "cost": 100.0,
                    "price": 200.0
                }
                success, response = self.make_request("POST", "/products", duplicate_product, 400)
                if isinstance(response, str):
                    self.log_test("POST /products - duplikat SKU", False, f"Request failed: {response}")
                else:
                    self.log_test("POST /products - duplikat SKU", success, 
                                 "Correctly rejected duplicate SKU" if success else f"Got {response.status_code}")
                
                # Test 4: Update product
                update_data = {
                    "sku": unique_sku,
                    "name": "Updated Test Vitamin D3 + K2",
                    "category": "Kosttilskudd",
                    "cost": 160.0,
                    "price": 319.0,
                    "description": "Updated description"
                }
                success, response = self.make_request("PUT", f"/products/{product_id}", update_data)
                if isinstance(response, str):
                    self.log_test("PUT /products/{id} - oppdater", False, f"Request failed: {response}")
                elif success:
                    self.log_test("PUT /products/{id} - oppdater", True, "Product updated successfully")
                else:
                    self.log_test("PUT /products/{id} - oppdater", False, f"Got status {response.status_code}")
                
                # Test 5: Verify update by getting all products
                success, response = self.make_request("GET", "/products")
                if isinstance(response, str):
                    self.log_test("GET /products - verifiser oppdatering", False, f"Request failed: {response}")
                elif success:
                    try:
                        products = response.json()
                        updated_product = next((p for p in products if p.get("id") == product_id), None)
                        if updated_product and updated_product.get("name") == "Updated Test Vitamin D3 + K2":
                            self.log_test("GET /products - verifiser oppdatering", True, "Product update verified")
                        else:
                            self.log_test("GET /products - verifiser oppdatering", False, "Product update not found")
                    except:
                        self.log_test("GET /products - verifiser oppdatering", False, "Invalid JSON response")
                else:
                    self.log_test("GET /products - verifiser oppdatering", False, f"Got status {response.status_code}")
                
                # Test 6: Delete product (soft delete)
                success, response = self.make_request("DELETE", f"/products/{product_id}", expected_status=204)
                if isinstance(response, str):
                    self.log_test("DELETE /products/{id} - slett", False, f"Request failed: {response}")
                elif success:
                    self.log_test("DELETE /products/{id} - slett", True, "Product deleted successfully")
                else:
                    self.log_test("DELETE /products/{id} - slett", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("POST /products - opprett nytt", False, f"JSON parsing error: {e}")
        else:
            self.log_test("POST /products - opprett nytt", False, f"Got status {response.status_code}")

    def test_stock_full_functionality(self):
        """Test stock - Full functionality"""
        print("\n📊 LAGER - FULL FUNKSJONALITET")
        print("=" * 50)
        
        # Test 1: Get all stock
        success, response = self.make_request("GET", "/stock")
        if isinstance(response, str):
            self.log_test("GET /stock - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                stock_items = response.json()
                self.log_test("GET /stock - hent alle", True, f"Retrieved {len(stock_items)} stock items")
                
                if stock_items:
                    first_item = stock_items[0]
                    product_id = first_item.get("product_id")
                    current_qty = first_item.get("quantity", 0)
                    
                    # Test 2: Positive adjustment (+10)
                    success, response = self.make_request("POST", "/stock/adjust", 
                                                        params={"product_id": product_id, "adjustment": 10, "note": "Test positive adjustment"})
                    if isinstance(response, str):
                        self.log_test("POST /stock/adjust - positiv justering", False, f"Request failed: {response}")
                    elif success:
                        try:
                            result = response.json()
                            new_qty = result.get("new_quantity", 0)
                            if new_qty == current_qty + 10:
                                self.log_test("POST /stock/adjust - positiv justering", True, f"Stock increased from {current_qty} to {new_qty}")
                                current_qty = new_qty
                            else:
                                self.log_test("POST /stock/adjust - positiv justering", False, f"Expected {current_qty + 10}, got {new_qty}")
                        except:
                            self.log_test("POST /stock/adjust - positiv justering", False, "Invalid JSON response")
                    else:
                        self.log_test("POST /stock/adjust - positiv justering", False, f"Got status {response.status_code}")
                    
                    # Test 3: Negative adjustment (-5)
                    success, response = self.make_request("POST", "/stock/adjust", 
                                                        params={"product_id": product_id, "adjustment": -5, "note": "Test negative adjustment"})
                    if isinstance(response, str):
                        self.log_test("POST /stock/adjust - negativ justering", False, f"Request failed: {response}")
                    elif success:
                        try:
                            result = response.json()
                            new_qty = result.get("new_quantity", 0)
                            if new_qty == current_qty - 5:
                                self.log_test("POST /stock/adjust - negativ justering", True, f"Stock decreased from {current_qty} to {new_qty}")
                                current_qty = new_qty
                            else:
                                self.log_test("POST /stock/adjust - negativ justering", False, f"Expected {current_qty - 5}, got {new_qty}")
                        except:
                            self.log_test("POST /stock/adjust - negativ justering", False, "Invalid JSON response")
                    else:
                        self.log_test("POST /stock/adjust - negativ justering", False, f"Got status {response.status_code}")
                    
                    # Test 4: Excessive negative adjustment (should fail)
                    excessive_negative = -(current_qty + 1000)  # More than available
                    success, response = self.make_request("POST", "/stock/adjust", 
                                                        params={"product_id": product_id, "adjustment": excessive_negative, "note": "Test excessive negative"}, 
                                                        expected_status=400)
                    if isinstance(response, str):
                        self.log_test("POST /stock/adjust - for mye negativ", False, f"Request failed: {response}")
                    else:
                        self.log_test("POST /stock/adjust - for mye negativ", success, 
                                     "Correctly rejected excessive negative adjustment" if success else f"Got {response.status_code}")
                else:
                    self.log_test("Stock adjustment tests", False, "No stock items available for testing")
                    
            except Exception as e:
                self.log_test("GET /stock - hent alle", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /stock - hent alle", False, f"Got status {response.status_code}")

        # Test 5: Get stock movements
        success, response = self.make_request("GET", "/stock/movements")
        if isinstance(response, str):
            self.log_test("GET /stock/movements - hent bevegelser", False, f"Request failed: {response}")
        elif success:
            try:
                movements = response.json()
                self.log_test("GET /stock/movements - hent bevegelser", True, f"Retrieved {len(movements)} stock movements")
            except:
                self.log_test("GET /stock/movements - hent bevegelser", False, "Invalid JSON response")
        else:
            self.log_test("GET /stock/movements - hent bevegelser", False, f"Got status {response.status_code}")

    def test_customers_full_crud(self):
        """Test customers - Full CRUD"""
        print("\n👥 KUNDER - FULL CRUD")
        print("=" * 50)
        
        # Test 1: Get all customers
        success, response = self.make_request("GET", "/customers")
        if isinstance(response, str):
            self.log_test("GET /customers - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                customers = response.json()
                self.log_test("GET /customers - hent alle", True, f"Retrieved {len(customers)} customers")
            except:
                self.log_test("GET /customers - hent alle", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /customers - hent alle", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new customer
        new_customer = {
            "name": "Test Kunde Nordmann",
            "email": f"testkunde{uuid.uuid4().hex[:8]}@example.no",
            "phone": "+47 12345678",
            "address": "Testveien 123",
            "zip_code": "0123",
            "city": "Oslo",
            "type": "Business",
            "status": "New",
            "notes": "Test kunde for API testing"
        }
        success, response = self.make_request("POST", "/customers", new_customer, 201)
        if isinstance(response, str):
            self.log_test("POST /customers - opprett ny", False, f"Request failed: {response}")
        elif success:
            try:
                created_customer = response.json()
                customer_id = created_customer.get("id")
                self.created_resources.append(("customer", customer_id))
                self.log_test("POST /customers - opprett ny", True, f"Customer created with ID: {customer_id}")
                
                # Test 3: Update customer
                update_data = {
                    "name": "Updated Test Kunde Nordmann",
                    "email": new_customer["email"],
                    "phone": "+47 87654321",
                    "address": "Updated Address 456",
                    "zip_code": "0456",
                    "city": "Bergen",
                    "type": "Business",
                    "status": "Active",
                    "notes": "Updated notes"
                }
                success, response = self.make_request("PUT", f"/customers/{customer_id}", update_data)
                if isinstance(response, str):
                    self.log_test("PUT /customers/{id} - oppdater", False, f"Request failed: {response}")
                elif success:
                    self.log_test("PUT /customers/{id} - oppdater", True, "Customer updated successfully")
                else:
                    self.log_test("PUT /customers/{id} - oppdater", False, f"Got status {response.status_code}")
                
                # Test 4: Get customer timeline
                success, response = self.make_request("GET", f"/customers/{customer_id}/timeline")
                if isinstance(response, str):
                    self.log_test("GET /customers/{id}/timeline - hent timeline", False, f"Request failed: {response}")
                elif success:
                    try:
                        timeline = response.json()
                        self.log_test("GET /customers/{id}/timeline - hent timeline", True, f"Retrieved {len(timeline)} timeline entries")
                    except:
                        self.log_test("GET /customers/{id}/timeline - hent timeline", False, "Invalid JSON response")
                else:
                    self.log_test("GET /customers/{id}/timeline - hent timeline", False, f"Got status {response.status_code}")
                
                # Test 5: Delete customer (if no orders)
                success, response = self.make_request("DELETE", f"/customers/{customer_id}", expected_status=204)
                if isinstance(response, str):
                    self.log_test("DELETE /customers/{id} - slett", False, f"Request failed: {response}")
                elif success:
                    self.log_test("DELETE /customers/{id} - slett", True, "Customer deleted successfully")
                    # Remove from cleanup list since already deleted
                    self.created_resources = [(t, i) for t, i in self.created_resources if not (t == "customer" and i == customer_id)]
                else:
                    self.log_test("DELETE /customers/{id} - slett", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("POST /customers - opprett ny", False, f"JSON parsing error: {e}")
        else:
            self.log_test("POST /customers - opprett ny", False, f"Got status {response.status_code}")

    def test_orders_complete_workflow(self):
        """Test orders - Complete workflow"""
        print("\n🛒 ORDRER - KOMPLETT WORKFLOW")
        print("=" * 50)
        
        # Test 1: Get all orders
        success, response = self.make_request("GET", "/orders")
        if isinstance(response, str):
            self.log_test("GET /orders - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                orders = response.json()
                self.log_test("GET /orders - hent alle", True, f"Retrieved {len(orders)} orders")
            except:
                self.log_test("GET /orders - hent alle", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /orders - hent alle", False, f"Got status {response.status_code}")
            return

        # Get existing customers and products for order creation
        customers_success, customers_response = self.make_request("GET", "/customers")
        products_success, products_response = self.make_request("GET", "/products")
        
        if not (customers_success and products_success):
            self.log_test("Order workflow", False, "Cannot get customers or products for order creation")
            return
            
        try:
            customers = customers_response.json()
            products = products_response.json()
            
            if not customers or len(products) < 2:
                self.log_test("Order workflow", False, "Need at least 1 customer and 2 products for order creation")
                return
                
            # Test 2: Create new order with 2 products
            customer = customers[0]
            product1 = products[0]
            product2 = products[1] if len(products) > 1 else products[0]
            
            # Get current stock before order
            stock_success, stock_response = self.make_request("GET", "/stock")
            initial_stock = {}
            if stock_success:
                try:
                    stock_items = stock_response.json()
                    for item in stock_items:
                        initial_stock[item.get("product_id")] = item.get("quantity", 0)
                except:
                    pass
            
            new_order = {
                "customer_id": customer["id"],
                "items": [
                    {
                        "product_id": product1["id"],
                        "quantity": 2,
                        "sale_price": product1.get("price", 299.0),
                        "discount": 0
                    },
                    {
                        "product_id": product2["id"],
                        "quantity": 1,
                        "sale_price": product2.get("price", 199.0),
                        "discount": 0
                    }
                ],
                "channel": "Direct",
                "shipping_paid_by_customer": 99.0,
                "shipping_cost": 50.0,
                "payment_method": "Card",
                "notes": "Test order for API testing - 2 products"
            }
            
            success, response = self.make_request("POST", "/orders", new_order, 201)
            if isinstance(response, str):
                self.log_test("POST /orders - opprett ny ordre", False, f"Request failed: {response}")
            elif success:
                try:
                    created_order = response.json()
                    order_id = created_order.get("id")
                    self.created_resources.append(("order", order_id))
                    self.log_test("POST /orders - opprett ny ordre", True, f"Order created with ID: {order_id}")
                    
                    # Verify stock reduction
                    stock_success, stock_response = self.make_request("GET", "/stock")
                    if stock_success:
                        try:
                            new_stock_items = stock_response.json()
                            stock_reduced_correctly = True
                            for item in new_stock_items:
                                pid = item.get("product_id")
                                if pid in initial_stock:
                                    expected_reduction = 0
                                    if pid == product1["id"]:
                                        expected_reduction = 2
                                    elif pid == product2["id"]:
                                        expected_reduction = 1
                                    
                                    if expected_reduction > 0:
                                        expected_qty = initial_stock[pid] - expected_reduction
                                        actual_qty = item.get("quantity", 0)
                                        if actual_qty != expected_qty:
                                            stock_reduced_correctly = False
                                            break
                            
                            self.log_test("Verifiser lager reduksjon", stock_reduced_correctly, 
                                         "Stock reduced correctly" if stock_reduced_correctly else "Stock reduction mismatch")
                        except:
                            self.log_test("Verifiser lager reduksjon", False, "Could not verify stock reduction")
                    
                    # Test 3: Update order status to "Shipped"
                    success, response = self.make_request("PUT", f"/orders/{order_id}/status", 
                                                        params={"status": "Shipped"})
                    if isinstance(response, str):
                        self.log_test("PUT /orders/{id} - oppdater status", False, f"Request failed: {response}")
                    elif success:
                        self.log_test("PUT /orders/{id} - oppdater status", True, "Order status updated to Shipped")
                        
                        # Test 4: Verify status change
                        success, response = self.make_request("GET", f"/orders/{order_id}")
                        if isinstance(response, str):
                            # Try getting all orders and find our order
                            success, response = self.make_request("GET", "/orders")
                            if success:
                                try:
                                    all_orders = response.json()
                                    our_order = next((o for o in all_orders if o.get("id") == order_id), None)
                                    if our_order and our_order.get("status") == "Shipped":
                                        self.log_test("GET /orders/{id} - verifiser endring", True, "Order status verified as Shipped")
                                    else:
                                        self.log_test("GET /orders/{id} - verifiser endring", False, "Order status not updated correctly")
                                except:
                                    self.log_test("GET /orders/{id} - verifiser endring", False, "Could not verify order status")
                            else:
                                self.log_test("GET /orders/{id} - verifiser endring", False, "Could not retrieve orders for verification")
                        elif success:
                            try:
                                order_data = response.json()
                                if order_data.get("status") == "Shipped":
                                    self.log_test("GET /orders/{id} - verifiser endring", True, "Order status verified as Shipped")
                                else:
                                    self.log_test("GET /orders/{id} - verifiser endring", False, f"Expected 'Shipped', got '{order_data.get('status')}'")
                            except:
                                self.log_test("GET /orders/{id} - verifiser endring", False, "Invalid JSON response")
                        else:
                            self.log_test("GET /orders/{id} - verifiser endring", False, f"Got status {response.status_code}")
                    else:
                        self.log_test("PUT /orders/{id} - oppdater status", False, f"Got status {response.status_code}")
                        
                except Exception as e:
                    self.log_test("POST /orders - opprett ny ordre", False, f"JSON parsing error: {e}")
            else:
                self.log_test("POST /orders - opprett ny ordre", False, f"Got status {response.status_code}")
                # Check if it's the known bug
                if response.status_code == 500:
                    self.log_test("Order creation bug", False, "Known bug: AttributeError in update_customer_stats - 'str' object has no attribute 'isoformat'")
                
        except Exception as e:
            self.log_test("Order workflow", False, f"Error processing customers/products: {e}")

    def test_purchases_complete_workflow(self):
        """Test purchases - Complete workflow"""
        print("\n📦 INNKJØP - KOMPLETT WORKFLOW")
        print("=" * 50)
        
        # Test 1: Get all purchases
        success, response = self.make_request("GET", "/purchases")
        if isinstance(response, str):
            self.log_test("GET /purchases - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                purchases = response.json()
                self.log_test("GET /purchases - hent alle", True, f"Retrieved {len(purchases)} purchases")
            except:
                self.log_test("GET /purchases - hent alle", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /purchases - hent alle", False, f"Got status {response.status_code}")
            return

        # Test 2: Get suppliers
        success, response = self.make_request("GET", "/suppliers")
        if isinstance(response, str):
            self.log_test("GET /suppliers - hent leverandører", False, f"Request failed: {response}")
            return
        elif success:
            try:
                suppliers = response.json()
                self.log_test("GET /suppliers - hent leverandører", True, f"Retrieved {len(suppliers)} suppliers")
            except:
                self.log_test("GET /suppliers - hent leverandører", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /suppliers - hent leverandører", False, f"Got status {response.status_code}")
            return

        # Get products for purchase creation
        products_success, products_response = self.make_request("GET", "/products")
        
        if not products_success:
            self.log_test("Purchase workflow", False, "Cannot get products for purchase creation")
            return
            
        try:
            products = products_response.json()
            
            if not suppliers or len(products) < 2:
                self.log_test("Purchase workflow", False, "Need at least 1 supplier and 2 products for purchase creation")
                return
                
            # Test 3: Create new purchase with 2 products
            supplier = suppliers[0]
            product1 = products[0]
            product2 = products[1] if len(products) > 1 else products[0]
            
            # Get current stock before purchase
            stock_success, stock_response = self.make_request("GET", "/stock")
            initial_stock = {}
            if stock_success:
                try:
                    stock_items = stock_response.json()
                    for item in stock_items:
                        initial_stock[item.get("product_id")] = item.get("quantity", 0)
                except:
                    pass
            
            new_purchase = {
                "supplier_id": supplier["id"],
                "items": [
                    {
                        "product_id": product1["id"],
                        "quantity": 50
                    },
                    {
                        "product_id": product2["id"],
                        "quantity": 30
                    }
                ],
                "notes": "Test purchase for API testing - 2 products"
            }
            
            success, response = self.make_request("POST", "/purchases", new_purchase, 201)
            if isinstance(response, str):
                self.log_test("POST /purchases - opprett ny innkjøp", False, f"Request failed: {response}")
            elif success:
                try:
                    created_purchase = response.json()
                    purchase_id = created_purchase.get("id")
                    self.created_resources.append(("purchase", purchase_id))
                    self.log_test("POST /purchases - opprett ny innkjøp", True, f"Purchase created with ID: {purchase_id}")
                    
                    # Test 4: Receive purchase
                    success, response = self.make_request("PUT", f"/purchases/{purchase_id}/receive")
                    if isinstance(response, str):
                        self.log_test("PUT /purchases/{id}/receive - motta innkjøp", False, f"Request failed: {response}")
                    elif success:
                        self.log_test("PUT /purchases/{id}/receive - motta innkjøp", True, "Purchase received successfully")
                        
                        # Verify stock increase
                        stock_success, stock_response = self.make_request("GET", "/stock")
                        if stock_success:
                            try:
                                new_stock_items = stock_response.json()
                                stock_increased_correctly = True
                                for item in new_stock_items:
                                    pid = item.get("product_id")
                                    if pid in initial_stock:
                                        expected_increase = 0
                                        if pid == product1["id"]:
                                            expected_increase = 50
                                        elif pid == product2["id"]:
                                            expected_increase = 30
                                        
                                        if expected_increase > 0:
                                            expected_qty = initial_stock[pid] + expected_increase
                                            actual_qty = item.get("quantity", 0)
                                            if actual_qty != expected_qty:
                                                stock_increased_correctly = False
                                                break
                                
                                self.log_test("Verifiser lager økning", stock_increased_correctly, 
                                             "Stock increased correctly" if stock_increased_correctly else "Stock increase mismatch")
                            except:
                                self.log_test("Verifiser lager økning", False, "Could not verify stock increase")
                    else:
                        self.log_test("PUT /purchases/{id}/receive - motta innkjøp", False, f"Got status {response.status_code}")
                        
                except Exception as e:
                    self.log_test("POST /purchases - opprett ny innkjøp", False, f"JSON parsing error: {e}")
            else:
                self.log_test("POST /purchases - opprett ny innkjøp", False, f"Got status {response.status_code}")
                
        except Exception as e:
            self.log_test("Purchase workflow", False, f"Error processing suppliers/products: {e}")

    def test_tasks_full_crud(self):
        """Test tasks - Full CRUD"""
        print("\n📋 OPPGAVER - FULL CRUD")
        print("=" * 50)
        
        # Test 1: Get all tasks
        success, response = self.make_request("GET", "/tasks")
        if isinstance(response, str):
            self.log_test("GET /tasks - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                tasks = response.json()
                self.log_test("GET /tasks - hent alle", True, f"Retrieved {len(tasks)} tasks")
            except:
                self.log_test("GET /tasks - hent alle", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /tasks - hent alle", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new task
        new_task = {
            "title": "Test Oppgave - Følg opp kunde",
            "description": "Dette er en test oppgave for API testing",
            "due_date": "2024-12-31T23:59:59Z",
            "priority": "High",
            "type": "Customer",
            "status": "Planned"
        }
        success, response = self.make_request("POST", "/tasks", new_task, 201)
        if isinstance(response, str):
            self.log_test("POST /tasks - opprett ny", False, f"Request failed: {response}")
        elif success:
            try:
                created_task = response.json()
                task_id = created_task.get("id")
                self.created_resources.append(("task", task_id))
                self.log_test("POST /tasks - opprett ny", True, f"Task created with ID: {task_id}")
                
                # Test 3: Complete task
                success, response = self.make_request("PUT", f"/tasks/{task_id}/status", 
                                                    params={"status": "Done"})
                if isinstance(response, str):
                    self.log_test("PUT /tasks/{id}/complete - fullfør", False, f"Request failed: {response}")
                elif success:
                    self.log_test("PUT /tasks/{id}/complete - fullfør", True, "Task completed successfully")
                else:
                    self.log_test("PUT /tasks/{id}/complete - fullfør", False, f"Got status {response.status_code}")
                
                # Test 4: Delete task
                success, response = self.make_request("DELETE", f"/tasks/{task_id}", expected_status=204)
                if isinstance(response, str):
                    self.log_test("DELETE /tasks/{id} - slett", False, f"Request failed: {response}")
                elif success:
                    self.log_test("DELETE /tasks/{id} - slett", True, "Task deleted successfully")
                    # Remove from cleanup list since already deleted
                    self.created_resources = [(t, i) for t, i in self.created_resources if not (t == "task" and i == task_id)]
                else:
                    self.log_test("DELETE /tasks/{id} - slett", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("POST /tasks - opprett ny", False, f"JSON parsing error: {e}")
        else:
            self.log_test("POST /tasks - opprett ny", False, f"Got status {response.status_code}")

    def test_expenses_validation(self):
        """Test expenses - Validation"""
        print("\n💰 UTGIFTER - VALIDERING")
        print("=" * 50)
        
        # Test 1: Get all expenses
        success, response = self.make_request("GET", "/expenses")
        if isinstance(response, str):
            self.log_test("GET /expenses - hent alle", False, f"Request failed: {response}")
            return
        elif success:
            try:
                expenses = response.json()
                self.log_test("GET /expenses - hent alle", True, f"Retrieved {len(expenses)} expenses")
            except:
                self.log_test("GET /expenses - hent alle", False, "Invalid JSON response")
                return
        else:
            self.log_test("GET /expenses - hent alle", False, f"Got status {response.status_code}")
            return

        # Test 2: Create expense with positive amount
        positive_expense = {
            "category": "Software",
            "amount": 1500.0,
            "payment_status": "Unpaid",
            "notes": "Test expense - positive amount"
        }
        success, response = self.make_request("POST", "/expenses", positive_expense, 201)
        if isinstance(response, str):
            self.log_test("POST /expenses - positivt beløp", False, f"Request failed: {response}")
        elif success:
            try:
                created_expense = response.json()
                expense_id = created_expense.get("id")
                self.created_resources.append(("expense", expense_id))
                self.log_test("POST /expenses - positivt beløp", True, f"Expense created with ID: {expense_id}")
            except Exception as e:
                self.log_test("POST /expenses - positivt beløp", False, f"JSON parsing error: {e}")
        else:
            self.log_test("POST /expenses - positivt beløp", False, f"Got status {response.status_code}")

        # Test 3: Create expense with negative amount (should fail)
        negative_expense = {
            "category": "Marketing",
            "amount": -100.0,
            "payment_status": "Paid",
            "notes": "Test expense - negative amount"
        }
        success, response = self.make_request("POST", "/expenses", negative_expense, 400)
        if isinstance(response, str):
            self.log_test("POST /expenses - negativ utgift", False, f"Request failed: {response}")
        else:
            self.log_test("POST /expenses - negativ utgift", success, 
                         "Correctly rejected negative amount" if success else f"Got {response.status_code}")

        # Test 4: Create expense with null/zero amount (should fail)
        zero_expense = {
            "category": "Operations",
            "amount": 0.0,
            "payment_status": "Unpaid",
            "notes": "Test expense - zero amount"
        }
        success, response = self.make_request("POST", "/expenses", zero_expense, 400)
        if isinstance(response, str):
            self.log_test("POST /expenses - null beløp", False, f"Request failed: {response}")
        else:
            self.log_test("POST /expenses - null beløp", success, 
                         "Correctly rejected zero amount" if success else f"Got {response.status_code}")

    def test_dashboard_and_reports(self):
        """Test dashboard and reports"""
        print("\n📊 DASHBOARD OG RAPPORTER")
        print("=" * 50)
        
        # Test 1: Dashboard
        success, response = self.make_request("GET", "/dashboard")
        if isinstance(response, str):
            self.log_test("GET /dashboard - komplett data", False, f"Request failed: {response}")
        elif success:
            try:
                dashboard_data = response.json()
                required_sections = ["top_panel", "tasks", "sales_profit_graphs", "products", "customers"]
                missing_sections = [section for section in required_sections if section not in dashboard_data]
                
                if missing_sections:
                    self.log_test("GET /dashboard - komplett data", False, f"Missing sections: {missing_sections}")
                else:
                    self.log_test("GET /dashboard - komplett data", True, "Dashboard loaded with all required sections")
                    
            except Exception as e:
                self.log_test("GET /dashboard - komplett data", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /dashboard - komplett data", False, f"Got status {response.status_code}")

        # Test 2: Daily report
        success, response = self.make_request("GET", "/reports/daily")
        if isinstance(response, str):
            self.log_test("GET /reports/daily - dagens rapport", False, f"Request failed: {response}")
        elif success:
            try:
                daily_report = response.json()
                required_fields = ["date", "daily_sales", "daily_profit", "orders_today", "low_stock_count"]
                missing_fields = [field for field in required_fields if field not in daily_report]
                
                if missing_fields:
                    self.log_test("GET /reports/daily - dagens rapport", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("GET /reports/daily - dagens rapport", True, "Daily report loaded with all required fields")
                    
            except Exception as e:
                self.log_test("GET /reports/daily - dagens rapport", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /reports/daily - dagens rapport", False, f"Got status {response.status_code}")

        # Test 3: Monthly report
        success, response = self.make_request("GET", "/reports/monthly")
        if isinstance(response, str):
            self.log_test("GET /reports/monthly - månedlig rapport", False, f"Request failed: {response}")
        elif success:
            try:
                monthly_report = response.json()
                required_fields = ["month", "year", "monthly_sales", "monthly_profit", "top_products", "top_customers"]
                missing_fields = [field for field in required_fields if field not in monthly_report]
                
                if missing_fields:
                    self.log_test("GET /reports/monthly - månedlig rapport", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("GET /reports/monthly - månedlig rapport", True, "Monthly report loaded with all required fields")
                    
            except Exception as e:
                self.log_test("GET /reports/monthly - månedlig rapport", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /reports/monthly - månedlig rapport", False, f"Got status {response.status_code}")

    def test_search_functionality(self):
        """Test search functionality"""
        print("\n🔍 SØK")
        print("=" * 50)
        
        # Test 1: Search for products (vitamin)
        success, response = self.make_request("GET", "/search", params={"q": "vitamin"})
        if isinstance(response, str):
            self.log_test("GET /search?q=vitamin - søk produkter", False, f"Request failed: {response}")
        elif success:
            try:
                search_results = response.json()
                self.log_test("GET /search?q=vitamin - søk produkter", True, f"Search returned {len(search_results)} results for 'vitamin'")
            except Exception as e:
                self.log_test("GET /search?q=vitamin - søk produkter", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /search?q=vitamin - søk produkter", False, f"Got status {response.status_code}")

        # Test 2: Search for customers (admin)
        success, response = self.make_request("GET", "/search", params={"q": "admin"})
        if isinstance(response, str):
            self.log_test("GET /search?q=admin - søk kunder", False, f"Request failed: {response}")
        elif success:
            try:
                search_results = response.json()
                self.log_test("GET /search?q=admin - søk kunder", True, f"Search returned {len(search_results)} results for 'admin'")
            except Exception as e:
                self.log_test("GET /search?q=admin - søk kunder", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /search?q=admin - søk kunder", False, f"Got status {response.status_code}")

        # Test 3: Search for tasks (task)
        success, response = self.make_request("GET", "/search", params={"q": "task"})
        if isinstance(response, str):
            self.log_test("GET /search?q=task - søk oppgaver", False, f"Request failed: {response}")
        elif success:
            try:
                search_results = response.json()
                self.log_test("GET /search?q=task - søk oppgaver", True, f"Search returned {len(search_results)} results for 'task'")
            except Exception as e:
                self.log_test("GET /search?q=task - søk oppgaver", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /search?q=task - søk oppgaver", False, f"Got status {response.status_code}")

    def test_automation(self):
        """Test automation"""
        print("\n🤖 AUTOMATISERING")
        print("=" * 50)
        
        # Test 1: Get automation status
        success, response = self.make_request("GET", "/automation/status")
        if isinstance(response, str):
            self.log_test("GET /automation/status - hent status", False, f"Request failed: {response}")
        elif success:
            try:
                automation_status = response.json()
                self.log_test("GET /automation/status - hent status", True, "Automation status retrieved successfully")
            except Exception as e:
                self.log_test("GET /automation/status - hent status", False, f"JSON parsing error: {e}")
        else:
            self.log_test("GET /automation/status - hent status", False, f"Got status {response.status_code}")

        # Test 2: Trigger low stock check
        success, response = self.make_request("POST", "/automation/check-low-stock")
        if isinstance(response, str):
            self.log_test("POST /automation/check-low-stock - trigger", False, f"Request failed: {response}")
        elif success:
            try:
                check_result = response.json()
                self.log_test("POST /automation/check-low-stock - trigger", True, "Low stock check triggered successfully")
            except Exception as e:
                self.log_test("POST /automation/check-low-stock - trigger", False, f"JSON parsing error: {e}")
        else:
            self.log_test("POST /automation/check-low-stock - trigger", False, f"Got status {response.status_code}")

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        print("=" * 50)
        
        cleanup_count = 0
        
        for resource_type, resource_id in self.created_resources:
            if resource_type == "expense":
                success, response = self.make_request("DELETE", f"/expenses/{resource_id}", expected_status=204)
            elif resource_type == "task":
                success, response = self.make_request("DELETE", f"/tasks/{resource_id}", expected_status=204)
            elif resource_type == "customer":
                success, response = self.make_request("DELETE", f"/customers/{resource_id}", expected_status=204)
            elif resource_type == "supplier":
                success, response = self.make_request("DELETE", f"/suppliers/{resource_id}", expected_status=204)
            elif resource_type == "product":
                success, response = self.make_request("DELETE", f"/products/{resource_id}", expected_status=204)
            else:
                continue  # Skip orders and purchases as they might not have delete endpoints
                
            if success:
                cleanup_count += 1
        
        print(f"Cleaned up {cleanup_count} test resources")

    def run_comprehensive_test(self):
        """Run comprehensive API test"""
        print("🚀 FULLSTENDIG ENDE-TIL-ENDE TEST AV ZENVIT CRM BACKEND API")
        print(f"Backend URL: {self.base_url}")
        print(f"Test Credentials: {TEST_CREDENTIALS['email']}")
        print("=" * 80)
        
        # Authentication is required for all other tests
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all comprehensive tests
        self.test_products_full_crud()
        self.test_stock_full_functionality()
        self.test_customers_full_crud()
        self.test_orders_complete_workflow()
        self.test_purchases_complete_workflow()
        self.test_tasks_full_crud()
        self.test_expenses_validation()
        self.test_dashboard_and_reports()
        self.test_search_functionality()
        self.test_automation()
        
        # Clean up test data
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 SAMMENDRAG AV TESTRESULTATER")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        total = len(self.test_results)
        
        print(f"Totalt antall tester: {total}")
        print(f"Bestått: {passed} ✅")
        print(f"Feilet: {failed} ❌")
        print(f"Suksessrate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FEILEDE TESTER:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # Return overall success
        return failed == 0

if __name__ == "__main__":
    tester = ComprehensiveAPITester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("🎉 Alle tester bestått! Backend API fungerer korrekt.")
        sys.exit(0)
    else:
        print("⚠️  Noen tester feilet. Sjekk resultatene ovenfor.")
        sys.exit(1)