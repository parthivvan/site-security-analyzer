"""
Visual Attack Graph Generator
Creates interactive D3.js attack graphs showing paths to compromise
"""
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from core.intelligence_engine import Vulnerability, VulnerabilityType


class NodeType(Enum):
    ENTRY_POINT = "entry_point"
    VULNERABILITY = "vulnerability"
    COMPROMISED_STATE = "compromised_state"
    CRITICAL_ASSET = "critical_asset"
    PRIVILEGE_LEVEL = "privilege_level"


@dataclass
class AttackNode:
    """Node in the attack graph"""
    id: str
    type: NodeType
    label: str
    description: str
    severity: str = "medium"
    exploitability: float = 0.5


@dataclass
class AttackEdge:
    """Edge representing an attack step"""
    source: str
    target: str
    action: str
    technique: str
    difficulty: str = "medium"


class AttackGraphBuilder:
    """
    Builds visual attack graphs showing paths to system compromise
    """
    
    def __init__(self):
        self.nodes: Dict[str, AttackNode] = {}
        self.edges: List[AttackEdge] = []
        self.paths: List[List[str]] = []
    
    def build_graph(self, vulnerabilities: List[Vulnerability]) -> Dict:
        """
        Build complete attack graph from vulnerabilities
        """
        # Add entry point
        self._add_entry_point()
        
        # Add vulnerability nodes
        for vuln in vulnerabilities:
            self._add_vulnerability_node(vuln)
        
        # Build attack chains
        self._build_attack_chains(vulnerabilities)
        
        # Find critical paths
        self._find_critical_paths()
        
        return self.to_dict()
    
    def _add_entry_point(self):
        """Add the initial entry point (public user)"""
        entry = AttackNode(
            id="entry_public",
            type=NodeType.ENTRY_POINT,
            label="Public User",
            description="Unauthenticated attacker",
            severity="info"
        )
        self.nodes[entry.id] = entry
    
    def _add_vulnerability_node(self, vuln: Vulnerability):
        """Add vulnerability as a node"""
        node_id = f"vuln_{hash(vuln.url + str(vuln.type))}"
        
        node = AttackNode(
            id=node_id,
            type=NodeType.VULNERABILITY,
            label=vuln.title,
            description=vuln.description,
            severity=vuln.severity.value,
            exploitability=vuln.confidence
        )
        
        self.nodes[node_id] = node
    
    def _build_attack_chains(self, vulnerabilities: List[Vulnerability]):
        """
        Build attack chains showing progression from entry to compromise
        
        Example chain:
        Public User → XSS → Steal Admin Cookie → Admin Access → 
        SQL Injection → Database Access → Server Compromise
        """
        # Group vulns by severity and type
        critical_vulns = [v for v in vulnerabilities if v.severity.value == "critical"]
        high_vulns = [v for v in vulnerabilities if v.severity.value == "high"]
        
        # Chain 1: XSS → Session Hijacking → Privilege Escalation
        xss_vulns = [v for v in vulnerabilities 
                     if v.type in [VulnerabilityType.XSS_REFLECTED, VulnerabilityType.XSS_STORED]]
        
        for vuln in xss_vulns:
            vuln_id = f"vuln_{hash(vuln.url + str(vuln.type))}"
            
            # Entry → XSS
            self.edges.append(AttackEdge(
                source="entry_public",
                target=vuln_id,
                action="Exploit XSS vulnerability",
                technique="Cross-Site Scripting",
                difficulty="low"
            ))
            
            # XSS → Cookie theft
            cookie_node_id = "state_stolen_session"
            if cookie_node_id not in self.nodes:
                self.nodes[cookie_node_id] = AttackNode(
                    id=cookie_node_id,
                    type=NodeType.COMPROMISED_STATE,
                    label="Stolen Session Cookie",
                    description="Attacker obtained admin session",
                    severity="high"
                )
            
            self.edges.append(AttackEdge(
                source=vuln_id,
                target=cookie_node_id,
                action="Steal session cookie",
                technique="Cookie theft via XSS",
                difficulty="trivial"
            ))
        
        # Chain 2: SQLi → Database Access → Server Compromise
        sqli_vulns = [v for v in vulnerabilities 
                      if v.type == VulnerabilityType.SQL_INJECTION]
        
        for vuln in sqli_vulns:
            vuln_id = f"vuln_{hash(vuln.url + str(vuln.type))}"
            
            # SQLi → Database access
            db_node_id = "asset_database"
            if db_node_id not in self.nodes:
                self.nodes[db_node_id] = AttackNode(
                    id=db_node_id,
                    type=NodeType.CRITICAL_ASSET,
                    label="Database Access",
                    description="Full database read/write access",
                    severity="critical"
                )
            
            self.edges.append(AttackEdge(
                source=vuln_id,
                target=db_node_id,
                action="Execute SQL queries",
                technique="SQL Injection",
                difficulty="medium"
            ))
            
            # Database → Server compromise (via into outfile, xp_cmdshell, etc.)
            server_node_id = "asset_server"
            if server_node_id not in self.nodes:
                self.nodes[server_node_id] = AttackNode(
                    id=server_node_id,
                    type=NodeType.CRITICAL_ASSET,
                    label="Server Compromise",
                    description="Full server control",
                    severity="critical"
                )
            
            self.edges.append(AttackEdge(
                source=db_node_id,
                target=server_node_id,
                action="Write webshell via INTO OUTFILE",
                technique="RCE via SQL Injection",
                difficulty="high"
            ))
        
        # Chain 3: IDOR → Privilege Escalation
        idor_vulns = [v for v in vulnerabilities 
                      if v.type == VulnerabilityType.IDOR]
        
        for vuln in idor_vulns:
            vuln_id = f"vuln_{hash(vuln.url + str(vuln.type))}"
            
            admin_node_id = "priv_admin"
            if admin_node_id not in self.nodes:
                self.nodes[admin_node_id] = AttackNode(
                    id=admin_node_id,
                    type=NodeType.PRIVILEGE_LEVEL,
                    label="Admin Privileges",
                    description="Escalated to administrator",
                    severity="critical"
                )
            
            self.edges.append(AttackEdge(
                source=vuln_id,
                target=admin_node_id,
                action="Access admin resources",
                technique="Insecure Direct Object Reference",
                difficulty="low"
            ))
    
    def _find_critical_paths(self):
        """Find all paths from entry to critical assets"""
        # Simple DFS to find paths
        critical_assets = [nid for nid, node in self.nodes.items() 
                          if node.type == NodeType.CRITICAL_ASSET]
        
        for asset_id in critical_assets:
            paths = self._find_paths("entry_public", asset_id)
            self.paths.extend(paths)
    
    def _find_paths(self, start: str, end: str, visited: Set[str] = None) -> List[List[str]]:
        """DFS to find all paths from start to end"""
        if visited is None:
            visited = set()
        
        if start == end:
            return [[end]]
        
        if start in visited:
            return []
        
        visited.add(start)
        paths = []
        
        # Find outgoing edges
        for edge in self.edges:
            if edge.source == start:
                sub_paths = self._find_paths(edge.target, end, visited.copy())
                for path in sub_paths:
                    paths.append([start] + path)
        
        return paths
    
    def to_dict(self) -> Dict:
        """Convert to D3.js-compatible JSON format"""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type.value,
                    "label": node.label,
                    "description": node.description,
                    "severity": node.severity,
                    "exploitability": node.exploitability
                }
                for node in self.nodes.values()
            ],
            "links": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "action": edge.action,
                    "technique": edge.technique,
                    "difficulty": edge.difficulty
                }
                for edge in self.edges
            ],
            "paths": self.paths,
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "critical_paths": len([p for p in self.paths if len(p) > 0]),
                "max_path_length": max([len(p) for p in self.paths]) if self.paths else 0
            }
        }
    
    def export_for_d3(self, filename: str = "attack_graph.json"):
        """Export graph in D3.js force-directed graph format"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return filename


# Example usage
if __name__ == "__main__":
    from core.intelligence_engine import Vulnerability, VulnerabilityType, Severity
    
    # Create sample vulnerabilities
    vulns = [
        Vulnerability(
            type=VulnerabilityType.XSS_REFLECTED,
            severity=Severity.HIGH,
            title="XSS in search",
            description="Reflected XSS vulnerability",
            url="https://example.com/search",
            parameter="q",
            remediation="Encode output",
            confidence=0.9
        ),
        Vulnerability(
            type=VulnerabilityType.SQL_INJECTION,
            severity=Severity.CRITICAL,
            title="SQLi in admin panel",
            description="SQL injection in admin",
            url="https://example.com/admin",
            parameter="id",
            remediation="Use prepared statements",
            confidence=0.95
        )
    ]
    
    # Build attack graph
    builder = AttackGraphBuilder()
    graph = builder.build_graph(vulns)
    
    print(f"Generated attack graph with {graph['statistics']['total_nodes']} nodes")
    print(f"Found {graph['statistics']['critical_paths']} attack paths")
    
    # Export for D3.js
    builder.export_for_d3()
    print("Exported to attack_graph.json")
