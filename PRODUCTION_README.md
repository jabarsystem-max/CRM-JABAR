# ZenVit CRM - Production Deployment Guide

## 📋 System Overview

ZenVit CRM er et fullstendig Customer Relationship Management-system bygget med:
- **Backend**: FastAPI + MongoDB + JWT Authentication
- **Frontend**: React 18 + React Router + Axios
- **Database**: MongoDB (async with Motor)
- **Styling**: Custom CSS with theme support (light/dark)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB 5.0+
- Yarn package manager

### Backend Setup
```bash
cd /app/backend
pip install -r requirements.txt
python -m server  # or uvicorn server:app
```

### Frontend Setup
```bash
cd /app/frontend
yarn install
yarn start
```

## 🔧 Environment Configuration

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="zenvit_crm"
CORS_ORIGINS="*"
SECRET_KEY="your-secret-key-change-in-production"

# Email configuration (optional)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER=""
SMTP_PASSWORD=""
EMAIL_FROM="noreply@zenvit.no"
EMAIL_ENABLED="false"
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL="http://localhost:8001"
```

## 📊 Database Setup

### Initial Data Seeding
```bash
curl -X POST http://localhost:8001/api/seed-data \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Database Indexes
Automatic creation on startup via `/app/backend/utils/db_indexes.py`

## 🔐 Security

### Default Credentials
- **Email**: admin@zenvit.no
- **Password**: admin123
- ⚠️ **CHANGE THESE IN PRODUCTION**

### JWT Configuration
- Token expiry: 24 hours (configurable in server.py)
- Algorithm: HS256
- Secret key: Set in .env file

### Password Security
- Hashing: bcrypt
- Salt rounds: Default (handled by passlib)

## 🎯 API Documentation

### Base URL
- Development: `http://localhost:8001/api`
- Production: Your deployed URL + `/api`

### Interactive API Docs
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

### Main Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

#### Products
- `GET /api/products` - List all products
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

#### Customers
- `GET /api/customers` - List customers
- `POST /api/customers` - Create customer
- `GET /api/customers/{id}/timeline` - Customer timeline

#### Orders
- `GET /api/orders` - List orders
- `POST /api/orders` - Create order
- `PUT /api/orders/{id}` - Update order

#### Stock
- `GET /api/stock` - List stock levels
- `POST /api/stock/adjust` - Adjust stock (+/-)
- `GET /api/stock/movements` - Stock movement history

#### Dashboard & Reports
- `GET /api/dashboard` - Dashboard data
- `GET /api/reports/daily` - Daily report
- `GET /api/reports/monthly` - Monthly report

#### Search & Automation
- `GET /api/search?q=query` - Global search
- `GET /api/automation/status` - Automation status
- `POST /api/automation/check-low-stock` - Trigger automation

## 🤖 Automation Features

### Active Automations
1. **Low Stock Monitoring** - Auto-creates tasks when stock is low
2. **Customer Stats Update** - Auto-updates on order creation
3. **Task Completion** - Auto-completes tasks when stock replenished
4. **Email Notifications** - Sends emails for important events (if configured)

## 📧 Email Notifications

### Supported Notifications
- Low stock alerts
- New order notifications
- Task deadline reminders

### Setup
1. Configure SMTP settings in backend/.env
2. Set EMAIL_ENABLED="true"
3. Test with: `POST /api/automation/test-email`

## 🎨 Frontend Features

### Pages
- Dashboard with KPIs and widgets
- Products management
- Stock tracking
- Orders with workflow
- Customers with timeline
- Purchases and suppliers
- Tasks management
- Expenses tracking
- Reports and analytics
- Global search
- Settings (5 tabs)

### Theme Support
- Light theme (default)
- Dark theme
- 3 accent colors: Blue, Green, Purple
- Settings persist in LocalStorage

## 📈 Performance Optimizations

### Database
- 15+ indexes created automatically
- Projection fields for efficient queries
- Async operations with Motor

### Frontend
- React component optimization
- Lazy loading (can be enhanced)
- Responsive images
- CSS variables for theming

## 🔍 Monitoring & Logging

### Backend Logs
- Location: `/app/backend/logs/`
- Daily rotation
- Separate error logs

### Health Check
```bash
curl http://localhost:8001/docs
```

## 🐛 Troubleshooting

### Backend won't start
1. Check MongoDB connection
2. Verify .env file exists
3. Check port 8001 is available
4. Review logs: `tail -f /var/log/supervisor/backend.err.log`

### Frontend won't load
1. Check backend is running
2. Verify REACT_APP_BACKEND_URL is correct
3. Check port 3000 is available
4. Clear browser cache

### Database issues
1. Verify MongoDB is running: `sudo systemctl status mongodb`
2. Check connection string in .env
3. Verify database indexes: Check startup logs

### Authentication issues
1. Clear browser LocalStorage
2. Verify JWT_SECRET_KEY is set
3. Check token expiry time

## 📦 Production Deployment

### Checklist
- [ ] Change default admin password
- [ ] Set strong SECRET_KEY in .env
- [ ] Configure proper CORS_ORIGINS
- [ ] Enable HTTPS
- [ ] Configure email (if using notifications)
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Configure database backups
- [ ] Set up reverse proxy (nginx)
- [ ] Enable rate limiting
- [ ] Configure proper logging

### Recommended Stack
- **Server**: Ubuntu 20.04+
- **Reverse Proxy**: Nginx
- **Process Manager**: Supervisor (already configured)
- **Database**: MongoDB Atlas or self-hosted
- **SSL**: Let's Encrypt
- **Monitoring**: Sentry, LogRocket, or similar

### Performance Tuning
- Enable MongoDB replica set for HA
- Use Redis for caching (future enhancement)
- Configure CDN for static assets
- Enable gzip compression
- Set up load balancing (if needed)

## 🧪 Testing

### Backend Testing
```bash
# Run comprehensive API tests
python /app/comprehensive_test.py
```

### Frontend Testing
Use built-in testing agent or manual testing.

## 📞 Support

### Common Issues
- See `/app/ISSUES_AND_IMPROVEMENTS.md` for known issues
- Check GitHub issues (if using version control)

### Version
- Current Version: 1.0.0
- Last Updated: 2024-11-29
- Production Ready: Yes ✅

## 🎯 Future Enhancements

### Planned Features
- Redis caching
- Rate limiting per endpoint
- Advanced analytics
- Multi-tenant support
- Mobile app (React Native)
- Export to Excel/PDF
- Advanced reporting
- Inventory forecasting

### Low Priority Items
See `/app/ISSUES_AND_IMPROVEMENTS.md` for detailed list.

## 📄 License

Proprietary - ZenVit AS

---

**Made with ❤️ for ZenVit**
