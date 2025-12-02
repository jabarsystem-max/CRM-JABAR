"""
One-time migration: Sync Stock.quantity to Product.stock_quantity
After this, Stock table will no longer be used as active inventory source.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

async def sync_stock_to_products():
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔄 Syncing Stock.quantity → Product.stock_quantity")
    print("=" * 60)
    
    # Get all stock records
    stock_records = await db.stock.find({}, {"_id": 0}).to_list(1000)
    
    updated_count = 0
    for stock in stock_records:
        product_id = stock['product_id']
        quantity = stock['quantity']
        
        # Update product with stock quantity
        result = await db.products.update_one(
            {"id": product_id},
            {
                "$set": {
                    "stock_quantity": quantity,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            product = await db.products.find_one({"id": product_id}, {"_id": 0, "name": 1})
            print(f"✅ {product['name']}: {quantity} stk")
            updated_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"✅ Synced {updated_count} products")
    
    # Verify sync
    print(f"\n📊 Verification:")
    products = await db.products.find({}, {"_id": 0, "name": 1, "stock_quantity": 1}).to_list(100)
    for p in products:
        print(f"   {p['name']}: {p.get('stock_quantity', 0)} stk")
    
    print(f"\n{'=' * 60}")
    print("✅ Sync complete!")
    print("\n⚠️  Stock table is now INACTIVE")
    print("   All future stock operations will use Product.stock_quantity")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(sync_stock_to_products())
