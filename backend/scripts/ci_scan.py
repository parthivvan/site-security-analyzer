#!/usr/bin/env python3
"""
CI/CD Scanner Script
Runs security scans in CI/CD pipelines
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.intelligence_engine import IntelligentScanner
from core.risk_scorer import ContextualRiskScorer, RiskContext, AssetValue
from core.attack_graph import AttackGraphBuilder


async def run_ci_scan(target_url: str, fail_on: list = None) -> dict:
    """
    Run security scan for CI/CD environment
    """
    print(f"[*] Starting security scan of {target_url}")
    
    # Create scanner
    scanner = IntelligentScanner()
    
    # Run scan
    scan_result = await scanner.deep_scan(target_url)
    
    # Calculate risks
    risk_scorer = ContextualRiskScorer()
    context = RiskContext(
        asset_value=AssetValue.HIGH,
        is_production=True,
        is_internet_facing=True
    )
    
    vulns_with_risk = []
    for vuln in scanner.discovered_vulns:
        risk = risk_scorer.calculate_risk(vuln, context)
        vulns_with_risk.append({
            **vuln.to_dict(),
            "risk_score": risk["risk_score"],
            "priority": risk["priority"]
        })
    
    # Build attack graph
    graph_builder = AttackGraphBuilder()
    attack_graph = graph_builder.build_graph(scanner.discovered_vulns)
    
    # Prepare results
    results = {
        "target": target_url,
        "summary": scan_result,
        "vulnerabilities": vulns_with_risk,
        "attack_graph": attack_graph,
        "timestamp": scan_result.get("timestamp", "")
    }
    
    # Check for failures
    if fail_on:
        critical_count = results["summary"]["critical"]
        high_count = results["summary"]["high"]
        
        should_fail = False
        if "critical" in fail_on and critical_count > 0:
            should_fail = True
            print(f"[!] Found {critical_count} CRITICAL vulnerabilities")
        
        if "high" in fail_on and high_count > 0:
            should_fail = True
            print(f"[!] Found {high_count} HIGH vulnerabilities")
        
        if should_fail:
            print("[!] Security scan FAILED - blocking deployment")
            return results, 1
    
    print("[+] Security scan PASSED")
    return results, 0


def main():
    parser = argparse.ArgumentParser(description="CI/CD Security Scanner")
    parser.add_argument("--target", required=True, help="Target URL to scan")
    parser.add_argument("--output", default="scan-results.json", help="Output JSON file")
    parser.add_argument("--fail-on", help="Fail on severity levels (comma-separated: critical,high)")
    
    args = parser.parse_args()
    
    # Parse fail-on levels
    fail_on = args.fail_on.split(",") if args.fail_on else []
    
    # Run scan
    results, exit_code = asyncio.run(run_ci_scan(args.target, fail_on))
    
    # Write results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"[*] Results written to {args.output}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
