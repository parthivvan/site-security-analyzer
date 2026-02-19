from app import app, db, User

with app.app_context():
    # Check the user
    u = User.query.filter_by(email='parthivvanapalli@gmail.com').first()
    if u:
        print('User found: True')
        print('ID:', u.id)
        print('Email:', u.email)
        print('Password hash:', u.password_hash[:80])
        print('Failed attempts:', u.failed_login_attempts)
        print('Account locked:', u.account_locked_until)
        print('Active:', u.is_active)
        
        # Test common passwords
        test_passwords = ['Test@123', 'Test@1234', 'Parthiv@123', 'Parthiv@1234']
        print('\nTesting passwords:')
        for pwd in test_passwords:
            result = u.check_password(pwd)
            print(f'  {pwd}: {result}')
    else:
        print('User not found')
