"""
Initialize Stock Management System

This script prepares the database for the new automated stock management system:
1. Sets all existing Stock.quantity = 0 (clean slate)
2. Sets all Purchase.stock_applied = False
3. Sets all Order.stock_applied = False
4. Creates Stock records for any products that don't have one

Run this script ONCE before deploying the new stock system.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def initialize_stock_system():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🚀 Initializing Stock Management System...")
    print("=" * 60)
    
    # Step 1: Reset all stock quantities to 0
    print("\n📦 Step 1: Resetting all stock quantities to 0...")
    result = await db.stock.update_many(
        {},
        {"$set": {"quantity": 0}}
    )
    print(f"   ✅ Updated {result.modified_count} stock records")
    
    # Step 2: Set stock_applied = False for all purchases
    print("\n🛒 Step 2: Setting stock_applied = False for all purchases...")
    result = await db.purchases.update_many(
        {},
        {"$set": {"stock_applied": False}}
    )
    print(f"   ✅ Updated {result.modified_count} purchase records")
    
    # Step 3: Set stock_applied = False for all orders
    print("\n📋 Step 3: Setting stock_applied = False for all orders...")
    result = await db.orders.update_many(
        {},
        {"$set": {"stock_applied": False}}
    )
    print(f"   ✅ Updated {result.modified_count} order records")
    
    # Step 4: Create Stock records for products that don't have one
    print("\n🆕 Step 4: Creating missing stock records...")
    products = await db.products.find({}, {"_id": 0, "id": 1, "min_stock": 1}).to_list(1000)
    created_count = 0
    
    for product in products:
        stock_exists = await db.stock.find_one({"product_id": product['id']})
        if not stock_exists:
            import uuid
            from datetime import datetime, timezone
            new_stock = {
                "id": str(uuid.uuid4()),
                "product_id": product['id'],
                "quantity": 0,
                "min_stock": product.get('min_stock', 80),
                "status": "Out",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.stock.insert_one(new_stock)
            created_count += 1
    
    print(f"   ✅ Created {created_count} new stock records")
    
    # Step 5: Summary
    print("\n" + "=" * 60)
    print("✅ Stock Management System initialized successfully!")
    print("\n📊 Summary:")
    
    total_products = len(products)
    total_stock = await db.stock.count_documents({})
    total_purchases = await db.purchases.count_documents({})
    total_orders = await db.orders.count_documents({})
    
    print(f"   • Total products: {total_products}")
    print(f"   • Total stock records: {total_stock}")
    print(f"   • Total purchases: {total_purchases} (all set to stock_applied=False)")
    print(f"   • Total orders: {total_orders} (all set to stock_applied=False)")
    
    print("\n🎯 Next Steps:")
    print("   1. Deploy the new backend with stock management logic")
    print("   2. Use 'Stock Adjustment' to set correct initial quantities")
    print("   3. From now on, stock will be managed automatically!")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(initialize_stock_system())
