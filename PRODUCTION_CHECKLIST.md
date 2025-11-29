# 🚀 ZenVit CRM - Production Deployment Checklist

## Pre-Deployment Checklist

### 🔐 Security
- [ ] **CRITICAL**: Change default admin password (admin@zenvit.no / admin123)
- [ ] Set strong SECRET_KEY in backend/.env (minimum 32 characters)
- [ ] Configure proper CORS_ORIGINS (not "*")
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up rate limiting
- [ ] Configure CSP (Content Security Policy) headers
- [ ] Review and update JWT_SECRET_KEY
- [ ] Disable debug mode
- [ ] Remove any test/development users

### 📧 Email Configuration (Optional)
- [ ] Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
- [ ] Set EMAIL_FROM to your company email
- [ ] Set EMAIL_ENABLED="true"
- [ ] Test email sending: `POST /api/automation/test-email`

### 🗄️ Database
- [ ] Set up MongoDB with authentication
- [ ] Configure database backups (daily recommended)
- [ ] Set proper MONGO_URL with credentials
- [ ] Verify database indexes are created (check startup logs)
- [ ] Set up monitoring for database health
- [ ] Configure replica set for high availability (recommended)

### 🌐 Frontend
- [ ] Update REACT_APP_BACKEND_URL to production URL
- [ ] Build production bundle: `yarn build`
- [ ] Configure CDN for static assets (optional)
- [ ] Enable gzip compression
- [ ] Configure proper caching headers

### 🔧 Backend
- [ ] Set proper DB_NAME in .env
- [ ] Configure proper logging level
- [ ] Set up process manager (Supervisor already configured)
- [ ] Configure reverse proxy (Nginx recommended)
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper file permissions

### 📊 Monitoring & Logging
- [ ] Set up error tracking (Sentry, Rollbar, etc.)
- [ ] Configure application monitoring (New Relic, DataDog, etc.)
- [ ] Set up log aggregation (ELK stack, CloudWatch, etc.)
- [ ] Configure uptime monitoring (Pingdom, UptimeRobot, etc.)
- [ ] Set up performance monitoring
- [ ] Configure alerts for critical errors

### 🧪 Testing
- [ ] Run full backend E2E tests
- [ ] Run full frontend E2E tests
- [ ] Perform load testing
- [ ] Test backup and restore procedures
- [ ] Verify all API endpoints work
- [ ] Test with production-like data volume

### 🚀 Deployment
- [ ] Set up CI/CD pipeline (optional)
- [ ] Configure staging environment
- [ ] Prepare rollback plan
- [ ] Document deployment procedures
- [ ] Set up blue-green deployment (optional)

### 📱 Post-Deployment
- [ ] Verify health check endpoint: GET /health
- [ ] Check system stats: GET /api/system/stats
- [ ] Monitor error logs for first 24 hours
- [ ] Verify email notifications work (if enabled)
- [ ] Test critical user flows
- [ ] Update documentation with production URLs
- [ ] Train users on the system

## Production Environment Variables

### Backend (.env)
```bash
# Database
MONGO_URL="mongodb://username:password@host:27017/?authSource=admin"
DB_NAME="zenvit_crm_production"

# Security
SECRET_KEY="your-very-secure-secret-key-minimum-32-characters-long"
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Email (Optional)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
EMAIL_FROM="noreply@zenvit.no"
EMAIL_ENABLED="true"
```

### Frontend (.env.production)
```bash
REACT_APP_BACKEND_URL="https://api.yourdomain.com"
```

## Performance Optimization Checklist

- [ ] Enable MongoDB indexes (auto-created on startup)
- [ ] Configure connection pooling
- [ ] Set up Redis caching (future enhancement)
- [ ] Enable HTTP/2
- [ ] Optimize images and static assets
- [ ] Enable browser caching
- [ ] Configure CDN for static files
- [ ] Minimize bundle size
- [ ] Enable lazy loading for large components

## Security Hardening

- [ ] Implement rate limiting per IP
- [ ] Set up WAF (Web Application Firewall)
- [ ] Configure DDoS protection
- [ ] Enable request size limits
- [ ] Set up security headers (HSTS, X-Frame-Options, etc.)
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Set up intrusion detection

## Backup Strategy

### Database Backups
- Daily full backups
- Hourly incremental backups (if high traffic)
- Retention: 30 days
- Test restore procedures monthly

### Application Backups
- Code in version control (Git)
- Configuration files backed up
- Environment variables documented

## Monitoring Metrics

### Application Metrics
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Database query time
- Memory usage
- CPU usage

### Business Metrics
- Active users
- Orders per day
- Revenue tracking
- Customer growth
- Task completion rate

## Alerts Configuration

### Critical Alerts (Immediate response)
- Service down
- Database connection failed
- Error rate > 5%
- Response time > 5 seconds

### Warning Alerts (Monitor closely)
- Error rate > 1%
- Response time > 2 seconds
- Disk space < 20%
- Memory usage > 80%

## Maintenance Schedule

### Daily
- Monitor error logs
- Check system health
- Review performance metrics

### Weekly
- Review slow queries
- Check database performance
- Update dependencies (security patches)

### Monthly
- Full system audit
- Performance optimization review
- Security review
- Backup restoration test

## Rollback Plan

### If deployment fails:
1. Stop new services
2. Restore previous version
3. Verify database integrity
4. Run health checks
5. Monitor for 30 minutes
6. Document what went wrong

### Emergency Contacts
- DevOps Lead: [Contact]
- Database Admin: [Contact]
- Security Team: [Contact]

## Success Criteria

- [ ] All services running without errors for 24 hours
- [ ] Response time < 500ms for 95% of requests
- [ ] Zero critical errors
- [ ] All user flows working
- [ ] Backup procedures verified
- [ ] Monitoring alerts configured
- [ ] Documentation complete

---

## Quick Health Check Commands

```bash
# Check API health
curl https://api.yourdomain.com/health

# Check system stats (requires auth)
curl https://api.yourdomain.com/api/system/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check frontend
curl https://yourdomain.com

# Check database
mongo --eval "db.adminCommand('ping')"

# Check logs
tail -f /app/backend/logs/zenvit_crm_*.log
```

## Support Contacts

- **Technical Support**: support@zenvit.no
- **Emergency**: [Phone number]
- **Documentation**: /app/PRODUCTION_README.md

---

**Last Updated**: 2024-11-29
**Version**: 1.0.0
