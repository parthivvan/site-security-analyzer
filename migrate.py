#!/usr/bin/env python3
"""
Migration Script for Site Security Analyzer
Applies all security fixes and updates files with secure versions
"""

import os
import shutil
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

print(f"{BOLD}{BLUE}")
print("=" * 70)
print("  SITE SECURITY ANALYZER - SECURITY MIGRATION SCRIPT")
print("  Applying all 23 vulnerability fixes")
print("=" * 70)
print(RESET)

# Get project root
PROJECT_ROOT = Path(__file__).parent

# File migrations
MIGRATIONS = [
    # Backend
    {
        'src': 'backend/app_secure.py',
        'dst': 'backend/app.py',
        'backup': True,
        'description': 'Backend with all SSRF, auth, and infrastructure fixes'
    },
    {
        'src': 'backend/celery_tasks.py',
        'dst': 'backend/celery_tasks.py',
        'backup': False,  # New file
        'description': 'Celery async task queue for scanning'
    },
    {
        'src': 'backend/requirements-production.txt',
        'dst': 'backend/requirements.txt',
        'backup': True,
        'description': 'Production dependencies'
    },
    {
        'src': 'backend/start_production.sh',
        'dst': 'backend/start.sh',
        'backup': True,
        'description': 'Production startup script'
    },
    
    # Frontend
    {
        'src': 'frontend/src/api_secure.js',
        'dst': 'frontend/src/api.js',
        'backup': True,
        'description': 'Secure API client with XSS prevention'
    },
    {
        'src': 'frontend/src/SiteSecurityAnalyzer_secure.jsx',
        'dst': 'frontend/src/SiteSecurityAnalyzer.jsx',
        'backup': True,
        'description': 'XSS-safe frontend component'
    },
    
    # Extension
    {
        'src': 'extension/popup_secure.js',
        'dst': 'extension/popup.js',
        'backup': True,
        'description': 'Secure extension popup with token protection'
    },
    {
        'src': 'extension/manifest_secure.json',
        'dst': 'extension/manifest.json',
        'backup': True,
        'description': 'Secure manifest with CSP'
    },
    {
        'src': 'extension/background.js',
        'dst': 'extension/background.js',
        'backup': False,  # New file
        'description': 'Background service worker'
    },
    
    # Infrastructure
    {
        'src': 'docker-compose.yml',
        'dst': 'docker-compose.yml',
        'backup': True,
        'description': 'Production docker-compose stack'
    },
    {
        'src': '.env.example',
        'dst': '.env.example',
        'backup': False,  # Usually exists as example
        'description': 'Environment variables template'
    },
]

def create_backup(file_path):
    """Create backup of existing file"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        print(f"  {YELLOW}↳ Backup created: {backup_path}{RESET}")
        return True
    return False

def migrate_file(migration):
    """Migrate a single file"""
    src_path = PROJECT_ROOT / migration['src']
    dst_path = PROJECT_ROOT / migration['dst']
    
    print(f"\n{BOLD}Migrating: {migration['dst']}{RESET}")
    print(f"  Description: {migration['description']}")
    
    # Check if source file exists
    if not src_path.exists():
        print(f"  {RED}✗ Source file not found: {src_path}{RESET}")
        return False
    
    # Create backup if needed
    if migration['backup'] and dst_path.exists():
        create_backup(dst_path)
    
    # Create destination directory if needed
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    try:
        shutil.copy2(src_path, dst_path)
        print(f"  {GREEN}✓ Migrated successfully{RESET}")
        return True
    except Exception as e:
        print(f"  {RED}✗ Migration failed: {e}{RESET}")
        return False

def main():
    print(f"\n{BOLD}Starting migration...{RESET}\n")
    
    success_count = 0
    failed_count = 0
    
    for migration in MIGRATIONS:
        if migrate_file(migration):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print(f"\n{BOLD}{BLUE}")
    print("=" * 70)
    print("  MIGRATION SUMMARY")
    print("=" * 70)
    print(RESET)
    print(f"  {GREEN}✓ Successful: {success_count}{RESET}")
    print(f"  {RED}✗ Failed: {failed_count}{RESET}")
    
    if failed_count == 0:
        print(f"\n{GREEN}{BOLD}🎉 All migrations completed successfully!{RESET}\n")
        print(f"{YELLOW}NEXT STEPS:{RESET}")
        print(f"  1. Install frontend dependencies: {BOLD}cd frontend && npm install dompurify{RESET}")
        print(f"  2. Configure environment: {BOLD}cp .env.example .env{RESET}")
        print(f"  3. Generate secret key: {BOLD}python -c 'import secrets; print(secrets.token_urlsafe(64))'{RESET}")
        print(f"  4. Update .env with your SECRET_KEY")
        print(f"  5. Start services: {BOLD}docker-compose up -d{RESET}")
        print(f"  6. Check health: {BOLD}curl http://localhost/health{RESET}")
        print(f"\n{BLUE}See PRODUCTION_DEPLOYMENT.md for full deployment guide.{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}⚠️  Some migrations failed. Please review the errors above.{RESET}\n")
    
    # Show backup locations
    if any(m['backup'] for m in MIGRATIONS):
        print(f"{YELLOW}Backups created for existing files (*.backup){RESET}")
        print(f"  To restore: {BOLD}mv file.backup file{RESET}\n")

if __name__ == '__main__':
    main()
