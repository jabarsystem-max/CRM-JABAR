from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="ZenVit CRM API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============================================================================
# MODELS
# ============================================================================

# --- User Models ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "admin"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


# --- Product Models ---
class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # ProductID
    sku: str  # SKU
    name: str  # Name
    category: str  # Category - "vitamin", "supplement", etc.
    cost: float  # CostPrice - Innkjøpspris
    price: float  # SalePrice - Salgspris
    min_stock: int = 80  # MinStock
    stock_status: Optional[str] = "OK"  # StockStatus - auto: "OK" | "Low" | "Out"
    description: Optional[str] = None  # Description
    supplier_id: Optional[str] = None  # SupplierID
    active: bool = True  # Active
    color: Optional[str] = None  # For UI styling
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    cost: float
    price: float
    min_stock: int = 80
    description: Optional[str] = None
    supplier_id: Optional[str] = None
    color: Optional[str] = None


# --- Customer Models ---
class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    notes: Optional[str] = None


# --- Inventory Models ---
class Inventory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    quantity: int
    location: Optional[str] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryUpdate(BaseModel):
    quantity: int


# --- Order Models ---
class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total: float

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    customer_name: str
    items: List[OrderItem]
    subtotal: float
    total: float
    status: str = "pending"  # pending, completed, cancelled
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    customer_id: str
    items: List[Dict[str, Any]]  # [{product_id, quantity}]
    notes: Optional[str] = None


