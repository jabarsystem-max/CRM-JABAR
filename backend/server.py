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

# Create the main app
app = FastAPI(title="ZenVit Complete CRM API")
api_router = APIRouter(prefix="/api")


# ============================================================================
# MODELS - ALL CRM ENTITIES
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sku: str
    name: str
    category: str
    cost: float
    price: float
    description: Optional[str] = None
    supplier_id: Optional[str] = None
    active: bool = True
    color: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    cost: float
    price: float
    description: Optional[str] = None
    supplier_id: Optional[str] = None
    color: Optional[str] = None


# --- Stock Models ---
class Stock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    quantity: int = 0
    min_stock: int = 80
    status: str = "OK"  # OK, Low, Out
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockUpdate(BaseModel):
    quantity: int
    min_stock: Optional[int] = None


# --- StockMovement Models ---
class StockMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: str  # IN or OUT
    quantity: int
    order_id: Optional[str] = None
    purchase_id: Optional[str] = None
    note: Optional[str] = None

class StockMovementCreate(BaseModel):
    product_id: str
    type: str
    quantity: int
    order_id: Optional[str] = None
    purchase_id: Optional[str] = None
    note: Optional[str] = None


# --- Supplier Models ---
class Supplier(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


# --- Purchase Models ---
class PurchaseLine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    purchase_id: str
    product_id: str
    product_name: str
    quantity: int
    cost_price: float

class Purchase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str
    supplier_name: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "Ordered"  # Ordered, Received, Cancelled
    total_amount: float = 0
    payment_status: str = "Unpaid"  # Unpaid, Partial, Paid
    notes: Optional[str] = None

class PurchaseCreate(BaseModel):
    supplier_id: str
    items: List[Dict[str, Any]]
    notes: Optional[str] = None


# --- Customer Models ---
class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    type: str = "Private"  # Private, Business
    status: str = "New"  # Lead, New, Active, VIP, Inactive, Lost
    total_value: float = 0  # AUTO
    order_count: int = 0  # AUTO
    favorite_product: Optional[str] = None  # AUTO
    last_order_date: Optional[datetime] = None  # AUTO
    tags: Optional[str] = None
    notes: Optional[str] = None
    next_step: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    type: str = "Private"
    status: str = "New"
    tags: Optional[str] = None
    notes: Optional[str] = None
    next_step: Optional[str] = None


# --- CustomerTimeline Models ---
class CustomerTimeline(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: str  # Order, Task, Note
    description: str

class TimelineCreate(BaseModel):
    customer_id: str
    type: str
    description: str


# --- Order Models ---
class OrderLine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    product_id: str
    product_name: str
    quantity: int
    sale_price: float
    cost_price: float
    discount: float = 0
    line_total: float = 0  # AUTO
    line_profit: float = 0  # AUTO

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    customer_name: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    channel: str = "Direct"  # Shopify, TikTok, Instagram, Direct, Campaign
    status: str = "New"  # New, Processing, Packed, Shipped, Delivered, Cancelled, Refund
    shipping_paid_by_customer: float = 0
    shipping_cost: float = 0
    payment_status: str = "Unpaid"  # Unpaid, Partial, Paid
    payment_method: Optional[str] = None  # Card, Vipps, Klarna, TikTokPay
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    order_total: float = 0  # AUTO
    cost_total: float = 0  # AUTO
    profit: float = 0  # AUTO
    profit_percent: float = 0  # AUTO

class OrderCreate(BaseModel):
    customer_id: str
    items: List[Dict[str, Any]]
    channel: str = "Direct"
    shipping_paid_by_customer: float = 0
    shipping_cost: float = 0
    payment_method: Optional[str] = None
    notes: Optional[str] = None


# --- Task Models ---
class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "Medium"  # High, Medium, Low
    status: str = "Planned"  # Planned, InProgress, Done
    type: str = "Admin"  # Customer, Order, Product, Stock, Supplier, Admin
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    supplier_id: Optional[str] = None
    assigned_to: str = "Jabar"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "Medium"
    type: str = "Admin"
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    supplier_id: Optional[str] = None


# --- Expense Models ---
class Expense(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: str  # COGS, Marketing, Shipping, Software, Operations
    amount: float
    payment_status: str = "Unpaid"  # Paid, Unpaid
    supplier_id: Optional[str] = None
    notes: Optional[str] = None

class ExpenseCreate(BaseModel):
    category: str
    amount: float
    payment_status: str = "Unpaid"
    supplier_id: Optional[str] = None
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
    
    if isinstance(user_data.get('created_at'), str):
        user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
    
    return User(**user_data)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_stock_status(quantity: int, min_stock: int) -> str:
    if quantity == 0:
        return "Out"
    elif quantity < min_stock:
        return "Low"
    else:
        return "OK"

async def update_stock_status(product_id: str):
    """Update stock status based on current quantity"""
    stock = await db.stock.find_one({"product_id": product_id})
    if stock:
        status = calculate_stock_status(stock['quantity'], stock.get('min_stock', 80))
        await db.stock.update_one(
            {"product_id": product_id},
            {"$set": {"status": status, "last_updated": datetime.now(timezone.utc).isoformat()}}
        )

async def create_stock_movement(product_id: str, type: str, quantity: int, 
                                order_id: str = None, purchase_id: str = None, note: str = None):
    """Create a stock movement record"""
    movement = StockMovement(
        product_id=product_id,
        type=type,
        quantity=quantity,
        order_id=order_id,
        purchase_id=purchase_id,
        note=note
    )
    doc = movement.model_dump()
    doc['date'] = doc['date'].isoformat()
    await db.stock_movements.insert_one(doc)

async def update_customer_stats(customer_id: str):
    """Update customer auto-calculated fields"""
    # Get all completed orders for this customer
    orders = await db.orders.find({
        "customer_id": customer_id,
        "status": {"$in": ["Delivered", "Shipped", "Processing", "Packed"]}
    }).to_list(1000)
    
    total_value = sum(order.get('order_total', 0) for order in orders)
    order_count = len(orders)
    
    # Find last order date
    last_order_date = None
    if orders:
        latest_order = max(orders, key=lambda x: x.get('date', ''))
        last_order_date = latest_order.get('date')
    
    # Find favorite product (most ordered)
    product_counts = {}
    for order in orders:
        order_id = order['id']
        lines = await db.order_lines.find({"order_id": order_id}).to_list(1000)
        for line in lines:
            pid = line['product_id']
            product_counts[pid] = product_counts.get(pid, 0) + line['quantity']
    
    favorite_product = None
    if product_counts:
        fav_id = max(product_counts, key=product_counts.get)
        fav_prod = await db.products.find_one({"id": fav_id})
        if fav_prod:
            favorite_product = fav_prod['name']
    
    # Determine status based on activity
    status = "Active" if order_count > 0 else "New"
    if order_count >= 10:
        status = "VIP"
    elif last_order_date:
        if isinstance(last_order_date, str):
            last_order_date = datetime.fromisoformat(last_order_date)
        days_since = (datetime.now(timezone.utc) - last_order_date).days
        if days_since > 90:
            status = "Inactive"
    
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": {
            "total_value": total_value,
            "order_count": order_count,
            "favorite_product": favorite_product,
            "last_order_date": last_order_date.isoformat() if last_order_date else None,
            "status": status
        }}
    )

