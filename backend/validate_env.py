#!/usr/bin/env python3
"""
Environment Validation Script for ZenVit CRM
Run this before deploying to production
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_environment():
    """Validate all required environment variables"""
    
    # Load .env file
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print("❌ ERROR: .env file not found!")
        return False
    
    load_dotenv(env_path)
    
    print("🔍 ZenVit CRM - Environment Validation")
    print("=" * 50)
    
    issues = []
    warnings = []
    
    # Required variables
    required_vars = {
        'MONGO_URL': 'Database connection string',
        'DB_NAME': 'Database name',
        'SECRET_KEY': 'JWT secret key',
        'CORS_ORIGINS': 'Allowed CORS origins'
    }
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            issues.append(f"❌ {var} is missing ({description})")
        else:
            print(f"✅ {var}: {'*' * 10} (configured)")
    
    # Security checks
    secret_key = os.getenv('SECRET_KEY', '')
    if secret_key:
        if len(secret_key) < 32:
            warnings.append(f"⚠️  SECRET_KEY is too short ({len(secret_key)} chars, recommended: 32+)")
        if 'change-in-production' in secret_key.lower() or 'your-secret' in secret_key.lower():
            issues.append("❌ SECRET_KEY contains default/insecure value!")
    
    # CORS check
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if cors_origins == '*':
        warnings.append("⚠️  CORS_ORIGINS is set to '*' (not recommended for production)")
    
    # Email configuration (optional)
    email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    if email_enabled:
        email_vars = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'EMAIL_FROM']
        for var in email_vars:
            if not os.getenv(var):
                warnings.append(f"⚠️  {var} not set (email notifications may not work)")
        print(f"✅ Email notifications: enabled")
    else:
        print(f"ℹ️  Email notifications: disabled")
    
    # Database name check
    db_name = os.getenv('DB_NAME', '')
    if db_name == 'test_database':
        warnings.append("⚠️  DB_NAME is 'test_database' (use production database name)")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    print("=" * 50)
    
    if not issues and not warnings:
        print("✅ All checks passed! Environment is production-ready.")
        return True
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")
    
    if issues:
        print(f"\n❌ Critical Issues ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")
        print("\n❌ FAILED: Fix critical issues before deploying!")
        return False
    
    print("\n✅ PASSED with warnings: Review warnings before deploying.")
    return True

if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
