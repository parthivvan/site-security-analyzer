"""
Test Suite for Advanced Security Scanner
"""
import pytest
import asyncio
from core.intelligence_engine import IntelligentScanner, VulnerabilityType, Severity
from core.crawler import IntelligentCrawler
from core.exploit_generator import ExploitGenerator


class TestIntelligentScanner:
    """Test advanced vulnerability detection"""
    
    @pytest.mark.asyncio
    async def test_sqli_detection(self):
        """Test SQL injection detection"""
        scanner = IntelligentScanner()
        vulns = await scanner.scan_url(
            "https://testsite.com/page",
            params={"id": "1"}
        )
        
        # Should detect SQL injection
        assert any(v.type == VulnerabilityType.SQL_INJECTION for v in vulns)
    
    @pytest.mark.asyncio
    async def test_xss_detection(self):
        """Test XSS detection"""
        scanner = IntelligentScanner()
        vulns = await scanner.scan_url(
            "https://testsite.com/search",
            params={"q": "test"}
        )
        
        # Should detect XSS
        assert any(v.type == VulnerabilityType.XSS_REFLECTED for v in vulns)
    
    @pytest.mark.asyncio
    async def test_deep_scan(self):
        """Test comprehensive deep scan"""
        scanner = IntelligentScanner()
        result = await scanner.deep_scan("https://testsite.com")
        
        assert "vulnerabilities" in result
        assert "total_vulns" in result
        assert isinstance(result["vulnerabilities"], list)


class TestIntelligentCrawler:
    """Test autonomous crawler"""
    
    @pytest.mark.asyncio
    async def test_basic_crawl(self):
        """Test basic crawling functionality"""
        crawler = IntelligentCrawler("https://testsite.com", max_depth=2)
        result = await crawler.crawl()
        
        assert result.total_urls >= 0
        assert isinstance(result.states, list)
    
    @pytest.mark.asyncio
    async def test_form_filling(self):
        """Test smart form filling"""
        crawler = IntelligentCrawler("https://testsite.com")
        form = {
            "fields": [
                {"name": "email", "type": "email"},
                {"name": "password", "type": "password"}
            ]
        }
        
        filled = await crawler._smart_form_fill(form)
        
        assert "email" in filled
        assert "password" in filled
        assert "@" in filled["email"]


class TestExploitGenerator:
    """Test automatic exploit generation"""
    
    @pytest.mark.asyncio
    async def test_sqli_exploit_generation(self):
        """Test SQL injection exploit generation"""
        from core.intelligence_engine import Vulnerability
        
        vuln = Vulnerability(
            type=VulnerabilityType.SQL_INJECTION,
            severity=Severity.CRITICAL,
            title="SQL Injection Test",
            description="Test SQLi vuln",
            url="https://test.com/page",
            parameter="id",
            payload="' OR '1'='1",
            remediation="Use parameterized queries"
        )
        
        generator = ExploitGenerator()
        exploits = await generator.generate_exploit(vuln)
        
        assert len(exploits) > 0
        assert any(exp.language.value == "python" for exp in exploits)
    
    @pytest.mark.asyncio
    async def test_xss_exploit_generation(self):
        """Test XSS exploit generation"""
        from core.intelligence_engine import Vulnerability
        
        vuln = Vulnerability(
            type=VulnerabilityType.XSS_REFLECTED,
            severity=Severity.HIGH,
            title="XSS Test",
            description="Test XSS vuln",
            url="https://test.com/search",
            parameter="q",
            payload="<script>alert(1)</script>",
            remediation="Sanitize input and encode output"
        )
        
        generator = ExploitGenerator()
        exploits = await generator.generate_exploit(vuln)
        
        assert len(exploits) > 0
        assert any("cookie" in exp.code or "Cookie" in exp.code for exp in exploits)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