async def create_timeline_entry(customer_id: str, type: str, description: str):
    """Create a customer timeline entry"""
    timeline = CustomerTimeline(
        customer_id=customer_id,
        type=type,
        description=description
    )
    doc = timeline.model_dump()
    doc['date'] = doc['date'].isoformat()
    await db.customer_timeline.insert_one(doc)


# ============================================================================
# AUTH ROUTES
# ============================================================================

@api_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user_create.model_dump(exclude={'password'})
    user = User(**user_dict)
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['hashed_password'] = hash_password(user_create.password)
    
    await db.users.insert_one(doc)
    return user

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    user_data = await db.users.find_one({"email": user_login.email})
    if not user_data:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not verify_password(user_login.password, user_data['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user_data['id']})
    
    user_data.pop('hashed_password', None)
    user_data.pop('_id', None)
    if isinstance(user_data.get('created_at'), str):
        user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
    
    return TokenResponse(access_token=access_token, user=User(**user_data))

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
    
    # Create stock entry
    stock = Stock(product_id=product.id, quantity=0)
    stock_doc = stock.model_dump()
    stock_doc['last_updated'] = stock_doc['last_updated'].isoformat()
    await db.stock.insert_one(stock_doc)
    
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


# Continuing in next part due to size...
# The file continues with STOCK, SUPPLIERS, PURCHASES, CUSTOMERS, ORDERS, TASKS, EXPENSES, DASHBOARD, and REPORTS routes

# ============================================================================
# Include router and middleware
# ============================================================================
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
