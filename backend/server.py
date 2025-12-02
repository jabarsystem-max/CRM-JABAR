from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
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
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import shutil
import aiofiles
import json


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

# Email settings
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@zenvit.no')
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'

# Create the main app
app = FastAPI(
    title="ZenVit Complete CRM API",
    description="Complete CRM system with products, customers, orders, and automation",
    version="1.0.0"
)
api_router = APIRouter(prefix="/api")


# Custom middleware to add CORS headers to static files
class StaticFilesCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add CORS headers for /uploads paths
        if request.url.path.startswith("/uploads"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            
            # Ensure correct Content-Type for images
            if request.url.path.endswith(".png"):
                response.headers["Content-Type"] = "image/png"
            elif request.url.path.endswith((".jpg", ".jpeg")):
                response.headers["Content-Type"] = "image/jpeg"
            elif request.url.path.endswith(".webp"):
                response.headers["Content-Type"] = "image/webp"
        
        return response


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True
    
    # Basic info
    sku: str
    name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    full_description: Optional[str] = None  # Markdown
    
    # Categorization
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    health_areas: Optional[List[str]] = []  # Tags: Immun, Søvn, Energi, etc.
    
    # Product details
    ean: Optional[str] = None  # Barcode
    packaging_type: Optional[str] = None  # flaske, glass, boks, pakke
    units_per_package: Optional[int] = 1
    weight_grams: Optional[float] = None
    
    # Pricing
    cost: float
    price: float
    min_stock: int = 80
    
    # Relations
    supplier_id: Optional[str] = None
    
    # UI/Display
    color: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ProductCreate(BaseModel):
    # Basic info
    name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    full_description: Optional[str] = None
    
    # Categorization
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    health_areas: Optional[List[str]] = []
    
    # Product details
    ean: Optional[str] = None
    packaging_type: Optional[str] = None
    units_per_package: Optional[int] = 1
    weight_grams: Optional[float] = None
    
    # Pricing (required)
    cost: float
    price: float
    min_stock: int = 80
    
    # Relations
    supplier_id: Optional[str] = None
    
    # UI/Display
    color: Optional[str] = None
    image_url: Optional[str] = None


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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: str  # "IN", "OUT", "ADJUST"
    change: int  # Positive or negative integer
    source: str  # "PURCHASE", "ORDER", "MANUAL"
    source_id: Optional[str] = None  # ID of purchase/order/adjustment
    note: Optional[str] = None
    
    # Legacy fields for backward compatibility
    date: Optional[datetime] = None
    quantity: Optional[int] = None
    order_id: Optional[str] = None
    purchase_id: Optional[str] = None

class StockMovementCreate(BaseModel):
    product_id: str
    type: str
    quantity: int
    order_id: Optional[str] = None
    purchase_id: Optional[str] = None
    note: Optional[str] = None


# --- Stock Adjustment Models ---
class StockAdjustment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    change: int  # Positive or negative
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class StockAdjustmentCreate(BaseModel):
    product_id: str
    change: int
    reason: str


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
    status: str = "DRAFT"  # DRAFT, ORDERED, RECEIVED, CANCELLED
    total_amount: float = 0
    payment_status: str = "Unpaid"  # Unpaid, Partial, Paid
    notes: Optional[str] = None
    stock_applied: bool = False  # Track if stock has been updated
    received_at: Optional[datetime] = None  # When purchase was received

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
    status: str = "NEW"  # DRAFT, NEW, PAID, SHIPPED, COMPLETED, CANCELLED
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
    stock_applied: bool = False  # Track if stock has been reduced
    completed_at: Optional[datetime] = None  # When order was completed

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
    """Calculate stock status based on quantity and min_stock threshold"""
    if quantity == 0:
        return "Out"
    elif quantity < min_stock:
        return "Low"
    else:
        return "OK"

async def generate_sku(category: str) -> str:
    """Generate automatic SKU in format: ZV-<CAT>-<number>"""
    # Category code mapping
    category_codes = {
        'vitamin': 'VIT',
        'mineral': 'MIN',
        'supplement': 'SUP',
        'omega': 'OME',
        'probiotic': 'PRO',
        'herbal': 'HRB',
        'protein': 'PRT',
        'other': 'OTH'
    }
    
    cat_code = category_codes.get(category.lower(), 'PRD')
    
    # Find highest existing number for this category
    existing_products = await db.products.find(
        {"sku": {"$regex": f"^ZV-{cat_code}-"}},
        {"_id": 0, "sku": 1}
    ).to_list(1000)
    
    if not existing_products:
        next_number = 1
    else:
        # Extract numbers from SKUs
        numbers = []
        for prod in existing_products:
            try:
                num = int(prod['sku'].split('-')[-1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue
        next_number = max(numbers) + 1 if numbers else 1
    
    return f"ZV-{cat_code}-{next_number:03d}"

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
    }, {"_id": 0}).to_list(1000)
    
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
        lines = await db.order_lines.find({"order_id": order_id}, {"_id": 0}).to_list(1000)
        for line in lines:
            pid = line['product_id']
            product_counts[pid] = product_counts.get(pid, 0) + line['quantity']
    
    favorite_product = None
    if product_counts:
        fav_id = max(product_counts, key=product_counts.get)
        fav_prod = await db.products.find_one({"id": fav_id}, {"_id": 0})
        if fav_prod:
            favorite_product = fav_prod['name']
    
    # Determine status based on activity
    status = "Active" if order_count > 0 else "New"
    last_order_date_str = None
    if order_count >= 10:
        status = "VIP"
    elif last_order_date:
        if isinstance(last_order_date, str):
            last_order_date_str = last_order_date
            last_order_date = datetime.fromisoformat(last_order_date)
        else:
            last_order_date_str = last_order_date.isoformat()
        
        days_since = (datetime.now(timezone.utc) - last_order_date).days
        if days_since > 90:
            status = "Inactive"
    
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": {
            "total_value": total_value,
            "order_count": order_count,
            "favorite_product": favorite_product,
            "last_order_date": last_order_date_str,
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
# AUTOMATION FUNCTIONS
# ============================================================================

async def check_and_create_low_stock_task(product_id: str):
    """Automation: Create task when stock is low"""
    stock = await db.stock.find_one({"product_id": product_id}, {"_id": 0})
    if not stock or stock.get('status') not in ['Low', 'Out']:
        return
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return
    
    # Check if task already exists for this product
    existing_task = await db.tasks.find_one({
        "product_id": product_id,
        "type": "Stock",
        "status": {"$ne": "Done"}
    })
    
    if existing_task:
        return  # Task already exists
    
    # Create new task
    task_title = f"Bestill mer {product['name']}"
    task_description = f"Lageret er {stock['status'].lower()} ({stock['quantity']} stk, min: {stock.get('min_stock', 80)} stk)"
    
    task = Task(
        title=task_title,
        description=task_description,
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
        priority="High" if stock['status'] == 'Out' else "Medium",
        status="Planned",
        type="Stock",
        product_id=product_id,
        assigned_to="Admin"
    )
    
    doc = task.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['due_date'] = doc['due_date'].isoformat()
    await db.tasks.insert_one(doc)
    
    # Send email notification
    await send_low_stock_notification(product['name'], stock['quantity'], stock.get('min_stock', 80))

async def auto_update_customer_on_order(customer_id: str, order_id: str):
    """Automation: Update customer stats and create timeline entry when order is created"""
    await update_customer_stats(customer_id)
    
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if order:
        await create_timeline_entry(
            customer_id,
            "Order",
            f"Ordre opprettet: {order_id[:8]} - {round(order.get('order_total', 0))} kr"
        )

async def auto_complete_task_on_stock_replenishment(product_id: str):
    """Automation: Mark stock tasks as done when stock is replenished"""
    stock = await db.stock.find_one({"product_id": product_id}, {"_id": 0})
    if not stock or stock.get('status') != 'OK':
        return
    
    # Find and complete related tasks
    tasks = await db.tasks.find({
        "product_id": product_id,
        "type": "Stock",
        "status": {"$ne": "Done"}
    }, {"_id": 0}).to_list(100)
    
    for task in tasks:
        await db.tasks.update_one(
            {"id": task['id']},
            {"$set": {"status": "Done"}}
        )


# ============================================================================
# EMAIL NOTIFICATION FUNCTIONS
# ============================================================================

async def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Send email notification"""
    if not EMAIL_ENABLED or not SMTP_USER or not SMTP_PASSWORD:
        logging.info(f"Email disabled or not configured. Would send: {subject} to {to_email}")
        return False
    
    try:
        message = MIMEMultipart('alternative')
        message['From'] = EMAIL_FROM
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add plain text version
        text_part = MIMEText(body, 'plain', 'utf-8')
        message.attach(text_part)
        
        # Add HTML version if provided
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True
        )
        logging.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

async def send_low_stock_notification(product_name: str, quantity: int, min_stock: int, admin_email: str = "admin@zenvit.no"):
    """Send notification when stock is low"""
    subject = f"⚠️ Lavt lagernivå: {product_name}"
    
    body = f"""
Hei,

Lagernivået for {product_name} er lavt.

Detaljer:
- Produkt: {product_name}
- Nåværende beholdning: {quantity} stk
- Minimum beholdning: {min_stock} stk
- Status: {'Tomt lager' if quantity == 0 else 'Lavt lager'}

Vennligst bestill mer fra leverandør så snart som mulig.

Med vennlig hilsen,
ZenVit CRM System
    """
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; padding: 20px; border-radius: 8px; }}
        .content {{ background: #f9fafb; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #dc2626; }}
        .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        .label {{ font-weight: 600; color: #7b8794; }}
        .value {{ color: #1e2a32; }}
        .footer {{ text-align: center; color: #7b8794; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⚠️ Varsel: Lavt lagernivå</h2>
        </div>
        <div class="content">
            <p>Hei,</p>
            <p>Lagernivået for <strong>{product_name}</strong> er lavt og krever handling.</p>
            
            <div class="details">
                <div class="detail-row">
                    <span class="label">Produkt:</span>
                    <span class="value">{product_name}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Nåværende beholdning:</span>
                    <span class="value" style="color: #dc2626; font-weight: 600;">{quantity} stk</span>
                </div>
                <div class="detail-row">
                    <span class="label">Minimum beholdning:</span>
                    <span class="value">{min_stock} stk</span>
                </div>
                <div class="detail-row">
                    <span class="label">Status:</span>
                    <span class="value" style="color: #dc2626; font-weight: 600;">{'🚫 Tomt lager' if quantity == 0 else '⚠️ Lavt lager'}</span>
                </div>
            </div>
            
            <p>Vennligst bestill mer fra leverandør så snart som mulig.</p>
        </div>
        <div class="footer">
            <p>Dette er en automatisk e-post fra ZenVit CRM System</p>
        </div>
    </div>
</body>
</html>
    """
    
    await send_email(admin_email, subject, body, html_body)

async def send_new_order_notification(order_id: str, customer_name: str, total: float, admin_email: str = "admin@zenvit.no"):
    """Send notification when new order is created"""
    subject = f"🛒 Ny ordre mottatt: {order_id[:8]}"
    
    body = f"""
Hei,

En ny ordre har blitt opprettet i systemet.

Detaljer:
- Ordre-ID: {order_id}
- Kunde: {customer_name}
- Totalt: {round(total)} kr
- Dato: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}

Logg inn på CRM-systemet for mer informasjon.

Med vennlig hilsen,
ZenVit CRM System
    """
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px; border-radius: 8px; }}
        .content {{ background: #f9fafb; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #10b981; }}
        .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        .label {{ font-weight: 600; color: #7b8794; }}
        .value {{ color: #1e2a32; }}
        .footer {{ text-align: center; color: #7b8794; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🛒 Ny ordre mottatt</h2>
        </div>
        <div class="content">
            <p>Hei,</p>
            <p>En ny ordre har blitt opprettet i systemet.</p>
            
            <div class="details">
                <div class="detail-row">
                    <span class="label">Ordre-ID:</span>
                    <span class="value">{order_id}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Kunde:</span>
                    <span class="value">{customer_name}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Totalt:</span>
                    <span class="value" style="color: #10b981; font-weight: 600;">{round(total)} kr</span>
                </div>
                <div class="detail-row">
                    <span class="label">Dato:</span>
                    <span class="value">{datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}</span>
                </div>
            </div>
            
            <p>Logg inn på CRM-systemet for å se fullstendige ordredetaljer.</p>
        </div>
        <div class="footer">
            <p>Dette er en automatisk e-post fra ZenVit CRM System</p>
        </div>
    </div>
</body>
</html>
    """
    
    await send_email(admin_email, subject, body, html_body)

async def send_task_deadline_notification(task_title: str, due_date: str, priority: str, admin_email: str = "admin@zenvit.no"):
    """Send notification for upcoming task deadline"""
    subject = f"⏰ Oppgavefrist: {task_title}"
    
    body = f"""
Hei,

Du har en oppgave som nærmer seg fristen.

Detaljer:
- Oppgave: {task_title}
- Frist: {due_date}
- Prioritet: {priority}

Vennligst fullfør oppgaven så snart som mulig.

Med vennlig hilsen,
ZenVit CRM System
    """
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 20px; border-radius: 8px; }}
        .content {{ background: #f9fafb; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #f59e0b; }}
        .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        .label {{ font-weight: 600; color: #7b8794; }}
        .value {{ color: #1e2a32; }}
        .footer {{ text-align: center; color: #7b8794; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⏰ Påminnelse: Oppgavefrist</h2>
        </div>
        <div class="content">
            <p>Hei,</p>
            <p>Du har en oppgave som nærmer seg fristen.</p>
            
            <div class="details">
                <div class="detail-row">
                    <span class="label">Oppgave:</span>
                    <span class="value">{task_title}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Frist:</span>
                    <span class="value" style="color: #f59e0b; font-weight: 600;">{due_date}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Prioritet:</span>
                    <span class="value">{priority}</span>
                </div>
            </div>
            
            <p>Vennligst fullfør oppgaven så snart som mulig.</p>
        </div>
        <div class="footer">
            <p>Dette er en automatisk e-post fra ZenVit CRM System</p>
        </div>
    </div>
</body>
</html>
    """
    
    await send_email(admin_email, subject, body, html_body)


# ============================================================================
# HEALTH CHECK & SYSTEM STATUS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        await db.command('ping')
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "healthy",
            "database": db_status,
            "email": "configured" if EMAIL_ENABLED else "disabled"
        }
    }

@api_router.get("/system/stats")
async def system_stats(current_user: User = Depends(get_current_user)):
    """Get system statistics for admin"""
    stats = {
        "users": await db.users.count_documents({}),
        "products": await db.products.count_documents({}),
        "customers": await db.customers.count_documents({}),
        "orders": await db.orders.count_documents({}),
        "tasks": await db.tasks.count_documents({}),
        "purchases": await db.purchases.count_documents({}),
        "expenses": await db.expenses.count_documents({}),
        "stock_items": await db.stock.count_documents({}),
        "low_stock": await db.stock.count_documents({"status": {"$in": ["Low", "Out"]}}),
        "database_name": os.environ.get('DB_NAME', 'unknown'),
        "version": "1.0.0"
    }
    return stats


# ============================================================================
# AUTH ROUTES
# ============================================================================

@api_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    existing_user = await db.users.find_one({"email": user_create.email}, {"_id": 0})
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
    user_data = await db.users.find_one({"email": user_login.email}, {"_id": 0})
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

@api_router.get("/products")
async def get_products(current_user: User = Depends(get_current_user)):
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    
    # Enrich products with stock information
    for p in products:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
        
        # Get stock information for this product
        stock = await db.stock.find_one({"product_id": p['id']}, {"_id": 0})
        if stock:
            p['current_stock'] = stock.get('quantity', 0)
            p['stock_status'] = stock.get('status', 'Unknown')
        else:
            p['current_stock'] = 0
            p['stock_status'] = 'Out'
    
    return products

@api_router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product_create: ProductCreate, current_user: User = Depends(get_current_user)):
    # Validate required fields
    if len(product_create.name) < 2:
        raise HTTPException(status_code=400, detail="Product name must be at least 2 characters")
    
    if product_create.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    
    if product_create.cost < 0:
        raise HTTPException(status_code=400, detail="Cost cannot be negative")
    
    if product_create.min_stock < 0:
        raise HTTPException(status_code=400, detail="Minimum stock must be positive")
    
    # Validate EAN if provided
    if product_create.ean and not product_create.ean.isdigit():
        raise HTTPException(status_code=400, detail="EAN must contain only digits")
    
    # Generate SKU automatically
    sku = await generate_sku(product_create.category)
    
    # Create product with generated SKU
    product_data = product_create.model_dump()
    product_data['sku'] = sku
    product = Product(**product_data)
    
    doc = product.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.products.insert_one(doc)
    
    # Create stock entry with min_stock from product
    stock = Stock(product_id=product.id, quantity=0, min_stock=product_create.min_stock)
    stock_doc = stock.model_dump()
    stock_doc['last_updated'] = stock_doc['last_updated'].isoformat()
    await db.stock.insert_one(stock_doc)
    
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: ProductCreate, current_user: User = Depends(get_current_user)):
    # Validate fields
    if len(product_update.name) < 2:
        raise HTTPException(status_code=400, detail="Product name must be at least 2 characters")
    
    if product_update.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    
    if product_update.cost < 0:
        raise HTTPException(status_code=400, detail="Cost cannot be negative")
    
    if product_update.min_stock < 0:
        raise HTTPException(status_code=400, detail="Minimum stock must be positive")
    
    if product_update.ean and not product_update.ean.isdigit():
        raise HTTPException(status_code=400, detail="EAN must contain only digits")
    
    # Get current product to preserve SKU
    current_product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not current_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Preserve the existing SKU (don't allow changing it)
    update_data = product_update.model_dump()
    update_data['sku'] = current_product['sku']
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
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


@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload a product image and return the URL"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("/app/backend/uploads/products")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Return the relative URL
        image_url = f"/uploads/products/{unique_filename}"
        return {"image_url": image_url, "message": "Image uploaded successfully"}
    
    except Exception as e:
        logging.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


# Continuing in next part due to size...
# The file continues with STOCK, SUPPLIERS, PURCHASES, CUSTOMERS, ORDERS, TASKS, EXPENSES, DASHBOARD, and REPORTS routes

# ============================================================================
# Include router and middleware (moved to end after all routes are defined)
# ============================================================================
# app.include_router(api_router)  # Moved to end of file


# ============================================================================
# STOCK ROUTES
# ============================================================================

@api_router.get("/stock", response_model=List[Dict[str, Any]])
async def get_stock(current_user: User = Depends(get_current_user)):
    stock_items = await db.stock.find({}, {"_id": 0}).to_list(1000)
    
    for item in stock_items:
        if isinstance(item.get('last_updated'), str):
            item['last_updated'] = datetime.fromisoformat(item['last_updated'])
        
        product = await db.products.find_one({"id": item['product_id']}, {"_id": 0})
        if product:
            item['product_name'] = product['name']
            item['product_sku'] = product['sku']
            item['product_cost'] = product['cost']
            item['product_color'] = product.get('color')
    
    return stock_items

@api_router.put("/stock/{product_id}", response_model=Dict[str, Any])
async def update_stock(product_id: str, stock_update: StockUpdate, current_user: User = Depends(get_current_user)):
    update_data = {"quantity": stock_update.quantity, "last_updated": datetime.now(timezone.utc).isoformat()}
    if stock_update.min_stock is not None:
        update_data["min_stock"] = stock_update.min_stock
    
    # Calculate new status
    status = calculate_stock_status(stock_update.quantity, stock_update.min_stock or 80)
    update_data["status"] = status
    
    result = await db.stock.update_one(
        {"product_id": product_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Create stock movement
    await create_stock_movement(product_id, "IN", stock_update.quantity, note="Manual adjustment")
    
    updated = await db.stock.find_one({"product_id": product_id}, {"_id": 0})
    if isinstance(updated.get('last_updated'), str):
        updated['last_updated'] = datetime.fromisoformat(updated['last_updated'])
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if product:
        updated['product_name'] = product['name']
        updated['product_sku'] = product['sku']
        updated['product_cost'] = product['cost']
    
    return updated

@api_router.post("/stock/adjust")
async def adjust_stock(product_id: str, adjustment: int, note: str = "Manual adjustment", current_user: User = Depends(get_current_user)):
    """Adjust stock quantity by a positive or negative amount"""
    # Get current stock
    stock = await db.stock.find_one({"product_id": product_id}, {"_id": 0})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Calculate new quantity
    current_qty = stock['quantity']
    new_qty = current_qty + adjustment
    
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Adjustment would result in negative stock")
    
    # Update stock
    await db.stock.update_one(
        {"product_id": product_id},
        {"$inc": {"quantity": adjustment}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update status
    await update_stock_status(product_id)
    
    # Create stock movement
    movement_type = "IN" if adjustment > 0 else "OUT"
    await create_stock_movement(product_id, movement_type, abs(adjustment), note=note)
    
    # Get updated stock
    updated = await db.stock.find_one({"product_id": product_id}, {"_id": 0})
    if isinstance(updated.get('last_updated'), str):
        updated['last_updated'] = datetime.fromisoformat(updated['last_updated'])
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if product:
        updated['product_name'] = product['name']
        updated['product_sku'] = product['sku']
    
    return {
        "message": f"Stock adjusted by {adjustment:+d}",
        "previous_quantity": current_qty,
        "new_quantity": new_qty,
        "stock": updated
    }


# ============================================================================
# STOCK MOVEMENTS ROUTES
# ============================================================================

@api_router.get("/stock-movements", response_model=List[Dict[str, Any]])
async def get_stock_movements(product_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"product_id": product_id} if product_id else {}
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    for mov in movements:
        if isinstance(mov.get('date'), str):
            mov['date'] = datetime.fromisoformat(mov['date'])
        
        product = await db.products.find_one({"id": mov['product_id']}, {"_id": 0})
        if product:
            mov['product_name'] = product['name']
    
    return movements

@api_router.get("/stock/movements", response_model=List[Dict[str, Any]])
async def get_stock_movements_alt(product_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Alias endpoint for stock movements (for consistency with /stock/adjust)"""
    return await get_stock_movements(product_id, current_user)

@api_router.post("/stock-movements", response_model=StockMovement, status_code=status.HTTP_201_CREATED)
async def create_movement(movement_create: StockMovementCreate, current_user: User = Depends(get_current_user)):
    await create_stock_movement(
        movement_create.product_id,
        movement_create.type,
        movement_create.quantity,
        movement_create.order_id,
        movement_create.purchase_id,
        movement_create.note
    )
    
    # Update stock
    multiplier = 1 if movement_create.type == "IN" else -1
    await db.stock.update_one(
        {"product_id": movement_create.product_id},
        {"$inc": {"quantity": multiplier * movement_create.quantity}}
    )
    await update_stock_status(movement_create.product_id)
    
    return StockMovement(**movement_create.model_dump())


# ============================================================================
# STOCK ADJUSTMENT ROUTES
# ============================================================================

@api_router.post("/stock/adjust", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def adjust_stock(adjustment: StockAdjustmentCreate, current_user: User = Depends(get_current_user)):
    """
    Manually adjust stock quantity (positive or negative).
    Used for corrections, damages, losses, etc.
    """
    # Get current stock
    stock = await db.stock.find_one({"product_id": adjustment.product_id}, {"_id": 0})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock record not found for this product")
    
    # Calculate new quantity
    new_quantity = stock['quantity'] + adjustment.change
    
    # Validate: quantity cannot go below 0
    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot adjust stock. Would result in negative quantity ({new_quantity}). Current: {stock['quantity']}, Change: {adjustment.change}"
        )
    
    # Create adjustment record
    adjustment_record = {
        "id": str(uuid.uuid4()),
        "product_id": adjustment.product_id,
        "change": adjustment.change,
        "reason": adjustment.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("email", "unknown")
    }
    await db.stock_adjustments.insert_one(adjustment_record)
    
    # Update stock quantity
    await db.stock.update_one(
        {"product_id": adjustment.product_id},
        {
            "$inc": {"quantity": adjustment.change},
            "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Update stock status
    await update_stock_status(adjustment.product_id)
    
    # Create StockMovement
    movement = {
        "id": str(uuid.uuid4()),
        "product_id": adjustment.product_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "ADJUST",
        "change": adjustment.change,
        "source": "MANUAL",
        "source_id": adjustment_record['id'],
        "note": f"Lagerjustering: {adjustment.reason}"
    }
    await db.stock_movements.insert_one(movement)
    
    # Get updated stock
    updated_stock = await db.stock.find_one({"product_id": adjustment.product_id}, {"_id": 0})
    
    # Get product info
    product = await db.products.find_one({"id": adjustment.product_id}, {"_id": 0})
    
    return {
        "message": "Stock adjusted successfully",
        "adjustment_id": adjustment_record['id'],
        "product_name": product.get('name', 'Unknown') if product else 'Unknown',
        "previous_quantity": stock['quantity'],
        "change": adjustment.change,
        "new_quantity": updated_stock['quantity'],
        "reason": adjustment.reason
    }


@api_router.get("/stock/adjustments", response_model=List[Dict[str, Any]])
async def get_stock_adjustments(
    product_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get stock adjustment history"""
    query = {"product_id": product_id} if product_id else {}
    adjustments = await db.stock_adjustments.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    for adj in adjustments:
        if isinstance(adj.get('created_at'), str):
            adj['created_at'] = datetime.fromisoformat(adj['created_at'])
        
        # Add product info
        product = await db.products.find_one({"id": adj['product_id']}, {"_id": 0})
        if product:
            adj['product_name'] = product['name']
            adj['product_sku'] = product['sku']
    
    return adjustments


# ============================================================================
# LOW STOCK ROUTES  
# ============================================================================

@api_router.get("/stock/low", response_model=List[Dict[str, Any]])
async def get_low_stock_products(current_user: User = Depends(get_current_user)):
    """
    Get all products where quantity <= min_stock.
    These products should be reordered soon.
    """
    # Get all stock records
    stock_items = await db.stock.find({}, {"_id": 0}).to_list(1000)
    
    low_stock = []
    for item in stock_items:
        # Check if quantity <= min_stock
        if item['quantity'] <= item.get('min_stock', 80):
            # Get product details
            product = await db.products.find_one({"id": item['product_id']}, {"_id": 0})
            if product:
                low_stock.append({
                    "product_id": item['product_id'],
                    "product_name": product['name'],
                    "product_sku": product['sku'],
                    "current_quantity": item['quantity'],
                    "min_stock": item.get('min_stock', 80),
                    "deficit": item.get('min_stock', 80) - item['quantity'],
                    "status": "critical" if item['quantity'] == 0 else "low",
                    "product_cost": product.get('cost', 0),
                    "product_price": product.get('price', 0)
                })
    
    # Sort by deficit (most critical first)
    low_stock.sort(key=lambda x: x['deficit'], reverse=True)
    
    return low_stock


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

@api_router.get("/purchases", response_model=List[Dict[str, Any]])
async def get_purchases(current_user: User = Depends(get_current_user)):
    purchases = await db.purchases.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    
    for p in purchases:
        if isinstance(p.get('date'), str):
            p['date'] = datetime.fromisoformat(p['date'])
        
        # Get purchase lines
        lines = await db.purchase_lines.find({"purchase_id": p['id']}, {"_id": 0}).to_list(1000)
        p['lines'] = lines
    
    return purchases

@api_router.post("/purchases", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_purchase(purchase_create: PurchaseCreate, current_user: User = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": purchase_create.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    purchase = Purchase(
        supplier_id=supplier['id'],
        supplier_name=supplier['name'],
        notes=purchase_create.notes
    )
    
    # Create purchase lines
    total_amount = 0
    lines = []
    
    for item_data in purchase_create.items:
        product = await db.products.find_one({"id": item_data['product_id']}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        
        quantity = item_data['quantity']
        cost_price = product['cost']
        
        line = PurchaseLine(
            purchase_id=purchase.id,
            product_id=product['id'],
            product_name=product['name'],
            quantity=quantity,
            cost_price=cost_price
        )
        lines.append(line.model_dump())
        total_amount += quantity * cost_price
    
    purchase.total_amount = total_amount
    
    # Save purchase
    purchase_doc = purchase.model_dump()
    purchase_doc['date'] = purchase_doc['date'].isoformat()
    await db.purchases.insert_one(purchase_doc)
    
    # Save lines (make a copy to avoid modifying the original)
    lines_to_save = [line.copy() for line in lines]
    await db.purchase_lines.insert_many(lines_to_save)
    
    # Remove MongoDB's _id field if it exists to prevent BSON serialization error
    purchase_doc.pop('_id', None)
    
    return {**purchase_doc, "lines": lines}

@api_router.put("/purchases/{purchase_id}/receive", response_model=Dict[str, Any])
async def receive_purchase(purchase_id: str, current_user: User = Depends(get_current_user)):
    purchase = await db.purchases.find_one({"id": purchase_id}, {"_id": 0})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # CRITICAL: Check if stock has already been applied
    if purchase.get('stock_applied', False):
        raise HTTPException(
            status_code=400, 
            detail="Stock has already been applied for this purchase. Cannot receive twice."
        )
    
    # Get purchase lines
    lines = await db.purchase_lines.find({"purchase_id": purchase_id}, {"_id": 0}).to_list(1000)
    
    if not lines:
        raise HTTPException(status_code=400, detail="No items in purchase")
    
    # Apply stock changes atomically for all items
    for line in lines:
        # Update stock quantity
        stock = await db.stock.find_one({"product_id": line['product_id']}, {"_id": 0})
        if not stock:
            # Create stock entry if it doesn't exist
            new_stock = {
                "id": str(uuid.uuid4()),
                "product_id": line['product_id'],
                "quantity": line['quantity'],
                "min_stock": 80,
                "status": "OK",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.stock.insert_one(new_stock)
        else:
            # Increment existing stock
            await db.stock.update_one(
                {"product_id": line['product_id']},
                {
                    "$inc": {"quantity": line['quantity']},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
                }
            )
        
        # Update stock status
        await update_stock_status(line['product_id'])
        
        # Create StockMovement with new structure
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": line['product_id'],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "IN",
            "change": line['quantity'],  # Positive number
            "source": "PURCHASE",
            "source_id": purchase_id,
            "note": f"Innkjøp mottatt: {line['product_name']}"
        }
        await db.stock_movements.insert_one(movement)
        
        # AUTOMATION: Complete stock tasks when replenished
        await auto_complete_task_on_stock_replenishment(line['product_id'])
    
    # Update purchase status and mark stock as applied
    await db.purchases.update_one(
        {"id": purchase_id},
        {
            "$set": {
                "status": "RECEIVED",
                "stock_applied": True,
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    updated = await db.purchases.find_one({"id": purchase_id}, {"_id": 0})
    if isinstance(updated.get('date'), str):
        updated['date'] = datetime.fromisoformat(updated['date'])
    if updated.get('received_at') and isinstance(updated['received_at'], str):
        updated['received_at'] = datetime.fromisoformat(updated['received_at'])
    
    updated['lines'] = lines
    return updated


# ============================================================================
# CUSTOMER ROUTES
# ============================================================================

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(current_user: User = Depends(get_current_user)):
    customers = await db.customers.find({}, {"_id": 0}).to_list(1000)
    for c in customers:
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
        if c.get('last_order_date') and isinstance(c['last_order_date'], str):
            c['last_order_date'] = datetime.fromisoformat(c['last_order_date'])
    return customers

@api_router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(customer_create: CustomerCreate, current_user: User = Depends(get_current_user)):
    customer = Customer(**customer_create.model_dump())
    doc = customer.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('last_order_date'):
        doc['last_order_date'] = doc['last_order_date'].isoformat()
    await db.customers.insert_one(doc)
    
    # Create timeline entry
    await create_timeline_entry(customer.id, "Note", f"Customer created: {customer.name}")
    
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
    if updated.get('last_order_date') and isinstance(updated['last_order_date'], str):
        updated['last_order_date'] = datetime.fromisoformat(updated['last_order_date'])
    
    return Customer(**updated)

@api_router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str, current_user: User = Depends(get_current_user)):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None

@api_router.get("/customers/{customer_id}/timeline", response_model=List[CustomerTimeline])
async def get_customer_timeline(customer_id: str, current_user: User = Depends(get_current_user)):
    timeline = await db.customer_timeline.find({"customer_id": customer_id}, {"_id": 0}).sort("date", -1).to_list(1000)
    for t in timeline:
        if isinstance(t.get('date'), str):
            t['date'] = datetime.fromisoformat(t['date'])
    return timeline


# ============================================================================
# ORDER ROUTES
# ============================================================================

@api_router.get("/orders", response_model=List[Dict[str, Any]])
async def get_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    
    for o in orders:
        if isinstance(o.get('date'), str):
            o['date'] = datetime.fromisoformat(o['date'])
        if o.get('payment_date') and isinstance(o['payment_date'], str):
            o['payment_date'] = datetime.fromisoformat(o['payment_date'])
        
        # Get order lines
        lines = await db.order_lines.find({"order_id": o['id']}, {"_id": 0}).to_list(1000)
        o['lines'] = lines
    
    return orders

@api_router.post("/orders", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_order(order_create: OrderCreate, current_user: User = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": order_create.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    order = Order(
        customer_id=customer['id'],
        customer_name=customer['name'],
        channel=order_create.channel,
        shipping_paid_by_customer=order_create.shipping_paid_by_customer,
        shipping_cost=order_create.shipping_cost,
        payment_method=order_create.payment_method,
        notes=order_create.notes
    )
    
    # Create order lines and calculate totals
    order_total = 0
    cost_total = 0
    lines = []
    
    for item_data in order_create.items:
        product = await db.products.find_one({"id": item_data['product_id']}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        
        quantity = item_data['quantity']
        sale_price = item_data.get('sale_price', product['price'])
        discount = item_data.get('discount', 0)
        
        line_total = (sale_price * quantity) - discount
        line_profit = line_total - (product['cost'] * quantity)
        
        line = OrderLine(
            order_id=order.id,
            product_id=product['id'],
            product_name=product['name'],
            quantity=quantity,
            sale_price=sale_price,
            cost_price=product['cost'],
            discount=discount,
            line_total=line_total,
            line_profit=line_profit
        )
        lines.append(line.model_dump())
        
        order_total += line_total
        cost_total += product['cost'] * quantity
        
        # Update stock
        await db.stock.update_one(
            {"product_id": product['id']},
            {"$inc": {"quantity": -quantity}}
        )
        await update_stock_status(product['id'])
        await create_stock_movement(product['id'], "OUT", quantity, order_id=order.id, note="Order created")
        
        # AUTOMATION: Check if stock is low and create task
        await check_and_create_low_stock_task(product['id'])
    
    # Calculate profit
    order_total += order.shipping_paid_by_customer
    cost_total += order.shipping_cost
    profit = order_total - cost_total
    profit_percent = (profit / order_total * 100) if order_total > 0 else 0
    
    order.order_total = order_total
    order.cost_total = cost_total
    order.profit = profit
    order.profit_percent = profit_percent
    order.status = "Processing"
    
    # Save order
    order_doc = order.model_dump()
    order_doc['date'] = order_doc['date'].isoformat()
    if order_doc.get('payment_date'):
        order_doc['payment_date'] = order_doc['payment_date'].isoformat()
    await db.orders.insert_one(order_doc)
    
    # Save lines (make a copy to avoid modifying the original)
    lines_to_save = [line.copy() for line in lines]
    await db.order_lines.insert_many(lines_to_save)
    
    # Update customer stats
    await update_customer_stats(customer['id'])
    
    # Create timeline entry
    await create_timeline_entry(customer['id'], "Order", f"New order created: {order.id[:8]} - {order_total:.2f} kr")
    
    # Send email notification for new order
    await send_new_order_notification(order.id, customer['name'], order_total)
    
    # Remove MongoDB's _id field if it exists to prevent BSON serialization error
    order_doc.pop('_id', None)
    
    return {**order_doc, "lines": lines}

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, current_user: User = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # CRITICAL: Handle COMPLETED status with stock reduction
    if status == "COMPLETED" and not order.get('stock_applied', False):
        # Get order lines
        lines = await db.order_lines.find({"order_id": order_id}, {"_id": 0}).to_list(1000)
        
        if not lines:
            raise HTTPException(status_code=400, detail="No items in order")
        
        # Validate stock availability before reducing
        for line in lines:
            stock = await db.stock.find_one({"product_id": line['product_id']}, {"_id": 0})
            if not stock:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No stock record found for product: {line['product_name']}"
                )
            if stock['quantity'] < line['quantity']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {line['product_name']}. Available: {stock['quantity']}, Required: {line['quantity']}"
                )
        
        # Apply stock changes atomically
        for line in lines:
            # Reduce stock quantity
            new_quantity_result = await db.stock.find_one_and_update(
                {"product_id": line['product_id']},
                {
                    "$inc": {"quantity": -line['quantity']},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
                },
                return_document=True,
                projection={"_id": 0}
            )
            
            # Double-check quantity didn't go negative (safety check)
            if new_quantity_result and new_quantity_result['quantity'] < 0:
                # Rollback this change
                await db.stock.update_one(
                    {"product_id": line['product_id']},
                    {"$inc": {"quantity": line['quantity']}}
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock went negative for {line['product_name']}. Transaction aborted."
                )
            
            # Update stock status
            await update_stock_status(line['product_id'])
            
            # Create StockMovement with new structure
            movement = {
                "id": str(uuid.uuid4()),
                "product_id": line['product_id'],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "OUT",
                "change": -line['quantity'],  # Negative number
                "source": "ORDER",
                "source_id": order_id,
                "note": f"Salg til kunde: {order['customer_name']}"
            }
            await db.stock_movements.insert_one(movement)
        
        # Update customer statistics
        customer = await db.customers.find_one({"id": order['customer_id']}, {"_id": 0})
        if customer:
            await db.customers.update_one(
                {"id": order['customer_id']},
                {
                    "$inc": {
                        "total_orders": 1,
                        "total_spent": order.get('order_total', 0)
                    },
                    "$set": {
                        "last_order_date": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        # Update order with stock_applied flag
        await db.orders.update_one(
            {"id": order_id},
            {
                "$set": {
                    "status": status,
                    "stock_applied": True,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    else:
        # Normal status update (not COMPLETED or already applied)
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {"status": status}}
        )
    
    # If order is delivered, create follow-up task
    if status == "Delivered" or status == "COMPLETED":
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if order:
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            task = Task(
                title=f"Follow up customer: {order['customer_name']}",
                description=f"Follow up on order {order_id[:8]}",
                due_date=due_date,
                priority="Medium",
                type="Customer",
                customer_id=order['customer_id'],
                order_id=order_id
            )
            task_doc = task.model_dump()
            task_doc['created_at'] = task_doc['created_at'].isoformat()
            if task_doc.get('due_date'):
                task_doc['due_date'] = task_doc['due_date'].isoformat()
            await db.tasks.insert_one(task_doc)
    
    return {"message": "Order status updated", "stock_reduced": status == "COMPLETED"}


# ============================================================================
# TASK ROUTES
# ============================================================================

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"status": status} if status else {}
    tasks = await db.tasks.find(query, {"_id": 0}).sort("due_date", 1).to_list(1000)
    
    for t in tasks:
        if isinstance(t.get('created_at'), str):
            t['created_at'] = datetime.fromisoformat(t['created_at'])
        if t.get('due_date') and isinstance(t['due_date'], str):
            t['due_date'] = datetime.fromisoformat(t['due_date'])
    
    return tasks

@api_router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task_create: TaskCreate, current_user: User = Depends(get_current_user)):
    task = Task(**task_create.model_dump())
    doc = task.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('due_date'):
        doc['due_date'] = doc['due_date'].isoformat()
    await db.tasks.insert_one(doc)
    return task

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskCreate, current_user: User = Depends(get_current_user)):
    result = await db.tasks.update_one(
        {"id": task_id},
        {"$set": task_update.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if updated.get('due_date') and isinstance(updated['due_date'], str):
        updated['due_date'] = datetime.fromisoformat(updated['due_date'])
    
    return Task(**updated)

@api_router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str, current_user: User = Depends(get_current_user)):
    result = await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task status updated"}

@api_router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return None


# ============================================================================
# EXPENSE ROUTES
# ============================================================================

@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses(current_user: User = Depends(get_current_user)):
    expenses = await db.expenses.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    for e in expenses:
        if isinstance(e.get('date'), str):
            e['date'] = datetime.fromisoformat(e['date'])
    return expenses

@api_router.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(expense_create: ExpenseCreate, current_user: User = Depends(get_current_user)):
    # Validate amount is positive
    if expense_create.amount <= 0:
        raise HTTPException(status_code=400, detail="Expense amount must be greater than 0")
    
    expense = Expense(**expense_create.model_dump())
    doc = expense.model_dump()
    doc['date'] = doc['date'].isoformat()
    await db.expenses.insert_one(doc)
    return expense

@api_router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str, current_user: User = Depends(get_current_user)):
    result = await db.expenses.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return None


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@api_router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.isoformat()
    
    # Today's orders
    today_orders = await db.orders.find({
        "date": {"$gte": today_str},
        "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
    }, {"_id": 0}).to_list(1000)
    
    today_sales = sum(order.get('order_total', 0) for order in today_orders)
    today_profit = sum(order.get('profit', 0) for order in today_orders)
    orders_count = len(today_orders)
    
    # Low stock count
    low_stock = await db.stock.find({"status": {"$in": ["Low", "Out"]}}, {"_id": 0}).to_list(1000)
    low_stock_count = len(low_stock)
    
    # Tasks
    all_tasks = await db.tasks.find({"status": {"$ne": "Done"}}, {"_id": 0}).to_list(1000)
    for t in all_tasks:
        if t.get('due_date') and isinstance(t['due_date'], str):
            t['due_date'] = datetime.fromisoformat(t['due_date']).replace(tzinfo=timezone.utc)
    
    today_tasks = [t for t in all_tasks if t.get('due_date') and t['due_date'].date() == datetime.now(timezone.utc).date()][:3]
    week_end = datetime.now(timezone.utc) + timedelta(days=7)
    week_tasks = [t for t in all_tasks if t.get('due_date') and t['due_date'] < week_end]
    overdue_tasks = [t for t in all_tasks if t.get('due_date') and t['due_date'] < datetime.now(timezone.utc)]
    
    # Best sellers (last 30 days)
    month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_orders = await db.orders.find({
        "date": {"$gte": month_ago},
        "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
    }, {"_id": 0}).to_list(1000)
    
    product_sales = {}
    product_profit = {}
    
    for order in recent_orders:
        lines = await db.order_lines.find({"order_id": order['id']}, {"_id": 0}).to_list(1000)
        for line in lines:
            pid = line['product_id']
            if pid not in product_sales:
                product_sales[pid] = {"name": line['product_name'], "quantity": 0, "revenue": 0}
                product_profit[pid] = {"name": line['product_name'], "profit": 0}
            product_sales[pid]['quantity'] += line['quantity']
            product_sales[pid]['revenue'] += line['line_total']
            product_profit[pid]['profit'] += line['line_profit']
    
    best_sellers = sorted(product_sales.values(), key=lambda x: x['quantity'], reverse=True)[:5]
    most_profitable = sorted(product_profit.values(), key=lambda x: x['profit'], reverse=True)[:5]
    
    # Customer segments
    customers = await db.customers.find({}, {"_id": 0}).to_list(1000)
    vip_customers = [c for c in customers if c.get('status') == 'VIP'][:5]
    new_customers = sorted([c for c in customers if c.get('status') == 'New'], 
                          key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    # Customers needing follow-up
    inactive_threshold = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    need_followup = [c for c in customers 
                     if c.get('last_order_date') and c['last_order_date'] < inactive_threshold 
                     and c.get('status') == 'Active'][:5]
    
    lost_customers = [c for c in customers if c.get('status') == 'Lost'][:5]
    
    # Monthly sales graph (last 6 months)
    monthly_sales = []
    monthly_profit = []
    for i in range(6):
        month_start = (datetime.now(timezone.utc).replace(day=1) - timedelta(days=30*i)).replace(hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        month_orders = await db.orders.find({
            "date": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()},
            "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
        }, {"_id": 0}).to_list(1000)
        
        sales = sum(o.get('order_total', 0) for o in month_orders)
        profit = sum(o.get('profit', 0) for o in month_orders)
        
        monthly_sales.insert(0, {"month": month_start.strftime("%b"), "value": sales})
        monthly_profit.insert(0, {"month": month_start.strftime("%b"), "value": profit})
    
    # Channel performance
    channel_stats = {}
    for order in recent_orders:
        channel = order.get('channel', 'Direct')
        if channel not in channel_stats:
            channel_stats[channel] = {"orders": 0, "revenue": 0, "profit": 0}
        channel_stats[channel]['orders'] += 1
        channel_stats[channel]['revenue'] += order.get('order_total', 0)
        channel_stats[channel]['profit'] += order.get('profit', 0)
    
    channel_performance = [{"channel": k, **v} for k, v in channel_stats.items()]
    
    return {
        "top_panel": {
            "today_sales": round(today_sales, 2),
            "today_profit": round(today_profit, 2),
            "orders_today": orders_count,
            "low_stock": low_stock_count
        },
        "tasks": {
            "today_top3": today_tasks,
            "this_week": week_tasks,
            "overdue": overdue_tasks
        },
        "sales_profit_graphs": {
            "monthly_sales": monthly_sales,
            "monthly_profit": monthly_profit
        },
        "products": {
            "best_sellers": best_sellers,
            "most_profitable": most_profitable,
            "low_stock": low_stock[:10]
        },
        "customers": {
            "vip": vip_customers,
            "new_this_week": new_customers,
            "need_followup": need_followup,
            "lost": lost_customers
        },
        "channel_performance": channel_performance
    }


@api_router.get("/dashboard/control-panel")
async def get_control_panel_data(current_user: User = Depends(get_current_user)):
    """Get data for the dashboard control panel"""
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_str = today_start.isoformat()
    
    # Alerts
    low_stock_count = await db.stock.count_documents({"status": {"$in": ["Low", "Out"]}})
    pending_orders = await db.orders.count_documents({"status": "Pending"})
    incoming_purchases = await db.purchases.count_documents({"status": {"$in": ["Ordered", "In_Transit"]}})
    
    # Today's stats
    today_orders = await db.orders.find({
        "date": {"$gte": today_start_str},
        "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
    }, {"_id": 0}).to_list(10000)
    
    today_sales = sum(order.get('order_total', 0) for order in today_orders)
    today_orders_count = len(today_orders)
    
    # New purchases today
    new_purchases_today = await db.purchases.count_documents({
        "date": {"$gte": today_start_str}
    })
    
    # Inventory value change today (based on stock movements)
    today_movements = await db.stock_movements.find({
        "date": {"$gte": today_start_str}
    }, {"_id": 0}).to_list(10000)
    
    inventory_change = 0
    products = await db.products.find({"active": True}, {"_id": 0}).to_list(10000)
    
    for movement in today_movements:
        product = next((p for p in products if p['id'] == movement['product_id']), None)
        if product:
            cost = product.get('cost', 0)
            quantity_change = movement['quantity'] if movement['type'] == 'IN' else -movement['quantity']
            inventory_change += quantity_change * cost
    
    return {
        "alerts": {
            "lowStock": low_stock_count,
            "pendingOrders": pending_orders,
            "incomingPurchases": incoming_purchases
        },
        "todayStats": {
            "sales": round(today_sales, 2),
            "orders": today_orders_count,
            "newPurchases": new_purchases_today,
            "inventoryChange": round(inventory_change, 2)
        }
    }


@api_router.get("/dashboard/kpis")
async def get_dashboard_kpis(current_user: User = Depends(get_current_user)):
    """Get key KPI data for the new dashboard layout"""
    
    # 1. Total Active Products
    products = await db.products.find({"active": True}, {"_id": 0}).to_list(10000)
    total_products = len(products)
    
    # 2. Low Stock Count
    low_stock_items = await db.stock.find({"status": {"$in": ["Low", "Out"]}}, {"_id": 0}).to_list(1000)
    low_stock_count = len(low_stock_items)
    
    # 3. Sales This Month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_str = month_start.isoformat()
    
    month_orders = await db.orders.find({
        "date": {"$gte": month_start_str},
        "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
    }, {"_id": 0}).to_list(10000)
    
    sales_count = len(month_orders)
    sales_revenue = sum(order.get('order_total', 0) for order in month_orders)
    
    # 4. Incoming Purchases
    incoming_purchases = await db.purchases.find({
        "status": {"$in": ["Ordered", "In_Transit"]}
    }, {"_id": 0}).to_list(1000)
    incoming_count = len(incoming_purchases)
    
    # 5. Total Inventory Value
    all_stock = await db.stock.find({}, {"_id": 0, "product_id": 1, "quantity": 1}).to_list(10000)
    total_value = 0
    
    for stock_item in all_stock:
        product = next((p for p in products if p['id'] == stock_item['product_id']), None)
        if product:
            total_value += stock_item['quantity'] * product.get('cost', 0)
    
    # 6. Active Customers This Month
    # Find unique customer IDs from this month's orders
    active_customer_ids = set(order.get('customer_id') for order in month_orders if order.get('customer_id'))
    active_customers_count = len(active_customer_ids)
    
    # Last 30 days data for graph
    days_data = []
    for i in range(30):
        day = now - timedelta(days=29-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_orders = [o for o in month_orders 
                      if day_start.isoformat() <= o['date'] < day_end.isoformat()]
        
        days_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "orders": len(day_orders),
            "revenue": round(sum(o.get('order_total', 0) for o in day_orders), 2)
        })
    
    # Low stock top 5 with product details
    low_stock_details = []
    for stock in low_stock_items[:5]:
        product = next((p for p in products if p['id'] == stock['product_id']), None)
        if product:
            low_stock_details.append({
                "product_name": product['name'],
                "current_stock": stock['quantity'],
                "min_stock": stock['min_stock'],
                "status": stock['status']
            })
    
    # Recent orders (last 5)
    recent_orders = sorted(month_orders, key=lambda x: x.get('date', ''), reverse=True)[:5]
    recent_orders_details = []
    
    for order in recent_orders:
        customer = await db.customers.find_one({"id": order.get('customer_id')}, {"_id": 0, "name": 1})
        recent_orders_details.append({
            "id": order['id'],
            "date": order['date'][:10],  # Just the date part
            "customer": customer.get('name') if customer else "Unknown",
            "total": round(order.get('order_total', 0), 2),
            "status": order.get('status', 'Unknown')
        })
    
    return {
        "kpis": {
            "total_products": total_products,
            "low_stock": low_stock_count,
            "sales_this_month": {
                "count": sales_count,
                "revenue": round(sales_revenue, 2)
            },
            "incoming_purchases": incoming_count,
            "inventory_value": round(total_value, 2),
            "active_customers": active_customers_count
        },
        "chart_data": {
            "last_30_days": days_data
        },
        "tables": {
            "low_stock": low_stock_details,
            "recent_orders": recent_orders_details
        }
    }


# ============================================================================
# REPORTS ROUTES
# ============================================================================

@api_router.get("/reports/daily")
async def get_daily_report(date: Optional[str] = None, current_user: User = Depends(get_current_user)):
    if date:
        target_date = datetime.fromisoformat(date)
    else:
        target_date = datetime.now(timezone.utc)
    
    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    orders = await db.orders.find({
        "date": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()},
        "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
    }, {"_id": 0}).to_list(1000)
    
    daily_sales = sum(o.get('order_total', 0) for o in orders)
    daily_profit = sum(o.get('profit', 0) for o in orders)
    orders_today = len(orders)
    
    # Low stock
    low_stock = await db.stock.find({"status": {"$in": ["Low", "Out"]}}, {"_id": 0}).to_list(1000)
    
    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "daily_sales": round(daily_sales, 2),
        "daily_profit": round(daily_profit, 2),
        "orders_today": orders_today,
        "low_stock_count": len(low_stock)
    }

@api_router.get("/reports/monthly")
async def get_monthly_report(month: Optional[int] = None, year: Optional[int] = None, current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year
    
    month_start = datetime(target_year, target_month, 1, tzinfo=timezone.utc)
    if target_month == 12:
        month_end = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(target_year, target_month + 1, 1, tzinfo=timezone.utc)
    
    orders = await db.orders.find({
        "date": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()},
        "status": {"$in": ["Processing", "Packed", "Shipped", "Delivered"]}
    }, {"_id": 0}).to_list(1000)
    
    monthly_sales = sum(o.get('order_total', 0) for o in orders)
    monthly_profit = sum(o.get('profit', 0) for o in orders)
    
    # Top products
    product_stats = {}
    for order in orders:
        lines = await db.order_lines.find({"order_id": order['id']}, {"_id": 0}).to_list(1000)
        for line in lines:
            pid = line['product_id']
            if pid not in product_stats:
                product_stats[pid] = {"name": line['product_name'], "quantity": 0, "revenue": 0}
            product_stats[pid]['quantity'] += line['quantity']
            product_stats[pid]['revenue'] += line['line_total']
    
    top_products = sorted(product_stats.values(), key=lambda x: x['revenue'], reverse=True)[:10]
    
    # Top customers
    customer_stats = {}
    for order in orders:
        cid = order['customer_id']
        if cid not in customer_stats:
            customer_stats[cid] = {"name": order['customer_name'], "orders": 0, "revenue": 0}
        customer_stats[cid]['orders'] += 1
        customer_stats[cid]['revenue'] += order.get('order_total', 0)
    
    top_customers = sorted(customer_stats.values(), key=lambda x: x['revenue'], reverse=True)[:10]
    
    return {
        "month": target_month,
        "year": target_year,
        "monthly_sales": round(monthly_sales, 2),
        "monthly_profit": round(monthly_profit, 2),
        "orders_count": len(orders),
        "top_products": top_products,
        "top_customers": top_customers
    }


# ============================================================================
# SEARCH ROUTE
# ============================================================================

@api_router.get("/search")
async def search(q: str, current_user: User = Depends(get_current_user)):
    query_lower = q.lower()
    results = {"products": [], "customers": [], "orders": [], "tasks": [], "expenses": []}
    
    # Search products
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    results['products'] = [p for p in products if query_lower in p.get('name', '').lower() or query_lower in p.get('sku', '').lower()][:10]
    
    # Search customers
    customers = await db.customers.find({}, {"_id": 0}).to_list(1000)
    results['customers'] = [c for c in customers if query_lower in c.get('name', '').lower() or query_lower in c.get('email', '').lower()][:10]
    
    # Search orders
    orders = await db.orders.find({}, {"_id": 0}).to_list(1000)
    results['orders'] = [o for o in orders if query_lower in o.get('customer_name', '').lower() or query_lower in o.get('id', '')][:10]
    
    # Search tasks
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(1000)
    results['tasks'] = [t for t in tasks if query_lower in t.get('title', '').lower() or query_lower in t.get('description', '').lower()][:10]
    
    # Search expenses
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    results['expenses'] = [e for e in expenses if query_lower in e.get('category', '').lower() or query_lower in e.get('notes', '').lower()][:10]
    
    return results


# ============================================================================
# AUTOMATION ROUTES
# ============================================================================

@api_router.post("/automation/check-low-stock")
async def run_low_stock_automation(current_user: User = Depends(get_current_user)):
    """Manually trigger low stock automation check for all products"""
    stock_items = await db.stock.find({"status": {"$in": ["Low", "Out"]}}, {"_id": 0}).to_list(1000)
    tasks_created = 0
    
    for stock_item in stock_items:
        await check_and_create_low_stock_task(stock_item['product_id'])
        # Check if task was created
        task_exists = await db.tasks.find_one({
            "product_id": stock_item['product_id'],
            "type": "Stock",
            "status": {"$ne": "Done"}
        })
        if task_exists:
            tasks_created += 1
    
    return {
        "message": "Low stock automation completed",
        "low_stock_items": len(stock_items),
        "tasks_created": tasks_created
    }

@api_router.get("/automation/status")
async def get_automation_status(current_user: User = Depends(get_current_user)):
    """Get status of all automation rules"""
    # Count low stock items
    low_stock_count = await db.stock.count_documents({"status": {"$in": ["Low", "Out"]}})
    
    # Count active stock tasks
    stock_tasks_count = await db.tasks.count_documents({
        "type": "Stock",
        "status": {"$ne": "Done"}
    })
    
    # Count customers needing follow-up (no order in last 60 days)
    inactive_threshold = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    customers_needing_followup = await db.customers.count_documents({
        "last_order_date": {"$lt": inactive_threshold},
        "status": "Active"
    })
    
    return {
        "automations": {
            "low_stock_monitoring": {
                "enabled": True,
                "description": "Auto-creates tasks when stock is low or out",
                "low_stock_items": low_stock_count,
                "active_tasks": stock_tasks_count
            },
            "customer_stats_update": {
                "enabled": True,
                "description": "Auto-updates customer stats on order creation"
            },
            "task_completion": {
                "enabled": True,
                "description": "Auto-completes stock tasks when inventory is replenished"
            },
            "customer_follow_up": {
                "enabled": False,
                "description": "Identifies customers needing follow-up",
                "customers_needing_followup": customers_needing_followup
            },
            "email_notifications": {
                "enabled": EMAIL_ENABLED,
                "description": "Email notifications for important events",
                "smtp_configured": bool(SMTP_USER and SMTP_PASSWORD)
            }
        }
    }

@api_router.post("/automation/test-email")
async def test_email_notification(email: str, current_user: User = Depends(get_current_user)):
    """Send a test email to verify email configuration"""
    subject = "🧪 Test E-post fra ZenVit CRM"
    body = """
Hei!

Dette er en test e-post fra ZenVit CRM-systemet.

Hvis du mottar denne e-posten, er e-postkonfigurasjonen din korrekt satt opp.

Med vennlig hilsen,
ZenVit CRM System
    """
    
    html_body = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; padding: 20px; border-radius: 8px; }
        .content { background: #f9fafb; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .footer { text-align: center; color: #7b8794; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🧪 Test E-post</h2>
        </div>
        <div class="content">
            <p>Hei!</p>
            <p>Dette er en test e-post fra <strong>ZenVit CRM-systemet</strong>.</p>
            <p>Hvis du mottar denne e-posten, er e-postkonfigurasjonen din korrekt satt opp og klar til bruk! ✅</p>
        </div>
        <div class="footer">
            <p>Dette er en automatisk e-post fra ZenVit CRM System</p>
        </div>
    </div>
</body>
</html>
    """
    
    success = await send_email(email, subject, body, html_body)
    
    if success:
        return {"message": f"Test e-post sendt til {email}", "success": True}
    else:
        return {
            "message": f"Kunne ikke sende e-post. E-post er {'ikke aktivert eller' if not EMAIL_ENABLED else ''} ikke konfigurert korrekt.",
            "success": False,
            "email_enabled": EMAIL_ENABLED,
            "smtp_configured": bool(SMTP_USER and SMTP_PASSWORD)
        }


# ============================================================================
# SEED DATA ROUTE
# ============================================================================

@api_router.post("/seed-data", status_code=status.HTTP_201_CREATED)
async def seed_data():
    """Populate database with comprehensive test data"""
    
    # Clear existing
    await db.products.delete_many({})
    await db.stock.delete_many({})
    await db.stock_movements.delete_many({})
    await db.customers.delete_many({})
    await db.customer_timeline.delete_many({})
    await db.suppliers.delete_many({})
    await db.purchases.delete_many({})
    await db.purchase_lines.delete_many({})
    await db.orders.delete_many({})
    await db.order_lines.delete_many({})
    await db.tasks.delete_many({})
    await db.expenses.delete_many({})
    
    # Create suppliers
    suppliers = [
        {"id": str(uuid.uuid4()), "name": "Nordic Supplements AS", "contact_person": "Per Olsen", 
         "email": "ordre@nordicsupplements.no", "phone": "22334455", "address": "Industriveien 10, 0581 Oslo",
         "website": "www.nordicsupplements.no", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "VitaImport Norge", "contact_person": "Anne Berg",
         "email": "salg@vitaimport.no", "phone": "55667788", "address": "Havnepromenaden 3, 5013 Bergen",
         "website": "www.vitaimport.no", "created_at": datetime.now(timezone.utc).isoformat()}
    ]
    await db.suppliers.insert_many(suppliers)
    
    # Create products
    products = [
        {"id": str(uuid.uuid4()), "sku": "ZV-D3K2-001", "name": "D3 + K2 Premium", 
         "description": "Vitamin D3 5000 IU + K2 MK-7 200 mcg", "category": "vitamin",
         "cost": 89.0, "price": 299.0, "supplier_id": suppliers[0]['id'], "color": "d3", "active": True,
         "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "sku": "ZV-OM3-001", "name": "Omega-3 Triglyceride",
         "description": "EPA 1000mg + DHA 500mg", "category": "supplement",
         "cost": 95.0, "price": 349.0, "supplier_id": suppliers[0]['id'], "color": "omega", "active": True,
         "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "sku": "ZV-MAG-001", "name": "Magnesium Glysinat 400mg",
         "description": "Høyt biotilgjengelig magnesium", "category": "mineral",
         "cost": 72.0, "price": 249.0, "supplier_id": suppliers[1]['id'], "color": "mag", "active": True,
         "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "sku": "ZV-CZNC-001", "name": "C-vitamin + Sink",
         "description": "Vitamin C 1000mg + Sink 15mg", "category": "vitamin",
         "cost": 58.0, "price": 199.0, "supplier_id": suppliers[1]['id'], "color": "csink", "active": True,
         "created_at": datetime.now(timezone.utc).isoformat()}
    ]
    await db.products.insert_many(products)
    
    # Create stock
    stock_items = [
        {"id": str(uuid.uuid4()), "product_id": products[0]['id'], "quantity": 312, "min_stock": 100, "status": "OK", "last_updated": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "product_id": products[1]['id'], "quantity": 284, "min_stock": 150, "status": "OK", "last_updated": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "product_id": products[2]['id'], "quantity": 75, "min_stock": 120, "status": "Low", "last_updated": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "product_id": products[3]['id'], "quantity": 198, "min_stock": 100, "status": "OK", "last_updated": datetime.now(timezone.utc).isoformat()}
    ]
    await db.stock.insert_many(stock_items)
    
    # Create customers
    customers = [
        {"id": str(uuid.uuid4()), "name": "Kari Nordmann", "email": "kari.nordmann@example.no", 
         "phone": "91234567", "address": "Storgata 1", "city": "Oslo", "zip_code": "0150",
         "type": "Private", "status": "Active", "total_value": 0, "order_count": 0,
         "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Ola Hansen", "email": "ola.hansen@example.no",
         "phone": "98765432", "address": "Fjordveien 25", "city": "Bergen", "zip_code": "5003",
         "type": "Private", "status": "VIP", "total_value": 0, "order_count": 0,
         "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Helse AS", "email": "post@helse.no",
         "phone": "22998877", "address": "Næringsveien 42", "city": "Oslo", "zip_code": "0580",
         "type": "Business", "status": "Active", "total_value": 0, "order_count": 0,
         "created_at": datetime.now(timezone.utc).isoformat()}
    ]
    await db.customers.insert_many(customers)
    
    # Create some tasks
    tasks = [
        {"id": str(uuid.uuid4()), "title": "Bestill mer Magnesium", "description": "Lageret går tom",
         "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "priority": "High",
         "status": "Planned", "type": "Stock", "product_id": products[2]['id'], "assigned_to": "Jabar",
         "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "title": "Følg opp VIP-kunde", "description": "Ola Hansen - sjekk tilfredshet",
         "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(), "priority": "Medium",
         "status": "Planned", "type": "Customer", "customer_id": customers[1]['id'], "assigned_to": "Jabar",
         "created_at": datetime.now(timezone.utc).isoformat()}
    ]
    await db.tasks.insert_many(tasks)
    
    # Create expenses
    expenses = [
        {"id": str(uuid.uuid4()), "date": datetime.now(timezone.utc).isoformat(), "category": "Marketing",
         "amount": 8500.0, "payment_status": "Paid", "notes": "Facebook Ads - Januar"},
        {"id": str(uuid.uuid4()), "date": datetime.now(timezone.utc).isoformat(), "category": "Shipping",
         "amount": 6200.0, "payment_status": "Paid", "notes": "Posten - Månedlig avtale"},
        {"id": str(uuid.uuid4()), "date": datetime.now(timezone.utc).isoformat(), "category": "Software",
         "amount": 3700.0, "payment_status": "Unpaid", "notes": "Shopify abonnement"}
    ]
    await db.expenses.insert_many(expenses)
    
    return {"message": "Complete test data created successfully"}


# ============================================================================
# REGISTER ROUTES - MUST BE AFTER ALL ROUTE DEFINITIONS
# ============================================================================
@api_router.post("/ai/recommend-products")
async def ai_recommend_products(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """AI-powered product recommendations based on customer needs"""
    try:
        import openai
        import re
        
        customer_context = request_data.get("customer_context", "")
        
        if not customer_context or len(customer_context.strip()) < 10:
            raise HTTPException(status_code=400, detail="Vennligst gi en mer detaljert beskrivelse av kunden")
        
        # Get all active products from database
        products = await db.products.find({"active": True}, {"_id": 0}).to_list(1000)
        
        # Prepare products data for AI
        products_info = []
        for p in products:
            product_data = {
                "name": p.get("name"),
                "category": p.get("category"),
                "subcategory": p.get("subcategory"),
                "tags": p.get("health_areas", []),
                "description": p.get("short_description") or p.get("description", ""),
                "sku": p.get("sku"),
                "price": p.get("price")
            }
            products_info.append(product_data)
        
        # Create AI prompt
        system_prompt = """Du er "ZenVit AI-Veileder", en intern fagassistent for ZenVit CRM.

VIKTIGE REGLER:
- Du hjelper kun ansatte, ikke sluttkunden direkte
- Du foreslår ALLTID kun ZenVit-produkter basert på produktdata som gis
- Du gir trygge, enkle, ærlige anbefalinger uten å overdrive
- Du gir IKKE medisinske diagnoser
- Du bruker en rolig, profesjonell og tydelig stil
- Du anbefaler maksimum 3 produkter

OPPGAVE:
Basert på kundebeskrivelsen, identifiser behov og match mot produkttags/kategori.
Velg 1-3 hovedprodukter som passer best.

SVAR FORMAT (JSON):
{
  "products": [
    {
      "name": "Produktnavn",
      "reason": "Kort grunn (1-2 setninger)",
      "dose": "Anbefalt dose og tidspunkt"
    }
  ],
  "explanation": "Detaljert forklaring i markdown format med:\\n- Identifiserte behov\\n- Hver produktanbefalning med begrunnelse\\n- Hvordan bruke sammen\\n- Viktig disclaimer om at dette er generelle anbefalinger"
}

Svar ALLTID med gyldig JSON."""

        user_prompt = f"""KUNDEBESKRIVELSE:
{customer_context}

TILGJENGELIGE ZENVIT-PRODUKTER:
{json.dumps(products_info, indent=2, ensure_ascii=False)}

Gi anbefalinger basert på beskrivelsen."""

        # Call OpenAI API with Emergent key
        client = openai.OpenAI(
            api_key="sk-emergent-bDeF7E1Fc202d02EdC2A8AB33Bdd17Fe5eFADD66B5f7B5BD",
            base_url="https://api.emergent.sh/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group())
            else:
                ai_data = json.loads(ai_response)
                
            return {
                "success": True,
                "recommendations": ai_data
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            return {
                "success": True,
                "recommendations": {
                    "products": [],
                    "explanation": ai_response
                }
            }
            
    except Exception as e:
        logging.error(f"AI recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Kunne ikke generere anbefalinger: {str(e)}")


# ============================================================================
# REGISTER ROUTES - MUST BE AFTER ALL ROUTE DEFINITIONS
# ============================================================================
app.include_router(api_router)

# Add custom static files CORS middleware first
app.add_middleware(StaticFilesCORSMiddleware)

# Add CORS middleware for API endpoints
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="/app/backend/uploads"), name="uploads")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db():
    """Initialize database indexes on startup"""
    try:
        from utils import create_indexes
        await create_indexes(db)
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Could not create indexes: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
