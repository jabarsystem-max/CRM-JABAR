"""
Performance Configuration for ZenVit CRM
"""

# Query projections to reduce data transfer
PROJECTIONS = {
    'user_basic': {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1},
    'product_basic': {"_id": 0, "id": 1, "name": 1, "sku": 1, "price": 1, "category": 1},
    'product_full': {"_id": 0},
    'customer_basic': {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1, "type": 1, "status": 1},
    'customer_full': {"_id": 0},
    'order_basic': {"_id": 0, "id": 1, "customer_id": 1, "order_total": 1, "status": 1, "date": 1},
    'stock_basic': {"_id": 0, "product_id": 1, "quantity": 1, "status": 1, "min_stock": 1},
}

# Cache settings (for future Redis implementation)
CACHE_TTL = {
    'dashboard': 300,  # 5 minutes
    'products': 600,   # 10 minutes
    'reports': 3600,   # 1 hour
}

# API rate limiting (requests per minute)
RATE_LIMITS = {
    'default': 60,
    'search': 30,
    'reports': 10,
}

# Database query limits
QUERY_LIMITS = {
    'max_results': 1000,
    'default_page_size': 50,
}
