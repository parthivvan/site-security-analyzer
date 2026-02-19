import unittest
import sys
import os
import json

# Add parent dir to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

class ScanTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'healthy')

    def test_scan_google(self):
        # This test hits the network, might be flaky if no internet
        response = self.app.post('/scan', json={'url': 'https://google.com'})
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertTrue(data['report']['https'])
        self.assertTrue(data['report']['hsts'])
        # Google usually has these
        
    def test_scan_invalid_url(self):
        response = self.app.post('/scan', json={'url': ''})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