# --- Supplier Models ---
class Supplier(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    products_supplied: List[str] = []  # Product IDs
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    products_supplied: List[str] = []
    notes: Optional[str] = None


# --- Purchase Order Models ---
class PurchaseItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_cost: float
    total: float

class Purchase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str
    supplier_name: str
    items: List[PurchaseItem]
    total: float
    status: str = "pending"  # pending, received, cancelled
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    received_date: Optional[datetime] = None
    notes: Optional[str] = None

class PurchaseCreate(BaseModel):
    supplier_id: str
    items: List[Dict[str, Any]]  # [{product_id, quantity}]
    notes: Optional[str] = None


# --- Cost Models ---
class Cost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # "marketing", "rent", "utilities", "salaries", etc.
    description: str
    amount: float
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recurring: bool = False
    notes: Optional[str] = None

class CostCreate(BaseModel):
    category: str
    description: str
    amount: float
    recurring: bool = False
    notes: Optional[str] = None


# ============================================================================
# AUTHENTICATION UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_data = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if user_data is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Convert ISO string to datetime if needed
    if isinstance(user_data.get('created_at'), str):
        user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
    
    return User(**user_data)

def calculate_stock_status(quantity: int, min_stock: int) -> str:
    """Calculate stock status based on quantity and minimum stock level"""
    if quantity == 0:
        return "Out"
    elif quantity < min_stock:
        return "Low"
    else:
        return "OK"

async def update_product_stock_status(product_id: str, quantity: int):
    """Update product stock status based on current quantity"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if product:
        min_stock = product.get('min_stock', 80)
        stock_status = calculate_stock_status(quantity, min_stock)
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"stock_status": stock_status}}
        )


# ============================================================================
# AUTH ROUTES
# ============================================================================

@api_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_dict = user_create.model_dump(exclude={'password'})
    user = User(**user_dict)
    
    # Hash password and store
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['hashed_password'] = hash_password(user_create.password)
    
    await db.users.insert_one(doc)
    return user

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    # Find user
    user_data = await db.users.find_one({"email": user_login.email})
    if not user_data:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Verify password
    if not verify_password(user_login.password, user_data['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create token
    access_token = create_access_token(data={"sub": user_data['id']})
    
    # Return user without password
    user_data.pop('hashed_password', None)
    user_data.pop('_id', None)
    if isinstance(user_data.get('created_at'), str):
        user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
    
    return TokenResponse(
        access_token=access_token,
        user=User(**user_data)
    )

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ============================================================================
# PRODUCT ROUTES
# ============================================================================

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: User = Depends(get_current_user)):
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    for p in products:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
    return products

@api_router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product_create: ProductCreate, current_user: User = Depends(get_current_user)):
    product = Product(**product_create.model_dump())
    doc = product.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.products.insert_one(doc)
    
    # Create inventory entry for this product
    inventory = Inventory(product_id=product.id, quantity=0)
    inv_doc = inventory.model_dump()
    inv_doc['last_updated'] = inv_doc['last_updated'].isoformat()
    await db.inventory.insert_one(inv_doc)
    
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: ProductCreate, current_user: User = Depends(get_current_user)):
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": product_update.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Product(**updated)

@api_router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, current_user: User = Depends(get_current_user)):
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": {"active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return None


# ============================================================================
# CUSTOMER ROUTES
# ============================================================================

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(current_user: User = Depends(get_current_user)):
    customers = await db.customers.find({}, {"_id": 0}).to_list(1000)
    for c in customers:
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
    return customers

@api_router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(customer_create: CustomerCreate, current_user: User = Depends(get_current_user)):
    customer = Customer(**customer_create.model_dump())
    doc = customer.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.customers.insert_one(doc)
    return customer

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: CustomerCreate, current_user: User = Depends(get_current_user)):
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$set": customer_update.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Customer(**updated)

@api_router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str, current_user: User = Depends(get_current_user)):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None


# ============================================================================
# INVENTORY ROUTES
# ============================================================================

@api_router.get("/inventory", response_model=List[Dict[str, Any]])
async def get_inventory(current_user: User = Depends(get_current_user)):
    inventory = await db.inventory.find({}, {"_id": 0}).to_list(1000)
    
    # Enrich with product info and update stock status
    for inv in inventory:
        if isinstance(inv.get('last_updated'), str):
            inv['last_updated'] = datetime.fromisoformat(inv['last_updated'])
        
        product = await db.products.find_one({"id": inv['product_id']}, {"_id": 0})
        if product:
            inv['product_name'] = product['name']
            inv['product_sku'] = product['sku']
            inv['product_cost'] = product['cost']
            inv['product_color'] = product.get('color')
            inv['min_quantity'] = product.get('min_stock', 80)
            inv['stock_status'] = product.get('stock_status', 'OK')
    
    return inventory

@api_router.put("/inventory/{product_id}", response_model=Dict[str, Any])
async def update_inventory(product_id: str, inventory_update: InventoryUpdate, current_user: User = Depends(get_current_user)):
    update_data = {"quantity": inventory_update.quantity, "last_updated": datetime.now(timezone.utc).isoformat()}
    
    result = await db.inventory.update_one(
        {"product_id": product_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    # Update product stock status
    await update_product_stock_status(product_id, inventory_update.quantity)
    
    updated = await db.inventory.find_one({"product_id": product_id}, {"_id": 0})
    if isinstance(updated.get('last_updated'), str):
        updated['last_updated'] = datetime.fromisoformat(updated['last_updated'])
    
    # Enrich with product info
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if product:
        updated['product_name'] = product['name']
        updated['product_sku'] = product['sku']
        updated['product_cost'] = product['cost']
    
    return updated


# ============================================================================
# ORDER ROUTES
# ============================================================================

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({}, {"_id": 0}).sort("order_date", -1).to_list(1000)
    for o in orders:
        if isinstance(o.get('order_date'), str):
            o['order_date'] = datetime.fromisoformat(o['order_date'])
    return orders

@api_router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(order_create: OrderCreate, current_user: User = Depends(get_current_user)):
    # Get customer
    customer = await db.customers.find_one({"id": order_create.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Build order items
    items = []
    subtotal = 0
    for item_data in order_create.items:
        product = await db.products.find_one({"id": item_data['product_id']}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        
        quantity = item_data['quantity']
        unit_price = product['price']
        total = quantity * unit_price
        
        items.append(OrderItem(
            product_id=product['id'],
            product_name=product['name'],
            quantity=quantity,
            unit_price=unit_price,
            total=total
        ))
        subtotal += total
        
        # Update inventory
        inv_result = await db.inventory.find_one_and_update(
            {"product_id": product['id']},
            {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}},
            return_document=True
        )
        if inv_result:
            # Update product stock status
            await update_product_stock_status(product['id'], inv_result['quantity'])
    
    order = Order(
        customer_id=customer['id'],
        customer_name=customer['name'],
        items=items,
        subtotal=subtotal,
        total=subtotal,
        status="completed",
        notes=order_create.notes
    )
    
    doc = order.model_dump()
    doc['order_date'] = doc['order_date'].isoformat()
    await db.orders.insert_one(doc)
    
    return order


# ============================================================================
# SUPPLIER ROUTES
# ============================================================================

@api_router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(current_user: User = Depends(get_current_user)):
    suppliers = await db.suppliers.find({}, {"_id": 0}).to_list(1000)
    for s in suppliers:
        if isinstance(s.get('created_at'), str):
            s['created_at'] = datetime.fromisoformat(s['created_at'])
    return suppliers

@api_router.post("/suppliers", response_model=Supplier, status_code=status.HTTP_201_CREATED)
async def create_supplier(supplier_create: SupplierCreate, current_user: User = Depends(get_current_user)):
    supplier = Supplier(**supplier_create.model_dump())
    doc = supplier.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.suppliers.insert_one(doc)
    return supplier

@api_router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(supplier_id: str, supplier_update: SupplierCreate, current_user: User = Depends(get_current_user)):
    result = await db.suppliers.update_one(
        {"id": supplier_id},
        {"$set": supplier_update.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Supplier(**updated)

@api_router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: str, current_user: User = Depends(get_current_user)):
    result = await db.suppliers.delete_one({"id": supplier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return None


# ============================================================================
# PURCHASE ROUTES
# ============================================================================

@api_router.get("/purchases", response_model=List[Purchase])
async def get_purchases(current_user: User = Depends(get_current_user)):
    purchases = await db.purchases.find({}, {"_id": 0}).sort("order_date", -1).to_list(1000)
    for p in purchases:
        if isinstance(p.get('order_date'), str):
            p['order_date'] = datetime.fromisoformat(p['order_date'])
        if p.get('received_date') and isinstance(p['received_date'], str):
            p['received_date'] = datetime.fromisoformat(p['received_date'])
    return purchases

@api_router.post("/purchases", response_model=Purchase, status_code=status.HTTP_201_CREATED)
async def create_purchase(purchase_create: PurchaseCreate, current_user: User = Depends(get_current_user)):
    # Get supplier
    supplier = await db.suppliers.find_one({"id": purchase_create.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Build purchase items
    items = []
    total = 0
    for item_data in purchase_create.items:
        product = await db.products.find_one({"id": item_data['product_id']}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        
        quantity = item_data['quantity']
        unit_cost = product['cost']
        item_total = quantity * unit_cost
        
        items.append(PurchaseItem(
            product_id=product['id'],
            product_name=product['name'],
            quantity=quantity,
            unit_cost=unit_cost,
            total=item_total
        ))
        total += item_total
    
    purchase = Purchase(
        supplier_id=supplier['id'],
        supplier_name=supplier['name'],
        items=items,
        total=total,
        status="pending",
        notes=purchase_create.notes
    )
    
    doc = purchase.model_dump()
    doc['order_date'] = doc['order_date'].isoformat()
    if doc.get('received_date'):
        doc['received_date'] = doc['received_date'].isoformat()
    await db.purchases.insert_one(doc)
    
    return purchase

@api_router.put("/purchases/{purchase_id}/receive", response_model=Purchase)
async def receive_purchase(purchase_id: str, current_user: User = Depends(get_current_user)):
    purchase = await db.purchases.find_one({"id": purchase_id}, {"_id": 0})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Update inventory for all items
    for item in purchase['items']:
        inv_result = await db.inventory.find_one_and_update(
            {"product_id": item['product_id']},
            {"$inc": {"quantity": item['quantity']}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}},
            return_document=True
        )
        if inv_result:
            # Update product stock status
            await update_product_stock_status(item['product_id'], inv_result['quantity'])
    
    # Update purchase status
    await db.purchases.update_one(
        {"id": purchase_id},
        {"$set": {"status": "received", "received_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated = await db.purchases.find_one({"id": purchase_id}, {"_id": 0})
    if isinstance(updated.get('order_date'), str):
        updated['order_date'] = datetime.fromisoformat(updated['order_date'])
    if updated.get('received_date') and isinstance(updated['received_date'], str):
        updated['received_date'] = datetime.fromisoformat(updated['received_date'])
    
    return Purchase(**updated)


# ============================================================================
# COST ROUTES
# ============================================================================

@api_router.get("/costs", response_model=List[Cost])
async def get_costs(current_user: User = Depends(get_current_user)):
    costs = await db.costs.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    for c in costs:
        if isinstance(c.get('date'), str):
            c['date'] = datetime.fromisoformat(c['date'])
    return costs

@api_router.post("/costs", response_model=Cost, status_code=status.HTTP_201_CREATED)
async def create_cost(cost_create: CostCreate, current_user: User = Depends(get_current_user)):
    cost = Cost(**cost_create.model_dump())
    doc = cost.model_dump()
    doc['date'] = doc['date'].isoformat()
    await db.costs.insert_one(doc)
    return cost

@api_router.delete("/costs/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost(cost_id: str, current_user: User = Depends(get_current_user)):
    result = await db.costs.delete_one({"id": cost_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cost not found")
    return None


# ============================================================================
# DASHBOARD & REPORTS
# ============================================================================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.isoformat()
    
    # Get today's orders
    today_orders = await db.orders.find({
        "order_date": {"$gte": today_str},
        "status": "completed"
    }, {"_id": 0}).to_list(1000)
    
    today_revenue = sum(order['total'] for order in today_orders)
    today_order_count = len(today_orders)
    
    # Calculate COGS for today
    today_cogs = 0
    for order in today_orders:
        for item in order['items']:
            product = await db.products.find_one({"id": item['product_id']}, {"_id": 0})
            if product:
                today_cogs += item['quantity'] * product['cost']
    
    today_profit = today_revenue - today_cogs
    
    # Average order value
    avg_order = today_revenue / today_order_count if today_order_count > 0 else 0
    
    # Inventory value
    inventory_items = await db.inventory.find({}, {"_id": 0}).to_list(1000)
    inventory_value = 0
    low_stock_count = 0
    
    for inv in inventory_items:
        product = await db.products.find_one({"id": inv['product_id']}, {"_id": 0})
        if product:
            inventory_value += inv['quantity'] * product['cost']
            if inv['quantity'] < inv.get('min_quantity', 80):
                low_stock_count += 1
    
    # Get inventory with product details for display
    inventory_display = []
    for inv in inventory_items[:4]:  # Top 4 for display
        product = await db.products.find_one({"id": inv['product_id']}, {"_id": 0})
        if product:
            inventory_display.append({
                "product_name": product['name'],
                "quantity": inv['quantity'],
                "color": product.get('color', 'omega')
            })
    
    return {
        "today": {
            "orders": today_order_count,
            "revenue": round(today_revenue, 2),
            "profit": round(today_profit, 2),
            "avg_order": round(avg_order, 2),
            "cogs": round(today_cogs, 2)
        },
        "inventory": {
            "total_value": round(inventory_value, 2),
            "low_stock_count": low_stock_count,
            "items": inventory_display
        }
    }

@api_router.get("/dashboard/monthly")
async def get_monthly_stats(current_user: User = Depends(get_current_user)):
    # Get current month start
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_str = month_start.isoformat()
    
    # Get month's orders
    month_orders = await db.orders.find({
        "order_date": {"$gte": month_start_str},
        "status": "completed"
    }, {"_id": 0}).to_list(1000)
    
    month_revenue = sum(order['total'] for order in month_orders)
    
    # Calculate COGS for month
    month_cogs = 0
    product_sales = {}
    
    for order in month_orders:
        for item in order['items']:
            product = await db.products.find_one({"id": item['product_id']}, {"_id": 0})
            if product:
                month_cogs += item['quantity'] * product['cost']
                
                # Track product sales
                if product['id'] not in product_sales:
                    product_sales[product['id']] = {
                        "name": product['name'],
                        "color": product.get('color', 'omega'),
                        "total": 0
                    }
                product_sales[product['id']]['total'] += item['total']
    
    # Get other costs for the month
    other_costs = await db.costs.find({
        "date": {"$gte": month_start_str}
    }, {"_id": 0}).to_list(1000)
    
    other_costs_total = sum(cost['amount'] for cost in other_costs)
    
    month_profit = month_revenue - month_cogs - other_costs_total
    
    # Get top products
    top_products = sorted(product_sales.values(), key=lambda x: x['total'], reverse=True)[:2]
    for product in top_products:
        product['percentage'] = round((product['total'] / month_revenue * 100) if month_revenue > 0 else 0)
    
    return {
        "revenue": round(month_revenue, 2),
        "cogs": round(month_cogs, 2),
        "other_costs": round(other_costs_total, 2),
        "profit": round(month_profit, 2),
        "top_products": top_products
    }


# ============================================================================
# SEED DATA ENDPOINT (for testing)
# ============================================================================

@api_router.post("/seed-data", status_code=status.HTTP_201_CREATED)
async def seed_data():
    """Populate database with ZenVit test data"""
    
    # Clear existing data
    await db.products.delete_many({})
    await db.inventory.delete_many({})
    await db.customers.delete_many({})
    await db.suppliers.delete_many({})
    await db.orders.delete_many({})
    await db.purchases.delete_many({})
    await db.costs.delete_many({})
    
    # Create suppliers first
    suppliers = [
        {
            "id": str(uuid.uuid4()),
            "name": "Nordic Supplements AS",
            "contact_person": "Per Olsen",
            "email": "ordre@nordicsupplements.no",
            "phone": "22334455",
            "address": "Industriveien 10, 0581 Oslo",
            "products_supplied": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "VitaImport Norge",
            "contact_person": "Anne Berg",
            "email": "salg@vitaimport.no",
            "phone": "55667788",
            "address": "Havnepromenaden 3, 5013 Bergen",
            "products_supplied": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    await db.suppliers.insert_many(suppliers)
    
    # Create products
    products = [
        {
            "id": str(uuid.uuid4()),
            "name": "D3 + K2 Premium",
            "description": "Vitamin D3 5000 IU + K2 MK-7 200 mcg",
            "category": "vitamin",
            "sku": "ZV-D3K2-001",
            "price": 299.0,
            "cost": 89.0,
            "min_stock": 100,
            "stock_status": "OK",
            "supplier_id": suppliers[0]['id'],
            "color": "d3",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Omega-3 Triglyceride",
            "description": "EPA 1000mg + DHA 500mg per serving",
            "category": "supplement",
            "sku": "ZV-OM3-001",
            "price": 349.0,
            "cost": 95.0,
            "min_stock": 150,
            "stock_status": "OK",
            "supplier_id": suppliers[0]['id'],
            "color": "omega",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Magnesium Glysinat 400mg",
            "description": "Høyt biotilgjengelig magnesium",
            "category": "mineral",
            "sku": "ZV-MAG-001",
            "price": 249.0,
            "cost": 72.0,
            "min_stock": 120,
            "stock_status": "OK",
            "supplier_id": suppliers[1]['id'],
            "color": "mag",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "C-vitamin + Sink",
            "description": "Vitamin C 1000mg + Sink 15mg",
            "category": "vitamin",
            "sku": "ZV-Cznc-001",
            "price": 199.0,
            "cost": 58.0,
            "min_stock": 100,
            "stock_status": "OK",
            "supplier_id": suppliers[1]['id'],
            "color": "csink",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.products.insert_many(products)
    
    # Update suppliers with product IDs
    await db.suppliers.update_one(
        {"id": suppliers[0]['id']},
        {"$set": {"products_supplied": [products[0]['id'], products[1]['id']]}}
    )
    await db.suppliers.update_one(
        {"id": suppliers[1]['id']},
        {"$set": {"products_supplied": [products[2]['id'], products[3]['id']]}}
    )
    
    # Create inventory
    inventory = [
        {"id": str(uuid.uuid4()), "product_id": products[0]['id'], "quantity": 312, "last_updated": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "product_id": products[1]['id'], "quantity": 284, "last_updated": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "product_id": products[2]['id'], "quantity": 215, "last_updated": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "product_id": products[3]['id'], "quantity": 198, "last_updated": datetime.now(timezone.utc).isoformat()},
    ]
    
    await db.inventory.insert_many(inventory)
    
    # Create customers
    customers = [
        {
            "id": str(uuid.uuid4()),
            "name": "Kari Nordmann",
            "email": "kari.nordmann@example.no",
            "phone": "91234567",
            "address": "Storgata 1",
            "city": "Oslo",
            "postal_code": "0150",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ola Hansen",
            "email": "ola.hansen@example.no",
            "phone": "98765432",
            "address": "Fjordveien 25",
            "city": "Bergen",
            "postal_code": "5003",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Liv Johansen",
            "email": "liv.johansen@example.no",
            "phone": "45678912",
            "address": "Skogsveien 42",
            "city": "Trondheim",
            "postal_code": "7020",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.customers.insert_many(customers)
    
    # Create some orders (today's orders)
    today = datetime.now(timezone.utc)
    orders = []
    
    for i in range(18):
        customer = customers[i % len(customers)]
        items = []
        
        # Random 1-3 items per order
        num_items = (i % 3) + 1
        subtotal = 0
        
        for j in range(num_items):
            product = products[j % len(products)]
            quantity = ((i + j) % 3) + 1
            unit_price = product['price']
            total = quantity * unit_price
            
            items.append({
                "product_id": product['id'],
                "product_name": product['name'],
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total
            })
            subtotal += total
        
        order = {
            "id": str(uuid.uuid4()),
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "items": items,
            "subtotal": subtotal,
            "total": subtotal,
            "status": "completed",
            "order_date": (today - timedelta(hours=i)).isoformat(),
            "notes": None
        }
        orders.append(order)
    
    await db.orders.insert_many(orders)
    
    # Create costs
    costs = [
        {
            "id": str(uuid.uuid4()),
            "category": "marketing",
            "description": "Facebook Ads - Januar",
            "amount": 8500.0,
            "date": datetime.now(timezone.utc).isoformat(),
            "recurring": True
        },
        {
            "id": str(uuid.uuid4()),
            "category": "shipping",
            "description": "Posten - Månedlig avtale",
            "amount": 6200.0,
            "date": datetime.now(timezone.utc).isoformat(),
            "recurring": True
        },
        {
            "id": str(uuid.uuid4()),
            "category": "software",
            "description": "Shopify abonnement",
            "amount": 3700.0,
            "date": datetime.now(timezone.utc).isoformat(),
            "recurring": True
        }
    ]
    
    await db.costs.insert_many(costs)
    
    return {"message": "Test data created successfully", "products": len(products), "customers": len(customers), "orders": len(orders)}


# ============================================================================
# INCLUDE ROUTER & MIDDLEWARE
# ============================================================================

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
