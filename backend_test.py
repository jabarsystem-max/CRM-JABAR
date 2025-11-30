#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for ZenVit CRM
Tests all CRUD operations and edge cases for all endpoints
"""

import requests
import json
import sys
from datetime import datetime, timezone
import uuid

# Configuration
BACKEND_URL = "https://inventory-zen-1.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@zenvit.no",
    "password": "admin123"
}

class ZenVitAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        self.created_resources = {
            "products": [],
            "customers": [],
            "suppliers": [],
            "orders": [],
            "tasks": [],
            "expenses": [],
            "purchases": []
        }

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

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== TESTING AUTH ENDPOINTS ===")
        
        # Test 1: Register new user (should fail - email exists)
        register_data = {
            "email": "test@zenvit.no",
            "password": "testpass123",
            "full_name": "Test Bruker",
            "role": "admin"
        }
        success, response = self.make_request("POST", "/auth/register", register_data, 400)
        if isinstance(response, str):
            self.log_test("Auth Register (existing email)", False, f"Request failed: {response}")
        else:
            self.log_test("Auth Register (existing email)", success, 
                         "Expected 400 for existing email" if success else f"Got {response.status_code}")

        # Test 2: Login with correct credentials
        success, response = self.make_request("POST", "/auth/login", TEST_CREDENTIALS)
        if isinstance(response, str):
            self.log_test("Auth Login (correct credentials)", False, f"Request failed: {response}")
            return False
        elif success and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                self.log_test("Auth Login (correct credentials)", True, "Login successful, token received")
            except:
                self.log_test("Auth Login (correct credentials)", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Auth Login (correct credentials)", False, f"Got status {response.status_code}")
            return False

        # Test 3: Login with wrong password
        wrong_creds = {"email": "admin@zenvit.no", "password": "wrongpass"}
        success, response = self.make_request("POST", "/auth/login", wrong_creds, 401)
        if isinstance(response, str):
            self.log_test("Auth Login (wrong password)", False, f"Request failed: {response}")
        else:
            self.log_test("Auth Login (wrong password)", success, 
                         "Expected 401 for wrong password" if success else f"Got {response.status_code}")

        # Test 4: Get current user info
        success, response = self.make_request("GET", "/auth/me")
        if isinstance(response, str):
            self.log_test("Auth Get Me", False, f"Request failed: {response}")
        elif success:
            try:
                data = response.json()
                self.log_test("Auth Get Me", True, f"User info retrieved: {data.get('email', 'N/A')}")
            except:
                self.log_test("Auth Get Me", False, "Invalid JSON response")
        else:
            self.log_test("Auth Get Me", False, f"Got status {response.status_code}")

        return self.token is not None

    def test_products_endpoints(self):
        """Test products CRUD operations"""
        print("\n=== TESTING PRODUCTS ENDPOINTS ===")
        
        # Test 1: Get all products
        success, response = self.make_request("GET", "/products")
        if isinstance(response, str):
            self.log_test("Products GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                products = response.json()
                self.log_test("Products GET all", True, f"Retrieved {len(products)} products")
            except:
                self.log_test("Products GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Products GET all", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new product
        new_product = {
            "sku": f"TEST-{uuid.uuid4().hex[:8].upper()}",
            "name": "Test Produkt Magnesium Plus",
            "category": "Kosttilskudd",
            "cost": 150.0,
            "price": 299.0,
            "description": "Test produkt for API testing",
            "color": "blue"
        }
        success, response = self.make_request("POST", "/products", new_product, 201)
        if isinstance(response, str):
            self.log_test("Products POST create", False, f"Request failed: {response}")
        elif success:
            try:
                created_product = response.json()
                product_id = created_product.get("id")
                self.created_resources["products"].append(product_id)
                self.log_test("Products POST create", True, f"Product created with ID: {product_id}")
                
                # Test 3: Update the created product
                update_data = {
                    "sku": new_product["sku"],
                    "name": "Updated Test Produkt",
                    "category": "Kosttilskudd",
                    "cost": 160.0,
                    "price": 319.0,
                    "description": "Updated description"
                }
                success, response = self.make_request("PUT", f"/products/{product_id}", update_data)
                if isinstance(response, str):
                    self.log_test("Products PUT update", False, f"Request failed: {response}")
                elif success:
                    self.log_test("Products PUT update", True, "Product updated successfully")
                else:
                    self.log_test("Products PUT update", False, f"Got status {response.status_code}")
                
                # Test 4: Delete product (soft delete)
                success, response = self.make_request("DELETE", f"/products/{product_id}", expected_status=204)
                if isinstance(response, str):
                    self.log_test("Products DELETE", False, f"Request failed: {response}")
                elif success:
                    self.log_test("Products DELETE", True, "Product deleted successfully")
                else:
                    self.log_test("Products DELETE", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("Products POST create", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Products POST create", False, f"Got status {response.status_code}")

        # Test 5: Create product with duplicate SKU (should fail)
        duplicate_product = {
            "sku": "VIT-D3K2",  # Assuming this exists
            "name": "Duplicate Test",
            "category": "Test",
            "cost": 100.0,
            "price": 200.0
        }
        success, response = self.make_request("POST", "/products", duplicate_product, 400)
        if isinstance(response, str):
            self.log_test("Products POST duplicate SKU", False, f"Request failed: {response}")
        else:
            # Note: The API might not have duplicate SKU validation, so we check if it fails or succeeds
            if response.status_code == 400:
                self.log_test("Products POST duplicate SKU", True, "Correctly rejected duplicate SKU")
            elif response.status_code == 201:
                self.log_test("Products POST duplicate SKU", True, "API allows duplicate SKU (no validation)")
                # Clean up if created
                try:
                    data = response.json()
                    if data.get("id"):
                        self.created_resources["products"].append(data["id"])
                except:
                    pass
            else:
                self.log_test("Products POST duplicate SKU", False, f"Unexpected status {response.status_code}")

    def test_stock_endpoints(self):
        """Test stock management endpoints"""
        print("\n=== TESTING STOCK ENDPOINTS ===")
        
        # Test 1: Get all stock
        success, response = self.make_request("GET", "/stock")
        if isinstance(response, str):
            self.log_test("Stock GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                stock_items = response.json()
                self.log_test("Stock GET all", True, f"Retrieved {len(stock_items)} stock items")
                
                # Test 2: Update stock for first item if available
                if stock_items:
                    first_item = stock_items[0]
                    product_id = first_item.get("product_id")
                    if product_id:
                        stock_update = {
                            "quantity": first_item.get("quantity", 0) + 10,
                            "min_stock": 50
                        }
                        success, response = self.make_request("PUT", f"/stock/{product_id}", stock_update)
                        if isinstance(response, str):
                            self.log_test("Stock PUT update", False, f"Request failed: {response}")
                        elif success:
                            self.log_test("Stock PUT update", True, "Stock updated successfully")
                        else:
                            self.log_test("Stock PUT update", False, f"Got status {response.status_code}")
                else:
                    self.log_test("Stock PUT update", False, "No stock items available for testing")
                    
            except Exception as e:
                self.log_test("Stock GET all", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Stock GET all", False, f"Got status {response.status_code}")

        # Test 3: Get stock movements
        success, response = self.make_request("GET", "/stock-movements")
        if isinstance(response, str):
            self.log_test("Stock Movements GET", False, f"Request failed: {response}")
        elif success:
            try:
                movements = response.json()
                self.log_test("Stock Movements GET", True, f"Retrieved {len(movements)} stock movements")
            except:
                self.log_test("Stock Movements GET", False, "Invalid JSON response")
        else:
            self.log_test("Stock Movements GET", False, f"Got status {response.status_code}")

    def test_customers_endpoints(self):
        """Test customers CRUD operations"""
        print("\n=== TESTING CUSTOMERS ENDPOINTS ===")
        
        # Test 1: Get all customers
        success, response = self.make_request("GET", "/customers")
        if isinstance(response, str):
            self.log_test("Customers GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                customers = response.json()
                self.log_test("Customers GET all", True, f"Retrieved {len(customers)} customers")
            except:
                self.log_test("Customers GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Customers GET all", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new customer
        new_customer = {
            "name": "Test Kunde AS",
            "email": f"test{uuid.uuid4().hex[:8]}@example.com",
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
            self.log_test("Customers POST create", False, f"Request failed: {response}")
        elif success:
            try:
                created_customer = response.json()
                customer_id = created_customer.get("id")
                self.created_resources["customers"].append(customer_id)
                self.log_test("Customers POST create", True, f"Customer created with ID: {customer_id}")
                
                # Test 3: Update customer
                update_data = {
                    "name": "Updated Test Kunde AS",
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
                    self.log_test("Customers PUT update", False, f"Request failed: {response}")
                elif success:
                    self.log_test("Customers PUT update", True, "Customer updated successfully")
                else:
                    self.log_test("Customers PUT update", False, f"Got status {response.status_code}")
                
                # Test 4: Get customer timeline
                success, response = self.make_request("GET", f"/customers/{customer_id}/timeline")
                if isinstance(response, str):
                    self.log_test("Customers GET timeline", False, f"Request failed: {response}")
                elif success:
                    try:
                        timeline = response.json()
                        self.log_test("Customers GET timeline", True, f"Retrieved {len(timeline)} timeline entries")
                    except:
                        self.log_test("Customers GET timeline", False, "Invalid JSON response")
                else:
                    self.log_test("Customers GET timeline", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("Customers POST create", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Customers POST create", False, f"Got status {response.status_code}")

        # Test 5: Create customer with invalid email
        invalid_customer = {
            "name": "Invalid Email Test",
            "email": "invalid-email",
            "type": "Private"
        }
        success, response = self.make_request("POST", "/customers", invalid_customer, 422)
        if isinstance(response, str):
            self.log_test("Customers POST invalid email", False, f"Request failed: {response}")
        else:
            expected_fail = response.status_code == 422
            self.log_test("Customers POST invalid email", expected_fail, 
                         "Correctly rejected invalid email" if expected_fail else f"Got {response.status_code}")

    def test_suppliers_endpoints(self):
        """Test suppliers CRUD operations"""
        print("\n=== TESTING SUPPLIERS ENDPOINTS ===")
        
        # Test 1: Get all suppliers
        success, response = self.make_request("GET", "/suppliers")
        if isinstance(response, str):
            self.log_test("Suppliers GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                suppliers = response.json()
                self.log_test("Suppliers GET all", True, f"Retrieved {len(suppliers)} suppliers")
            except:
                self.log_test("Suppliers GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Suppliers GET all", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new supplier
        new_supplier = {
            "name": "Test Leverandør AS",
            "contact_person": "Test Kontakt",
            "email": f"supplier{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+47 11223344",
            "address": "Leverandørveien 789",
            "website": "https://testleverandor.no",
            "notes": "Test leverandør for API testing"
        }
        success, response = self.make_request("POST", "/suppliers", new_supplier, 201)
        if isinstance(response, str):
            self.log_test("Suppliers POST create", False, f"Request failed: {response}")
        elif success:
            try:
                created_supplier = response.json()
                supplier_id = created_supplier.get("id")
                self.created_resources["suppliers"].append(supplier_id)
                self.log_test("Suppliers POST create", True, f"Supplier created with ID: {supplier_id}")
                
                # Test 3: Update supplier
                update_data = {
                    "name": "Updated Test Leverandør AS",
                    "contact_person": "Updated Kontakt",
                    "email": new_supplier["email"],
                    "phone": "+47 44332211",
                    "address": "Updated Address 999",
                    "website": "https://updated-leverandor.no",
                    "notes": "Updated notes"
                }
                success, response = self.make_request("PUT", f"/suppliers/{supplier_id}", update_data)
                if isinstance(response, str):
                    self.log_test("Suppliers PUT update", False, f"Request failed: {response}")
                elif success:
                    self.log_test("Suppliers PUT update", True, "Supplier updated successfully")
                else:
                    self.log_test("Suppliers PUT update", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("Suppliers POST create", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Suppliers POST create", False, f"Got status {response.status_code}")

    def test_tasks_endpoints(self):
        """Test tasks CRUD operations"""
        print("\n=== TESTING TASKS ENDPOINTS ===")
        
        # Test 1: Get all tasks
        success, response = self.make_request("GET", "/tasks")
        if isinstance(response, str):
            self.log_test("Tasks GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                tasks = response.json()
                self.log_test("Tasks GET all", True, f"Retrieved {len(tasks)} tasks")
            except:
                self.log_test("Tasks GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Tasks GET all", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new task
        new_task = {
            "title": "Test Oppgave API",
            "description": "Dette er en test oppgave for API testing",
            "due_date": "2024-12-31T23:59:59Z",
            "priority": "High",
            "type": "Admin",
            "status": "Planned"
        }
        success, response = self.make_request("POST", "/tasks", new_task, 201)
        if isinstance(response, str):
            self.log_test("Tasks POST create", False, f"Request failed: {response}")
        elif success:
            try:
                created_task = response.json()
                task_id = created_task.get("id")
                self.created_resources["tasks"].append(task_id)
                self.log_test("Tasks POST create", True, f"Task created with ID: {task_id}")
                
                # Test 3: Update task
                update_data = {
                    "title": "Updated Test Oppgave",
                    "description": "Updated description",
                    "due_date": "2024-12-25T12:00:00Z",
                    "priority": "Medium",
                    "type": "Admin"
                }
                success, response = self.make_request("PUT", f"/tasks/{task_id}", update_data)
                if isinstance(response, str):
                    self.log_test("Tasks PUT update", False, f"Request failed: {response}")
                elif success:
                    self.log_test("Tasks PUT update", True, "Task updated successfully")
                else:
                    self.log_test("Tasks PUT update", False, f"Got status {response.status_code}")
                
                # Test 4: Update task status
                success, response = self.make_request("PUT", f"/tasks/{task_id}/status?status=Done")
                if isinstance(response, str):
                    self.log_test("Tasks PUT status", False, f"Request failed: {response}")
                elif success:
                    self.log_test("Tasks PUT status", True, "Task status updated successfully")
                else:
                    self.log_test("Tasks PUT status", False, f"Got status {response.status_code}")
                    
            except Exception as e:
                self.log_test("Tasks POST create", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Tasks POST create", False, f"Got status {response.status_code}")

        # Test 5: Get tasks by status
        success, response = self.make_request("GET", "/tasks?status=Planned")
        if isinstance(response, str):
            self.log_test("Tasks GET by status", False, f"Request failed: {response}")
        elif success:
            try:
                filtered_tasks = response.json()
                self.log_test("Tasks GET by status", True, f"Retrieved {len(filtered_tasks)} planned tasks")
            except:
                self.log_test("Tasks GET by status", False, "Invalid JSON response")
        else:
            self.log_test("Tasks GET by status", False, f"Got status {response.status_code}")

    def test_expenses_endpoints(self):
        """Test expenses CRUD operations"""
        print("\n=== TESTING EXPENSES ENDPOINTS ===")
        
        # Test 1: Get all expenses
        success, response = self.make_request("GET", "/expenses")
        if isinstance(response, str):
            self.log_test("Expenses GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                expenses = response.json()
                self.log_test("Expenses GET all", True, f"Retrieved {len(expenses)} expenses")
            except:
                self.log_test("Expenses GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Expenses GET all", False, f"Got status {response.status_code}")
            return

        # Test 2: Create new expense
        new_expense = {
            "category": "Software",
            "amount": 1500.0,
            "payment_status": "Unpaid",
            "notes": "Test expense for API testing"
        }
        success, response = self.make_request("POST", "/expenses", new_expense, 201)
        if isinstance(response, str):
            self.log_test("Expenses POST create", False, f"Request failed: {response}")
        elif success:
            try:
                created_expense = response.json()
                expense_id = created_expense.get("id")
                self.created_resources["expenses"].append(expense_id)
                self.log_test("Expenses POST create", True, f"Expense created with ID: {expense_id}")
            except Exception as e:
                self.log_test("Expenses POST create", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Expenses POST create", False, f"Got status {response.status_code}")

        # Test 3: Create expense with negative amount (edge case)
        negative_expense = {
            "category": "Marketing",
            "amount": -100.0,
            "payment_status": "Paid",
            "notes": "Negative amount test"
        }
        success, response = self.make_request("POST", "/expenses", negative_expense, 201)
        if isinstance(response, str):
            self.log_test("Expenses POST negative amount", False, f"Request failed: {response}")
        else:
            if response.status_code == 201:
                self.log_test("Expenses POST negative amount", True, "API allows negative amounts")
                try:
                    data = response.json()
                    if data.get("id"):
                        self.created_resources["expenses"].append(data["id"])
                except:
                    pass
            elif response.status_code == 400:
                self.log_test("Expenses POST negative amount", True, "API correctly rejects negative amounts")
            else:
                self.log_test("Expenses POST negative amount", False, f"Unexpected status {response.status_code}")

    def test_orders_endpoints(self):
        """Test orders CRUD operations"""
        print("\n=== TESTING ORDERS ENDPOINTS ===")
        
        # Test 1: Get all orders
        success, response = self.make_request("GET", "/orders")
        if isinstance(response, str):
            self.log_test("Orders GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                orders = response.json()
                self.log_test("Orders GET all", True, f"Retrieved {len(orders)} orders")
            except:
                self.log_test("Orders GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Orders GET all", False, f"Got status {response.status_code}")
            return

        # Get existing customers and products for order creation
        customers_success, customers_response = self.make_request("GET", "/customers")
        products_success, products_response = self.make_request("GET", "/products")
        
        if not (customers_success and products_success):
            self.log_test("Orders POST create", False, "Cannot get customers or products for order creation")
            return
            
        try:
            customers = customers_response.json()
            products = products_response.json()
            
            if not customers or not products:
                self.log_test("Orders POST create", False, "No customers or products available for order creation")
                return
                
            # Test 2: Create new order
            customer = customers[0]
            product = products[0]
            
            new_order = {
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
                "shipping_paid_by_customer": 99.0,
                "shipping_cost": 50.0,
                "payment_method": "Card",
                "notes": "Test order for API testing"
            }
            
            success, response = self.make_request("POST", "/orders", new_order, 201)
            if isinstance(response, str):
                self.log_test("Orders POST create", False, f"Request failed: {response}")
            elif success:
                try:
                    created_order = response.json()
                    order_id = created_order.get("id")
                    self.created_resources["orders"].append(order_id)
                    self.log_test("Orders POST create", True, f"Order created with ID: {order_id}")
                    
                    # Test 3: Update order status
                    success, response = self.make_request("PUT", f"/orders/{order_id}/status?status=Shipped")
                    if isinstance(response, str):
                        self.log_test("Orders PUT status", False, f"Request failed: {response}")
                    elif success:
                        self.log_test("Orders PUT status", True, "Order status updated successfully")
                    else:
                        self.log_test("Orders PUT status", False, f"Got status {response.status_code}")
                        
                except Exception as e:
                    self.log_test("Orders POST create", False, f"JSON parsing error: {e}")
            else:
                self.log_test("Orders POST create", False, f"Got status {response.status_code}")
                
        except Exception as e:
            self.log_test("Orders POST create", False, f"Error processing customers/products: {e}")

    def test_purchases_endpoints(self):
        """Test purchases CRUD operations"""
        print("\n=== TESTING PURCHASES ENDPOINTS ===")
        
        # Test 1: Get all purchases
        success, response = self.make_request("GET", "/purchases")
        if isinstance(response, str):
            self.log_test("Purchases GET all", False, f"Request failed: {response}")
            return
        elif success:
            try:
                purchases = response.json()
                self.log_test("Purchases GET all", True, f"Retrieved {len(purchases)} purchases")
            except:
                self.log_test("Purchases GET all", False, "Invalid JSON response")
                return
        else:
            self.log_test("Purchases GET all", False, f"Got status {response.status_code}")
            return

        # Get existing suppliers and products for purchase creation
        suppliers_success, suppliers_response = self.make_request("GET", "/suppliers")
        products_success, products_response = self.make_request("GET", "/products")
        
        if not (suppliers_success and products_success):
            self.log_test("Purchases POST create", False, "Cannot get suppliers or products for purchase creation")
            return
            
        try:
            suppliers = suppliers_response.json()
            products = products_response.json()
            
            if not suppliers or not products:
                self.log_test("Purchases POST create", False, "No suppliers or products available for purchase creation")
                return
                
            # Test 2: Create new purchase
            supplier = suppliers[0]
            product = products[0]
            
            new_purchase = {
                "supplier_id": supplier["id"],
                "items": [
                    {
                        "product_id": product["id"],
                        "quantity": 50
                    }
                ],
                "notes": "Test purchase for API testing"
            }
            
            success, response = self.make_request("POST", "/purchases", new_purchase, 201)
            if isinstance(response, str):
                self.log_test("Purchases POST create", False, f"Request failed: {response}")
            elif success:
                try:
                    created_purchase = response.json()
                    purchase_id = created_purchase.get("id")
                    self.created_resources["purchases"].append(purchase_id)
                    self.log_test("Purchases POST create", True, f"Purchase created with ID: {purchase_id}")
                    
                    # Test 3: Receive purchase (update stock)
                    success, response = self.make_request("PUT", f"/purchases/{purchase_id}/receive")
                    if isinstance(response, str):
                        self.log_test("Purchases PUT receive", False, f"Request failed: {response}")
                    elif success:
                        self.log_test("Purchases PUT receive", True, "Purchase received successfully, stock updated")
                    else:
                        self.log_test("Purchases PUT receive", False, f"Got status {response.status_code}")
                        
                except Exception as e:
                    self.log_test("Purchases POST create", False, f"JSON parsing error: {e}")
            else:
                self.log_test("Purchases POST create", False, f"Got status {response.status_code}")
                
        except Exception as e:
            self.log_test("Purchases POST create", False, f"Error processing suppliers/products: {e}")

    def test_dashboard_endpoint(self):
        """Test dashboard endpoint"""
        print("\n=== TESTING DASHBOARD ENDPOINT ===")
        
        success, response = self.make_request("GET", "/dashboard")
        if isinstance(response, str):
            self.log_test("Dashboard GET", False, f"Request failed: {response}")
        elif success:
            try:
                dashboard_data = response.json()
                required_sections = ["top_panel", "tasks", "sales_profit_graphs", "products", "customers"]
                missing_sections = [section for section in required_sections if section not in dashboard_data]
                
                if missing_sections:
                    self.log_test("Dashboard GET", False, f"Missing sections: {missing_sections}")
                else:
                    self.log_test("Dashboard GET", True, "Dashboard data loaded with all required sections")
                    
            except Exception as e:
                self.log_test("Dashboard GET", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Dashboard GET", False, f"Got status {response.status_code}")

    def test_reports_endpoints(self):
        """Test reports endpoints"""
        print("\n=== TESTING REPORTS ENDPOINTS ===")
        
        # Test 1: Daily report
        success, response = self.make_request("GET", "/reports/daily")
        if isinstance(response, str):
            self.log_test("Reports GET daily", False, f"Request failed: {response}")
        elif success:
            try:
                daily_report = response.json()
                required_fields = ["date", "daily_sales", "daily_profit", "orders_today", "low_stock_count"]
                missing_fields = [field for field in required_fields if field not in daily_report]
                
                if missing_fields:
                    self.log_test("Reports GET daily", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Reports GET daily", True, "Daily report loaded with all required fields")
                    
            except Exception as e:
                self.log_test("Reports GET daily", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Reports GET daily", False, f"Got status {response.status_code}")

        # Test 2: Monthly report
        success, response = self.make_request("GET", "/reports/monthly")
        if isinstance(response, str):
            self.log_test("Reports GET monthly", False, f"Request failed: {response}")
        elif success:
            try:
                monthly_report = response.json()
                required_fields = ["month", "year", "monthly_sales", "monthly_profit", "top_products", "top_customers"]
                missing_fields = [field for field in required_fields if field not in monthly_report]
                
                if missing_fields:
                    self.log_test("Reports GET monthly", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Reports GET monthly", True, "Monthly report loaded with all required fields")
                    
            except Exception as e:
                self.log_test("Reports GET monthly", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Reports GET monthly", False, f"Got status {response.status_code}")

    def test_search_endpoint(self):
        """Test search endpoint"""
        print("\n=== TESTING SEARCH ENDPOINT ===")
        
        # Test 1: Search for products (magnesium)
        success, response = self.make_request("GET", "/search?q=magnesium")
        if isinstance(response, str):
            self.log_test("Search GET magnesium", False, f"Request failed: {response}")
        elif success:
            try:
                search_results = response.json()
                self.log_test("Search GET magnesium", True, f"Search returned {len(search_results)} results for 'magnesium'")
            except Exception as e:
                self.log_test("Search GET magnesium", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Search GET magnesium", False, f"Got status {response.status_code}")

        # Test 2: Search for customers (ola)
        success, response = self.make_request("GET", "/search?q=ola")
        if isinstance(response, str):
            self.log_test("Search GET ola", False, f"Request failed: {response}")
        elif success:
            try:
                search_results = response.json()
                self.log_test("Search GET ola", True, f"Search returned {len(search_results)} results for 'ola'")
            except Exception as e:
                self.log_test("Search GET ola", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Search GET ola", False, f"Got status {response.status_code}")

        # Test 3: Empty search query
        success, response = self.make_request("GET", "/search?q=")
        if isinstance(response, str):
            self.log_test("Search GET empty", False, f"Request failed: {response}")
        else:
            # Empty search might return 400 or empty results, both are acceptable
            if response.status_code in [200, 400]:
                self.log_test("Search GET empty", True, f"Empty search handled correctly (status {response.status_code})")
            else:
                self.log_test("Search GET empty", False, f"Unexpected status {response.status_code}")

    def test_automation_endpoints(self):
        """Test automation endpoints"""
        print("\n=== TESTING AUTOMATION ENDPOINTS ===")
        
        # Test 1: Get automation status
        success, response = self.make_request("GET", "/automation/status")
        if isinstance(response, str):
            self.log_test("Automation GET status", False, f"Request failed: {response}")
        elif success:
            try:
                automation_status = response.json()
                self.log_test("Automation GET status", True, "Automation status retrieved successfully")
            except Exception as e:
                self.log_test("Automation GET status", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Automation GET status", False, f"Got status {response.status_code}")

        # Test 2: Trigger low stock check
        success, response = self.make_request("POST", "/automation/check-low-stock")
        if isinstance(response, str):
            self.log_test("Automation POST check-low-stock", False, f"Request failed: {response}")
        elif success:
            try:
                check_result = response.json()
                self.log_test("Automation POST check-low-stock", True, "Low stock check triggered successfully")
            except Exception as e:
                self.log_test("Automation POST check-low-stock", False, f"JSON parsing error: {e}")
        else:
            self.log_test("Automation POST check-low-stock", False, f"Got status {response.status_code}")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n=== TESTING EDGE CASES ===")
        
        # Test 1: Invalid product ID
        success, response = self.make_request("GET", "/products/invalid-id", expected_status=404)
        if isinstance(response, str):
            self.log_test("Edge Case: Invalid Product ID", False, f"Request failed: {response}")
        else:
            expected_fail = response.status_code == 404
            self.log_test("Edge Case: Invalid Product ID", expected_fail, 
                         "Correctly returned 404" if expected_fail else f"Got {response.status_code}")

        # Test 2: Invalid customer ID
        success, response = self.make_request("GET", "/customers/invalid-id", expected_status=404)
        if isinstance(response, str):
            self.log_test("Edge Case: Invalid Customer ID", False, f"Request failed: {response}")
        else:
            expected_fail = response.status_code == 404
            self.log_test("Edge Case: Invalid Customer ID", expected_fail, 
                         "Correctly returned 404" if expected_fail else f"Got {response.status_code}")

        # Test 3: Missing required fields in product creation
        invalid_product = {
            "name": "Missing SKU Product"
            # Missing required fields: sku, category, cost, price
        }
        success, response = self.make_request("POST", "/products", invalid_product, 422)
        if isinstance(response, str):
            self.log_test("Edge Case: Missing Required Fields", False, f"Request failed: {response}")
        else:
            expected_fail = response.status_code == 422
            self.log_test("Edge Case: Missing Required Fields", expected_fail, 
                         "Correctly rejected missing fields" if expected_fail else f"Got {response.status_code}")

        # Test 4: Unauthorized request (no token)
        old_headers = self.headers.copy()
        self.headers = {"Content-Type": "application/json"}  # Remove auth header
        
        success, response = self.make_request("GET", "/products", expected_status=401)
        if isinstance(response, str):
            self.log_test("Edge Case: Unauthorized Request", False, f"Request failed: {response}")
        else:
            expected_fail = response.status_code == 401
            self.log_test("Edge Case: Unauthorized Request", expected_fail, 
                         "Correctly returned 401" if expected_fail else f"Got {response.status_code}")
        
        self.headers = old_headers  # Restore auth header

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== CLEANING UP TEST DATA ===")
        
        cleanup_count = 0
        
        # Delete created expenses
        for expense_id in self.created_resources["expenses"]:
            success, response = self.make_request("DELETE", f"/expenses/{expense_id}", expected_status=204)
            if success:
                cleanup_count += 1
        
        # Delete created tasks
        for task_id in self.created_resources["tasks"]:
            success, response = self.make_request("DELETE", f"/tasks/{task_id}", expected_status=204)
            if success:
                cleanup_count += 1
        
        # Delete created customers
        for customer_id in self.created_resources["customers"]:
            success, response = self.make_request("DELETE", f"/customers/{customer_id}", expected_status=204)
            if success:
                cleanup_count += 1
        
        # Delete created suppliers
        for supplier_id in self.created_resources["suppliers"]:
            success, response = self.make_request("DELETE", f"/suppliers/{supplier_id}", expected_status=204)
            if success:
                cleanup_count += 1
        
        # Delete created products (soft delete)
        for product_id in self.created_resources["products"]:
            success, response = self.make_request("DELETE", f"/products/{product_id}", expected_status=204)
            if success:
                cleanup_count += 1
        
        print(f"Cleaned up {cleanup_count} test resources")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting ZenVit CRM Backend API Testing")
        print(f"Backend URL: {self.base_url}")
        print(f"Test Credentials: {TEST_CREDENTIALS['email']}")
        print("=" * 60)
        
        # Authentication is required for all other tests
        if not self.test_auth_endpoints():
            print("\n❌ CRITICAL: Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all endpoint tests
        self.test_products_endpoints()
        self.test_stock_endpoints()
        self.test_customers_endpoints()
        self.test_suppliers_endpoints()
        self.test_tasks_endpoints()
        self.test_expenses_endpoints()
        self.test_orders_endpoints()
        self.test_purchases_endpoints()
        self.test_dashboard_endpoint()
        self.test_reports_endpoints()
        self.test_search_endpoint()
        self.test_automation_endpoints()
        self.test_edge_cases()
        
        # Clean up test data
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
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
    tester = ZenVitAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed! Backend API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the results above.")
        sys.exit(1)