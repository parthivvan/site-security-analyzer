"""Core scan endpoint tests."""
import unittest
import sys
import os
import json
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.user import User, RefreshToken
from routes.auth import generate_access_token, generate_refresh_token


class ScanTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            self.user = User(email='scan-test@example.com')
            self.user.set_password('StrongPass123')
            db.session.add(self.user)
            db.session.commit()
            self.auth_headers = {
                'Authorization': f'Bearer {generate_access_token(self.user.id, self.user.email)}'
            }

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'healthy')

    def test_scan_success_returns_actionable_report(self):
        class FakeRaw:
            def read(self, *_args, **_kwargs):
                return b'<html><body>ok</body></html>'

        class FakeResponse:
            url = 'https://example.com'
            status_code = 200
            headers = {
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
            }
            raw = FakeRaw()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class FakeSession:
            def get(self, *_args, **_kwargs):
                return FakeResponse()

        with patch('routes.scans.create_safe_session', return_value=FakeSession()), \
             patch('routes.scans.check_dns_records', return_value={
                 'spf': {'present': True, 'score': 5},
                 'dmarc': {'present': False, 'score': 0},
             }):
            response = self.app.post(
                '/scan',
                json={'url': 'https://example.com'},
                headers=self.auth_headers,
            )

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertTrue(data['report']['https'])
        self.assertTrue(data['report']['hsts'])
        self.assertIn('priority_actions', data)
        self.assertIn('risk_snapshot', data)

    def test_scan_invalid_url(self):
        response = self.app.post('/scan', json={'url': ''}, headers=self.auth_headers)
        self.assertEqual(response.status_code, 400)

    def test_refresh_token_is_hashed_but_plaintext_still_refreshes(self):
        with app.app_context():
            plaintext = generate_refresh_token(self.user)
            stored = RefreshToken.query.filter_by(user_id=self.user.id).first()
            self.assertIsNotNone(stored)
            self.assertNotEqual(stored.token, plaintext)
            self.assertEqual(len(stored.token), 64)

        response = self.app.post('/auth/refresh', json={'refresh_token': plaintext})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json)


if __name__ == '__main__':
    unittest.main()
