"""
Database indexes for improved query performance
"""

async def create_indexes(db):
    """Create database indexes for all collections"""
    
    # Users collection
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    
    # Products collection
    await db.products.create_index("id", unique=True)
    await db.products.create_index("sku", unique=True)
    await db.products.create_index("name")
    await db.products.create_index("category")
    
    # Customers collection
    await db.customers.create_index("id", unique=True)
    await db.customers.create_index("email")
    await db.customers.create_index("phone")
    await db.customers.create_index("name")
    await db.customers.create_index("status")
    
    # Orders collection
    await db.orders.create_index("id", unique=True)
    await db.orders.create_index("customer_id")
    await db.orders.create_index("date")
    await db.orders.create_index("status")
    await db.orders.create_index([("date", -1)])  # Descending for recent first
    
    # Order lines collection
    await db.order_lines.create_index("order_id")
    await db.order_lines.create_index("product_id")
    
    # Stock collection
    await db.stock.create_index("product_id", unique=True)
    await db.stock.create_index("status")
    
    # Stock movements collection
    await db.stock_movements.create_index("product_id")
    await db.stock_movements.create_index("date")
    await db.stock_movements.create_index([("date", -1)])
    
    # Tasks collection
    await db.tasks.create_index("id", unique=True)
    await db.tasks.create_index("status")
    await db.tasks.create_index("due_date")
    await db.tasks.create_index("priority")
    await db.tasks.create_index("product_id")
    await db.tasks.create_index([("due_date", 1)])  # Ascending for upcoming first
    
    # Purchases collection
    await db.purchases.create_index("id", unique=True)
    await db.purchases.create_index("supplier_id")
    await db.purchases.create_index("date")
    await db.purchases.create_index([("date", -1)])
    
    # Suppliers collection
    await db.suppliers.create_index("id", unique=True)
    await db.suppliers.create_index("name")
    
    # Expenses collection
    await db.expenses.create_index("id", unique=True)
    await db.expenses.create_index("category")
    await db.expenses.create_index("date")
    await db.expenses.create_index([("date", -1)])
    
    # Customer timeline collection
    await db.customer_timeline.create_index("customer_id")
    await db.customer_timeline.create_index("date")
    await db.customer_timeline.create_index([("date", -1)])
    
    print("✅ Database indexes created successfully")
