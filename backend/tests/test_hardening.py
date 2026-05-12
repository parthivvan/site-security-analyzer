"""
Hardening test suite — covers auth lockout, token invalidation, header
normalization, cookie analysis, mixed content, score parity, and
Celery-disabled status endpoint.
"""
import unittest
import hashlib
import warnings
import sys
import os
import json
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.user import User, RefreshToken
from routes.auth import generate_access_token, generate_refresh_token
from utils.helpers import hash_token, utcnow
from services.scanner import (
    analyze_security_headers,
    analyze_cookies,
    analyze_page_content,
)
from services.scorer import (
    build_flat_report,
    compute_score_from_flat_report,
)


class BaseTestCase(unittest.TestCase):
    """Shared setUp/tearDown for in-memory DB tests."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            self.user = User(email='hardening@example.com')
            self.user.set_password('StrongPass1')
            db.session.add(self.user)
            db.session.commit()
            self.auth_headers = {
                'Authorization': f'Bearer {generate_access_token(self.user.id, self.user.email)}'
            }

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()


# ── Auth lockout ──────────────────────────────────────────────────────────

class TestLockoutAfter5Failures(BaseTestCase):
    """Atomic failed-login increment locks the account after 5 bad passwords."""

    def test_lockout_on_5_failures(self):
        for i in range(5):
            resp = self.client.post('/auth/login', json={
                'email': 'hardening@example.com',
                'password': 'WrongPass1'
            })
            self.assertEqual(resp.status_code, 401)

        # 6th attempt should be locked
        resp = self.client.post('/auth/login', json={
            'email': 'hardening@example.com',
            'password': 'StrongPass1'  # correct password this time
        })
        self.assertEqual(resp.status_code, 403)
        self.assertIn('locked', resp.json['error'].lower())


# ── Token invalidation ────────────────────────────────────────────────────

class TestPlaintextTokenRejection(BaseTestCase):
    """Old-style plaintext tokens must be rejected after startup migration."""

    def test_plaintext_refresh_token_rejected(self):
        """Manually insert a raw plaintext token and confirm refresh fails."""
        with app.app_context():
            legacy_token = 'this-is-a-legacy-plaintext-token'
            rt = RefreshToken(
                user_id=self.user.id,
                token=legacy_token,
                expires_at=utcnow() + __import__('datetime').timedelta(days=7),
                revoked=False,
            )
            db.session.add(rt)
            db.session.commit()

            db.session.execute(db.text(
                "UPDATE refresh_tokens SET revoked = 1 "
                "WHERE revoked = 0 AND length(token) != 64"
            ))
            db.session.commit()

        resp = self.client.post('/auth/refresh', json={
            'refresh_token': legacy_token
        })
        self.assertEqual(resp.status_code, 401)

    def test_hashed_token_still_works(self):
        with app.app_context():
            plaintext = generate_refresh_token(self.user)
        resp = self.client.post('/auth/refresh', json={'refresh_token': plaintext})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.json)


# ── Reset token hashing ──────────────────────────────────────────────────

class TestResetTokenHashing(BaseTestCase):
    """Password reset tokens must be stored hashed."""

    def test_reset_token_stored_hashed(self):
        resp = self.client.post('/auth/forgot-password', json={
            'email': 'hardening@example.com'
        })
        self.assertEqual(resp.status_code, 200)

        with app.app_context():
            user = User.query.filter_by(email='hardening@example.com').first()
            self.assertIsNotNone(user.reset_token)
            self.assertEqual(len(user.reset_token), 64)


# ── Header normalization ─────────────────────────────────────────────────

class TestLowercaseHeaders(unittest.TestCase):
    """analyze_security_headers must work with any case keys."""

    def test_lowercase_keys(self):
        headers = {
            'strict-transport-security': 'max-age=31536000; includeSubDomains',
            'x-frame-options': 'DENY',
            'x-content-type-options': 'nosniff',
            'referrer-policy': 'no-referrer',
            'content-security-policy': "default-src 'self'",
        }
        findings = analyze_security_headers(headers, 'https://example.com')
        self.assertTrue(findings['hsts']['present'])
        self.assertTrue(findings['csp']['present'])
        self.assertTrue(findings['x_frame_options']['present'])
        self.assertTrue(findings['x_content_type_options']['present'])
        self.assertTrue(findings['referrer_policy']['present'])

    def test_mixed_case_keys(self):
        headers = {
            'Strict-Transport-Security': 'max-age=31536000',
            'X-FRAME-OPTIONS': 'SAMEORIGIN',
        }
        findings = analyze_security_headers(headers, 'https://example.com')
        self.assertTrue(findings['hsts']['present'])
        self.assertTrue(findings['x_frame_options']['present'])

    def test_empty_headers(self):
        findings = analyze_security_headers({}, 'http://example.com')
        self.assertFalse(findings['https']['present'])
        self.assertFalse(findings['hsts']['present'])

    def test_none_headers(self):
        findings = analyze_security_headers(None, 'http://example.com')
        self.assertFalse(findings['https']['present'])


# ── Cookie analysis ───────────────────────────────────────────────────────

class TestCookieAnalysis(unittest.TestCase):

    def test_no_cookies(self):
        result = analyze_cookies({})
        self.assertFalse(result['cookies']['present'])

    def test_insecure_cookies(self):
        class FakeHeaders:
            def getlist(self, name):
                if name == 'Set-Cookie':
                    return ['session=abc123', 'tracking=xyz; HttpOnly']
                return []
        result = analyze_cookies(FakeHeaders())
        self.assertTrue(result['cookies']['present'])
        self.assertEqual(result['cookies']['cookie_count'], 2)
        self.assertGreater(len(result['cookies']['issues']), 0)
        self.assertEqual(result['cookies']['severity'], 'warning')

    def test_secure_cookies(self):
        class FakeHeaders:
            def getlist(self, name):
                if name == 'Set-Cookie':
                    return ['session=abc123; Secure; HttpOnly; SameSite=Strict']
                return []
        result = analyze_cookies(FakeHeaders())
        self.assertTrue(result['cookies']['present'])
        self.assertEqual(result['cookies']['issues'], [])
        self.assertEqual(result['cookies']['severity'], 'pass')


# ── Mixed content ─────────────────────────────────────────────────────────

class TestMixedContent(unittest.TestCase):

    def test_mixed_content_detected(self):
        html = b'<html><body><img src="http://evil.com/pic.jpg"></body></html>'
        findings = analyze_page_content(html, 'https://example.com')
        self.assertTrue(findings['mixed_content']['present'])
        self.assertEqual(findings['mixed_content']['count'], 1)

    def test_no_mixed_content(self):
        html = b'<html><body><img src="https://safe.com/pic.jpg"></body></html>'
        findings = analyze_page_content(html, 'https://example.com')
        self.assertFalse(findings['mixed_content']['present'])

    def test_http_page_skips_mixed_content(self):
        html = b'<html><body><img src="http://cdn.com/pic.jpg"></body></html>'
        findings = analyze_page_content(html, 'http://example.com')
        self.assertNotIn('mixed_content', findings)


# ── Score parity ──────────────────────────────────────────────────────────

class TestScoreFromFlatReport(unittest.TestCase):

    def test_perfect_score(self):
        flat = {
            'https': True, 'hsts': True, 'content_security_policy': True,
            'x_frame_options': True, 'x_content_type_options': True,
            'referrer_policy': True, 'permissions_policy': True,
            'dns_spf': True, 'dns_dmarc': True, 'cookies': True,
            'server_header': False, 'mixed_content': False,
        }
        self.assertEqual(compute_score_from_flat_report(flat), 95)

    def test_zero_score(self):
        flat = {k: False for k in [
            'https', 'hsts', 'content_security_policy', 'x_frame_options',
            'x_content_type_options', 'referrer_policy', 'permissions_policy',
            'dns_spf', 'dns_dmarc', 'cookies',
        ]}
        flat['server_header'] = True
        flat['mixed_content'] = True
        score = compute_score_from_flat_report(flat)
        self.assertEqual(score, 0)

    def test_partial_score(self):
        flat = {
            'https': True, 'hsts': True, 'content_security_policy': False,
            'x_frame_options': False, 'x_content_type_options': True,
            'referrer_policy': False, 'permissions_policy': False,
            'dns_spf': True, 'dns_dmarc': False, 'cookies': False,
            'server_header': False, 'mixed_content': False,
        }
        self.assertEqual(compute_score_from_flat_report(flat), 50)


# ── Celery-disabled status ────────────────────────────────────────────────

class TestCeleryDisabledStatus(BaseTestCase):
    def test_status_returns_error_when_celery_disabled(self):
        resp = self.client.get('/scan/status/fake-task-id', headers=self.auth_headers)
        self.assertEqual(resp.status_code, 400)


# ── build_flat_report contract ────────────────────────────────────────────

class TestBuildFlatReport(unittest.TestCase):

    def test_all_keys_present(self):
        header_findings = {
            'https': {'present': True}, 'hsts': {'present': True, 'max_age': 31536000},
            'csp': {'present': True, 'issues': []}, 'x_frame_options': {'present': True},
            'x_content_type_options': {'present': True}, 'referrer_policy': {'present': True},
            'permissions_policy': {'present': True}, 'server_disclosure': {'present': False},
        }
        dns_findings = {'spf': {'present': True}, 'dmarc': {'present': True}}
        cookie_findings = {'cookies': {'present': True, 'issues': []}}
        content_findings = {'mixed_content': {'present': False}}
        flat = build_flat_report(header_findings, dns_findings, cookie_findings, content_findings)
        expected_keys = {
            'https', 'hsts', 'content_security_policy', 'x_frame_options',
            'x_content_type_options', 'referrer_policy', 'permissions_policy',
            'server_header', 'dns_spf', 'dns_dmarc', 'cookies', 'mixed_content'
        }
        self.assertEqual(set(flat.keys()), expected_keys)

    def test_weak_hsts_fails(self):
        header_findings = {
            'https': {'present': True}, 'hsts': {'present': True, 'max_age': 100},
            'csp': {'present': False}, 'x_frame_options': {'present': False},
            'x_content_type_options': {'present': False}, 'referrer_policy': {'present': False},
            'permissions_policy': {'present': False},
        }
        flat = build_flat_report(header_findings, {}, {}, {})
        self.assertFalse(flat['hsts'])

    def test_csp_with_unsafe_inline_fails(self):
        header_findings = {
            'https': {'present': True}, 'hsts': {'present': False},
            'csp': {'present': True, 'issues': ["unsafe-inline allows inline scripts"]},
            'x_frame_options': {'present': False}, 'x_content_type_options': {'present': False},
            'referrer_policy': {'present': False}, 'permissions_policy': {'present': False},
        }
        flat = build_flat_report(header_findings, {}, {}, {})
        self.assertFalse(flat['content_security_policy'])


if __name__ == '__main__':
    unittest.main()
