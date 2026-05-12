import os
import sys

sys.path.insert(0, os.path.abspath('backend'))
from backend.app import app, db, User

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath('backend/instance/scanner.db')

email = "test123@gmail.com"
password = "Testpass@123"

with app.app_context():
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"User {email} found! Resetting password to {password} and unlocking...")
        user.set_password(password)
        user.failed_login_attempts = 0
        user.account_locked_until = None
        db.session.commit()
        print("Success!")
    else:
        print(f"User {email} NOT FOUND in backend/instance/scanner.db")
        print("Creating the test user instead...")
        new_user = User(email=email)
        new_user.set_password(password)
        new_user.is_active = True
        db.session.add(new_user)
        db.session.commit()
        print("User created successfully!")
