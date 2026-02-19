"""
Load Testing Script for Site Security Analyzer
Tests system performance under heavy load (100k+ users simulation)
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityScannerUser(HttpUser):
    """Simulates a real user interacting with the security scanner."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when user starts. Register and login."""
        # Generate unique email
        user_id = random.randint(1, 1000000)
        self.email = f"loadtest_{user_id}@test.com"
        self.password = "LoadTest123!"
        self.access_token = None
        self.refresh_token = None
        
        # Signup
        self.signup()
        
        # Login
        self.login()
    
    def signup(self):
        """Register new user."""
        response = self.client.post("/auth/signup", json={
            "email": self.email,
            "password": self.password
        }, name="/auth/signup")
        
        if response.status_code == 201:
            logger.info(f"✓ Signed up: {self.email}")
        else:
            logger.warning(f"✗ Signup failed: {response.text}")
    
    def login(self):
        """Login and get tokens."""
        response = self.client.post("/auth/login", json={
            "email": self.email,
            "password": self.password
        }, name="/auth/login")
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get('access_token')
            self.refresh_token = data.get('refresh_token')
            logger.info(f"✓ Logged in: {self.email}")
        else:
            logger.error(f"✗ Login failed for {self.email}: {response.text}")
    
    def get_auth_headers(self):
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(5)
    def scan_website(self):
        """Scan a random website (main user action)."""
        if not self.access_token:
            return
        
        # Random test domains
        domains = [
            "google.com",
            "github.com",
            "stackoverflow.com",
            "reddit.com",
            "twitter.com",
            "facebook.com",
            "amazon.com",
            "wikipedia.org"
        ]
        
        url = random.choice(domains)
        
        # Queue scan
        response = self.client.post("/scan", json={"url": url}, 
                                   headers=self.get_auth_headers(),
                                   name="/scan [queue]")
        
        if response.status_code == 202:
            task_id = response.json().get('task_id')
            
            # Poll for results (simulate real user behavior)
            for _ in range(5):  # Poll up to 5 times
                self.environment.runner.stats.get("/scan/status", "GET").log(0, 0)  # Don't count polls
                status_response = self.client.get(f"/scan/status/{task_id}",
                                                 headers=self.get_auth_headers(),
                                                 name="/scan/status/<id>")
                
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data.get('status') == 'complete':
                        logger.info(f"✓ Scan completed: {url}")
                        break
                    elif data.get('status') == 'failed':
                        logger.warning(f"✗ Scan failed: {url}")
                        break
                
                self.wait()  # Wait before next poll
        elif response.status_code == 200:
            # Cached response
            logger.info(f"↻ Cached scan: {url}")
    
    @task(2)
    def get_history(self):
        """Get scan history."""
        if not self.access_token:
            return
        
        self.client.get("/auth/history?page=1&per_page=20",
                       headers=self.get_auth_headers(),
                       name="/auth/history")
    
    @task(1)
    def refresh_token_task(self):
        """Refresh access token."""
        if not self.refresh_token:
            return
        
        response = self.client.post("/auth/refresh", json={
            "refresh_token": self.refresh_token
        }, name="/auth/refresh")
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get('access_token')
            logger.info(f"✓ Token refreshed: {self.email}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("=" * 60)
    logger.info("LOAD TEST STARTED")
    logger.info("=" * 60)
    
    if isinstance(environment.runner, MasterRunner):
        logger.info("Running in MASTER mode")
    else:
        logger.info(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    logger.info("=" * 60)
    logger.info("LOAD TEST COMPLETED")
    logger.info("=" * 60)
    
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"RPS: {stats.total.total_rps:.2f}")
    logger.info(f"Avg response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")


# Run this with:
# locust -f load_test.py --host http://localhost:5000
# 
# For 100k users simulation:
# locust -f load_test.py --host http://localhost:5000 --users 100000 --spawn-rate 1000 --run-time 10m
#
# Distributed load testing:
# Master: locust -f load_test.py --master --expect-workers 4
# Workers (run on multiple machines): locust -f load_test.py --worker --master-host <master-ip>
