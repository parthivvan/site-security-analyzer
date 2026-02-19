#!/usr/bin/env python3
"""Create a test user for login testing"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Flask app to get database context
from app import app, db, User
from werkzeug.security import generate_password_hash

def create_test_user():
    with app.app_context():
        # Check if test user already exists
        test_email = "test@example.com"
        existing_user = User.query.filter_by(email=test_email).first()
        
        if existing_user:
            print(f"✅ Test user already exists: {test_email}")
            print(f"   Password: test123")
            return
        
        # Create new test user
        test_user = User(email=test_email)
        test_user.set_password("test123")
        test_user.is_active = True
        test_user.failed_login_attempts = 0
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✅ Test user created successfully!")
        print(f"   Email: {test_email}")
        print(f"   Password: test123")
        print(f"\nYou can now login with these credentials at http://localhost:5173/login")

if __name__ == "__main__":
    try:
        create_test_user()
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        sys.exit(1)
