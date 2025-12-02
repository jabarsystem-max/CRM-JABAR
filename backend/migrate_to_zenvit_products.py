"""
Migrate to Official ZENVIT Product Structure

This script:
1. Deletes old test/demo products
2. Inserts the 4 official ZENVIT products with proper structure
3. Updates Product model to include stock_quantity directly
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv()

# Official ZENVIT Products
ZENVIT_PRODUCTS = [
    {
        "id": str(uuid.uuid4()),
        "name": "ZENVIT D3 + K2 Premium (2000 IE / MK-7)",
        "sku": "ZV-D3K2-01",
        "category": "Vitamin D",
        "color_hex": "#F4B58A",
        "icon_url": "/icons/d3k2.png",
        "cost_price": 65,
        "sale_price": 309,
        "stock_quantity": 0,
        "minimum_stock": 50,
        "batch_tracking": True,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "ZENVIT Omega-3 (EPA/DHA – Triglyseridform)",
        "sku": "ZV-OM3-01",
        "category": "Omega-3",
        "color_hex": "#B9D8E7",
        "icon_url": "/icons/omega3.png",
        "cost_price": 79,
        "sale_price": 349,
        "stock_quantity": 0,
        "minimum_stock": 50,
        "batch_tracking": True,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "ZENVIT Magnesium Glysinat 400 mg",
        "sku": "ZV-MG-01",
        "category": "Mineraler",
        "color_hex": "#9EC7B0",
        "icon_url": "/icons/magnesium.png",
        "cost_price": 55,
        "sale_price": 249,
        "stock_quantity": 0,
        "minimum_stock": 50,
        "batch_tracking": True,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "ZENVIT C-vitamin + Sink (Immunformel)",
        "sku": "ZV-CZ-01",
        "category": "Immun",
        "color_hex": "#F6E3A2",
        "icon_url": "/icons/czink.png",
        "cost_price": 39,
        "sale_price": 199,
        "stock_quantity": 0,
        "minimum_stock": 50,
        "batch_tracking": True,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
]

async def migrate_products():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🚀 Migrating to Official ZENVIT Products...")
    print("=" * 60)
    
    # Step 1: Delete old/test products
    print("\n🗑️  Step 1: Deleting old products...")
    
    # Delete products with specific patterns
    patterns = [
        {"name": {"$regex": "Redigert", "$options": "i"}},
        {"name": {"$regex": "triglyserid", "$options": "i"}},
        {"name": {"$regex": "400 mg", "$options": "i"}},
        {"name": {"$regex": "Vask", "$options": "i"}},
        {"name": {"$regex": "Test", "$options": "i"}},
        {"name": {"$regex": "Duplicate", "$options": "i"}},
        {"name": {"$regex": "Updated", "$options": "i"}},
        {"name": {"$regex": "Premium - Edited", "$options": "i"}}
    ]
    
    result = await db.products.delete_many({"$or": patterns})
    print(f"   ✅ Deleted {result.deleted_count} old products")
    
    # Step 2: Check if ZENVIT products already exist
    print("\n📦 Step 2: Checking existing ZENVIT products...")
    existing_skus = []
    for product in ZENVIT_PRODUCTS:
        existing = await db.products.find_one({"sku": product["sku"]})
        if existing:
            existing_skus.append(product["sku"])
            print(f"   ℹ️  Product {product['sku']} already exists, skipping...")
    
    # Step 3: Insert new ZENVIT products
    print("\n✨ Step 3: Inserting official ZENVIT products...")
    inserted_count = 0
    
    for product in ZENVIT_PRODUCTS:
        if product["sku"] not in existing_skus:
            await db.products.insert_one(product)
            print(f"   ✅ Inserted: {product['name']}")
            inserted_count += 1
            
            # Create Stock record for backward compatibility
            stock_record = {
                "id": str(uuid.uuid4()),
                "product_id": product["id"],
                "quantity": product["stock_quantity"],
                "min_stock": product["minimum_stock"],
                "status": "Out" if product["stock_quantity"] == 0 else "OK",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.stock.insert_one(stock_record)
    
    print(f"\n   ✅ Inserted {inserted_count} new products")
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("\n📊 Summary:")
    
    total_products = await db.products.count_documents({})
    zenvit_products = await db.products.count_documents({"sku": {"$regex": "^ZV-"}})
    
    print(f"   • Total products: {total_products}")
    print(f"   • ZENVIT products: {zenvit_products}")
    print(f"   • Deleted old products: {result.deleted_count}")
    print(f"   • Inserted new products: {inserted_count}")
    
    print("\n🎯 Next Steps:")
    print("   1. Restart backend to apply new Product model")
    print("   2. Use Stock Adjustment to set initial quantities")
    print("   3. Update frontend to use new fields (color_hex, icon_url)")
    print("=" * 60)
    
    # Show the 4 ZENVIT products
    print("\n📦 Official ZENVIT Products:")
    products = await db.products.find({"sku": {"$regex": "^ZV-"}}, {"_id": 0}).to_list(10)
    for p in products:
        print(f"\n   {p['name']}")
        print(f"   SKU: {p['sku']}")
        print(f"   Color: {p.get('color_hex', 'N/A')}")
        print(f"   Price: {p.get('sale_price', 'N/A')} kr")
        print(f"   Stock: {p.get('stock_quantity', 0)} (min: {p.get('minimum_stock', 50)})")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_products())
