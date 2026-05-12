import os
import sys

# Configure path so backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from backend.app import app, db, User

email = "test123@gmail.com"
password = "Testpass@123"

with app.app_context():
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"User {email} NOT FOUND!")
    else:
        print(f"User found: ID={user.id}, email={user.email}, is_active={user.is_active}, locked={user.is_locked()}")
        print(f"Failed attempts: {user.failed_login_attempts}")
        
        # Check password
        if user.check_password(password):
            print("Password check TRUE! Login should succeed.")
        else:
            print("Password check FALSE! Invalid password.")
            
        print("Creating user if password check was false...")
        if not user.check_password(password):
            user.set_password(password)
            user.failed_login_attempts = 0
            user.account_locked_until = None
            db.session.commit()
            print("Password reset to Testpass@123")
