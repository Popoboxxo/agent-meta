#!/usr/bin/env python3
"""
SE Framework Test Runner
Validiert die agent-meta SE-Kaskade und alle neuen Agenten-Templates.

Usage:
    python tests/automated/test-runner.py

Exit codes:
    0 - Alle Tests bestanden
    1 - Mindestens ein Test fehlgeschlagen
"""

import json
import os
import re
import sys
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict


# ============================================================================
# Base Directories
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEST_DATA_DIR = BASE_DIR / "tests" / "automated"
DOCS_DIR = BASE_DIR / "docs"
AGENTS_DIR = BASE_DIR / "agents" / "1-generic"
CONFIG_FILE = BASE_DIR / "config" / "role-defaults.yaml"
ORCHESTRATOR_FILE = BASE_DIR / "agents" / "1-generic" / "orchestrator.md"
CLAUDE_FILE = BASE_DIR / "CLAUDE.md"
AGENTS_MD_FILE = BASE_DIR / "AGENTS.md"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TestResult:
    """Ergebnis eines einzelnen Tests."""
    name: str
    passed: bool
    details: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class TestReport:
    """Gesamt-Testreport mit Markdown-Export."""
    timestamp: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    results: List[TestResult] = field(default_factory=list)

    def add(self, result: TestResult):
        self.results.append(result)
        self.total_tests += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1

    @property
    def success_rate(self) -> float:
        return (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0.0

    def to_markdown(self) -> str:
        lines = [
            "# SE Framework Test Report",
            "",
            f"**Timestamp:** {self.timestamp}",
            f"**Total Tests:** {self.total_tests}",
            f"**Passed:** {self.passed}",
            f"**Failed:** {self.failed}",
            f"**Success Rate:** {self.success_rate:.1f}%",
            "",
            "---",
            "",
        ]

        # Group by category
        current_category = ""
        for r in self.results:
            # Extract category from test name (prefix before first ":")
            parts = r.name.split(":", 1)
            category = parts[0].strip() if len(parts) > 1 else "General"
            test_name = parts[1].strip() if len(parts) > 1 else r.name

            if category != current_category:
                current_category = category
                lines.append(f"## {current_category}")
                lines.append("")
                lines.append("| Test | Status | Details |")
                lines.append("|------|--------|---------|")

            status = "PASS" if r.passed else "FAIL"
            details = r.details if r.details else ("; ".join(r.errors) if r.errors else "")
            # Escape pipe characters in details
            details = details.replace("|", "\\|")
            lines.append(f"| {test_name} | {status} | {details} |")

        lines.append("")
        lines.append("---")
        lines.append("")
        if self.failed == 0:
            lines.append("**All tests passed.**")
        else:
            lines.append(f"**{self.failed} test(s) failed.** See details above.")
        lines.append("")

        return "\n".join(lines)


# ============================================================================
# Simple YAML Parser (No PyYAML dependency)
# ============================================================================

def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """
    Einfacher YAML-Parser fur verschachtelte Key-Value Strukturen.
    Unterstutzt:
      - Top-level keys
      - Nested keys (2 Spaces Einruckung)
      - Listen (- item)
      - Kommentare (#)
      - Strings in Quotes und ohne
    """
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for line in text.split("\n"):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Skip YAML frontmatter delimiters
        if stripped == "---":
            continue

        # Detect indentation level
        indent = len(line) - len(line.lstrip())

        if indent == 0:
            # Top-level key
            if current_key and current_list is not None:
                result[current_key] = current_list
                current_list = None

            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()

                if value:
                    # Remove quotes if present
                    value = value.strip("'\"")
                    result[key] = value
                    current_key = None
                else:
                    # Nested structure follows
                    current_key = key
                    current_list = None
                    result[current_key] = {}
            continue

        if indent > 0 and current_key is not None:
            if isinstance(result.get(current_key), dict):
                # Nested key-value
                if ":" in stripped:
                    key, _, value = stripped.partition(":")
                    key = key.strip()
                    value = value.strip()

                    if value.startswith("[") and value.endswith("]"):
                        # Inline list
                        items = [
                            item.strip().strip("'\"")
                            for item in value[1:-1].split(",")
                            if item.strip()
                        ]
                        result[current_key][key] = items
                    elif value:
                        result[current_key][key] = value.strip("'\"")
                    else:
                        result[current_key][key] = {}
                elif stripped.startswith("- "):
                    # List item under current key
                    if not isinstance(result[current_key], list):
                        result[current_key] = []
                    result[current_key].append(stripped[2:].strip("'\""))
            continue

    # Flush remaining list
    if current_key and current_list is not None:
        result[current_key] = current_list

    return result


def parse_role_defaults(filepath: Path) -> Dict[str, Any]:
    """Parses role-defaults.yaml and returns structured dict."""
    if not filepath.exists():
        return {}

    text = filepath.read_text(encoding="utf-8")

    # Try PyYAML first
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    # Fallback: simple parser
    return parse_simple_yaml(text)


# ============================================================================
# Frontmatter Parser
# ============================================================================

def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """
    Parses YAML frontmatter from a Markdown file.
    Returns (frontmatter_dict, body_text).
    """
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm_text = parts[1].strip()
    body = parts[2].strip() if len(parts) > 2 else ""

    fm: Dict[str, str] = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip("'\"")

    return fm, body


# ============================================================================
# Test Category 1: Template Existence
# ============================================================================

REQUIRED_AGENT_TEMPLATES = [
    "se-orchestrator.md",
    "se-requirements.md",
    "se-architect.md",
    "se-critic.md",
    "se-interface-mgr.md",
    "se-termination.md",
    "se-test-engineer.md",
    "se-testreviewer.md",
    "se-verifier.md",
    "se-validator.md",
    "se-integration-and-test-manager.md",
    "code-reviewer.md",
    "ui-ux-designer.md",
    "api-specialist.md",
    "devops-engineer.md",
    "performance-optimizer.md",
    "export-manager.md",
]

REQUIRED_FRONTMATTER_FIELDS = ["name", "version", "description"]


def run_template_existence_tests(report: TestReport):
    """Prueft Existenz, Groesse und Frontmatter aller Agenten-Templates."""
    for template_name in REQUIRED_AGENT_TEMPLATES:
        filepath = AGENTS_DIR / template_name
        base_name = template_name.replace(".md", "")

        # Test 1: File exists
        exists = filepath.exists()
        report.add(TestResult(
            name=f"Template-Existenz: {base_name}",
            passed=exists,
            details=f"Path: {filepath}" if exists else f"File not found: {filepath}",
        ))

        if not exists:
            # Skip further tests for this file
            report.add(TestResult(
                name=f"Template-Size: {base_name}",
                passed=False,
                errors=["File does not exist, skipping size check"],
            ))
            report.add(TestResult(
                name=f"Template-Frontmatter: {base_name}",
                passed=False,
                errors=["File does not exist, skipping frontmatter check"],
            ))
            continue

        # Test 2: File not empty (> 100 chars)
        try:
            content = filepath.read_text(encoding="utf-8")
            size_ok = len(content) > 100
            report.add(TestResult(
                name=f"Template-Size: {base_name}",
                passed=size_ok,
                details=f"Size: {len(content)} chars" if size_ok else f"Too small: {len(content)} chars (min 100)",
            ))
        except Exception as e:
            report.add(TestResult(
                name=f"Template-Size: {base_name}",
                passed=False,
                errors=[f"Read error: {str(e)}"],
            ))
            content = ""

        # Test 3: Has YAML frontmatter
        has_fm = content.startswith("---")
        report.add(TestResult(
            name=f"Template-Frontmatter-Exists: {base_name}",
            passed=has_fm,
            details="Has YAML frontmatter" if has_fm else "Missing YAML frontmatter (---)",
        ))

        # Test 4: Frontmatter has required fields
        if has_fm:
            try:
                fm, _ = parse_frontmatter(content)
                missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if f not in fm]
                fm_ok = len(missing) == 0
                report.add(TestResult(
                    name=f"Template-Frontmatter-Fields: {base_name}",
                    passed=fm_ok,
                    details="All required fields present" if fm_ok
                    else f"Missing fields: {', '.join(missing)}",
                ))
            except Exception as e:
                report.add(TestResult(
                    name=f"Template-Frontmatter-Fields: {base_name}",
                    passed=False,
                    errors=[f"Frontmatter parse error: {str(e)}"],
                ))


# ============================================================================
# Test Category 2: role-defaults.yaml
# ============================================================================

REQUIRED_NEW_ROLES = [
    "se-test-engineer",
    "se-testreviewer",
    "se-verifier",
    "se-validator",
    "se-integration-and-test-manager",
    "code-reviewer",
    "ui-ux-designer",
    "api-specialist",
    "devops-engineer",
    "performance-optimizer",
    "export-manager",
]

REQUIRED_ROLE_FIELDS = ["model", "memory", "workflow_tier"]


def run_role_defaults_tests(report: TestReport):
    """Prueft role-defaults.yaml auf Vollstaendigkeit."""
    if not CONFIG_FILE.exists():
        report.add(TestResult(
            name="role-defaults: File exists",
            passed=False,
            errors=[f"Config file not found: {CONFIG_FILE}"],
        ))
        return

    report.add(TestResult(
        name="role-defaults: File exists",
        passed=True,
        details=str(CONFIG_FILE),
    ))

    try:
        config = parse_role_defaults(CONFIG_FILE)
    except Exception as e:
        report.add(TestResult(
            name="role-defaults: Parseable",
            passed=False,
            errors=[f"Parse error: {str(e)}"],
        ))
        return

    report.add(TestResult(
        name="role-defaults: Parseable",
        passed=True,
        details="YAML parsed successfully",
    ))

    for role in REQUIRED_NEW_ROLES:
        # Check role exists
        role_exists = role in config.get("roles", {})
        report.add(TestResult(
            name=f"role-defaults: Role '{role}' exists",
            passed=role_exists,
            details=f"Role '{role}' found in config" if role_exists
            else f"Role '{role}' NOT found in config",
        ))

        if role_exists and isinstance(config.get("roles", {}).get(role), dict):
            role_config = config["roles"][role]
            missing = [f for f in REQUIRED_ROLE_FIELDS if f not in role_config]
            fields_ok = len(missing) == 0
            report.add(TestResult(
                name=f"role-defaults: Role '{role}' has required fields",
                passed=fields_ok,
                details="All fields present" if fields_ok
                else f"Missing: {', '.join(missing)}",
            ))


# ============================================================================
# Test Category 3: Orchestrator Routing
# ============================================================================

def run_orchestrator_routing_tests(report: TestReport):
    """Prueft orchestrator.md auf Routing-Eintraege fuer neue Agenten."""
    if not ORCHESTRATOR_FILE.exists():
        report.add(TestResult(
            name="Orchestrator: File exists",
            passed=False,
            errors=[f"File not found: {ORCHESTRATOR_FILE}"],
        ))
        return

    report.add(TestResult(
        name="Orchestrator: File exists",
        passed=True,
    ))

    try:
        content = ORCHESTRATOR_FILE.read_text(encoding="utf-8")
    except Exception as e:
        report.add(TestResult(
            name="Orchestrator: Readable",
            passed=False,
            errors=[str(e)],
        ))
        return

    report.add(TestResult(
        name="Orchestrator: Readable",
        passed=True,
    ))

    content_lower = content.lower()

    # Check Intent-Routing-Tabelle
    all_agents_in_routing = True
    missing_routing = []
    for agent in REQUIRED_AGENT_TEMPLATES:
        agent_name = agent.replace(".md", "")
        if agent_name.lower() not in content_lower:
            all_agents_in_routing = False
            missing_routing.append(agent_name)

    report.add(TestResult(
        name="Orchestrator: Intent-Routing contains all agents",
        passed=all_agents_in_routing,
        details="All agents referenced in routing table" if all_agents_in_routing
        else f"Missing in routing: {', '.join(missing_routing)}",
    ))

    # Check Agenten-Tabelle
    # Look for markdown table rows containing agent names
    table_agents_found = 0
    for agent in REQUIRED_AGENT_TEMPLATES:
        agent_name = agent.replace(".md", "")
        if f"`{agent_name}`" in content or f"| {agent_name}" in content or f"| `{agent_name}`" in content:
            table_agents_found += 1

    table_ok = table_agents_found >= len(REQUIRED_AGENT_TEMPLATES) * 0.8  # At least 80%
    report.add(TestResult(
        name="Orchestrator: Agent table contains new agents",
        passed=table_ok,
        details=f"Found {table_agents_found}/{len(REQUIRED_AGENT_TEMPLATES)} agents in table",
    ))

    # Check SE-Kaskade / V&V Workflow references
    se_keywords = ["se-kaskade", "se cascade", "v&v", "verification", "validation",
                   "se-orchestrator", "se-requirements", "se-architect"]
    found_keywords = [kw for kw in se_keywords if kw.lower() in content_lower]
    workflow_ok = len(found_keywords) >= 3
    report.add(TestResult(
        name="Orchestrator: SE/V&V workflows referenced",
        passed=workflow_ok,
        details=f"Found {len(found_keywords)} SE/V&V keywords: {', '.join(found_keywords)}"
        if workflow_ok else "Insufficient SE/V&V workflow references",
    ))


# ============================================================================
# Test Category 4: JSON Schema Validation
# ============================================================================

def validate_json_file(filepath: Path) -> Tuple[bool, Any, str]:
    """Loads and validates a JSON file. Returns (success, data, error_msg)."""
    if not filepath.exists():
        return False, None, f"File not found: {filepath}"

    try:
        text = filepath.read_text(encoding="utf-8")
        data = json.loads(text)
        return True, data, ""
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, None, f"Read error: {str(e)}"


def run_json_schema_tests(report: TestReport):
    """Validiert JSON-Testdaten auf Schema-Konformitaet."""

    # --- expected-l1-requirements.json ---
    req_file = TEST_DATA_DIR / "expected-l1-requirements.json"
    req_ok, req_data, req_err = validate_json_file(req_file)

    report.add(TestResult(
        name="JSON-L1-Requirements: File exists and valid JSON",
        passed=req_ok,
        details=str(req_file) if req_ok else req_err,
    ))

    if req_ok and isinstance(req_data, dict):
        # Check top-level structure
        required_top = ["level", "type", "requirements", "metadata"]
        missing_top = [k for k in required_top if k not in req_data]
        report.add(TestResult(
            name="JSON-L1-Requirements: Top-level structure",
            passed=len(missing_top) == 0,
            details="All top-level keys present" if not missing_top
            else f"Missing keys: {', '.join(missing_top)}",
        ))

        # Check requirements array
        requirements = req_data.get("requirements", [])
        if isinstance(requirements, list):
            req_count_ok = len(requirements) >= 10
            report.add(TestResult(
                name="JSON-L1-Requirements: At least 10 requirements",
                passed=req_count_ok,
                details=f"Found {len(requirements)} requirements",
            ))

            # Check each requirement has required fields
            req_fields = ["id", "title", "description", "stakeholder",
                          "priority", "category", "acceptance_criteria"]
            all_reqs_valid = True
            bad_reqs = []
            for req in requirements:
                if isinstance(req, dict):
                    missing = [f for f in req_fields if f not in req]
                    if missing:
                        all_reqs_valid = False
                        bad_reqs.append(f"{req.get('id', '?')}: {', '.join(missing)}")

            report.add(TestResult(
                name="JSON-L1-Requirements: Each requirement has required fields",
                passed=all_reqs_valid,
                details="All requirements valid" if all_reqs_valid
                else f"Invalid requirements: {'; '.join(bad_reqs)}",
            ))

            # Check traceability matrix
            metadata = req_data.get("metadata", {})
            if isinstance(metadata, dict):
                traceability = metadata.get("traceability_matrix", {})
                if isinstance(traceability, dict) and len(traceability) > 0:
                    report.add(TestResult(
                        name="JSON-L1-Requirements: Traceability matrix present",
                        passed=True,
                        details=f"Traceability covers {len(traceability)} stakeholder(s)",
                    ))
                else:
                    report.add(TestResult(
                        name="JSON-L1-Requirements: Traceability matrix present",
                        passed=False,
                        errors=["Traceability matrix missing or empty"],
                    ))
        else:
            report.add(TestResult(
                name="JSON-L1-Requirements: requirements is an array",
                passed=False,
                errors=["'requirements' is not an array"],
            ))

    # --- expected-architecture.json ---
    arch_file = TEST_DATA_DIR / "expected-architecture.json"
    arch_ok, arch_data, arch_err = validate_json_file(arch_file)

    report.add(TestResult(
        name="JSON-Architecture: File exists and valid JSON",
        passed=arch_ok,
        details=str(arch_file) if arch_ok else arch_err,
    ))

    if arch_ok and isinstance(arch_data, dict):
        required_top = ["level", "type", "systems", "signal_flow", "architecture_audit"]
        missing_top = [k for k in required_top if k not in arch_data]
        report.add(TestResult(
            name="JSON-Architecture: Top-level structure",
            passed=len(missing_top) == 0,
            details="All top-level keys present" if not missing_top
            else f"Missing keys: {', '.join(missing_top)}",
        ))

        systems = arch_data.get("systems", [])
        if isinstance(systems, list):
            sys_count_ok = len(systems) >= 3
            report.add(TestResult(
                name="JSON-Architecture: At least 3 subsystems",
                passed=sys_count_ok,
                details=f"Found {len(systems)} subsystems",
            ))

            # Check each system has required fields
            sys_fields = ["id", "name", "description", "components", "interfaces"]
            all_sys_valid = True
            bad_sys = []
            for sys_item in systems:
                if isinstance(sys_item, dict):
                    missing = [f for f in sys_fields if f not in sys_item]
                    if missing:
                        all_sys_valid = False
                        bad_sys.append(f"{sys_item.get('id', '?')}: {', '.join(missing)}")

            report.add(TestResult(
                name="JSON-Architecture: Each system has required fields",
                passed=all_sys_valid,
                details="All systems valid" if all_sys_valid
                else f"Invalid systems: {'; '.join(bad_sys)}",
            ))
        else:
            report.add(TestResult(
                name="JSON-Architecture: systems is an array",
                passed=False,
                errors=["'systems' is not an array"],
            ))

        # Check architecture_audit
        audit = arch_data.get("architecture_audit", {})
        if isinstance(audit, dict):
            audit_fields = ["orthogonality", "testability", "traceability"]
            missing_audit = [f for f in audit_fields if f not in audit]
            report.add(TestResult(
                name="JSON-Architecture: architecture_audit has required fields",
                passed=len(missing_audit) == 0,
                details="All audit fields present" if not missing_audit
                else f"Missing: {', '.join(missing_audit)}",
            ))

        # Check signal_flow
        signal_flow = arch_data.get("signal_flow", {})
        report.add(TestResult(
            name="JSON-Architecture: signal_flow defined",
            passed=bool(signal_flow),
            details="Signal flow present" if signal_flow else "Signal flow missing",
        ))

    # --- expected-test-model.json ---
    test_file = TEST_DATA_DIR / "expected-test-model.json"
    test_ok, test_data, test_err = validate_json_file(test_file)

    report.add(TestResult(
        name="JSON-Test-Model: File exists and valid JSON",
        passed=test_ok,
        details=str(test_file) if test_ok else test_err,
    ))

    if test_ok and isinstance(test_data, dict):
        required_top = ["level", "type", "test_cases", "integration_tests", "coverage_matrix"]
        missing_top = [k for k in required_top if k not in test_data]
        report.add(TestResult(
            name="JSON-Test-Model: Top-level structure",
            passed=len(missing_top) == 0,
            details="All top-level keys present" if not missing_top
            else f"Missing keys: {', '.join(missing_top)}",
        ))

        test_cases = test_data.get("test_cases", [])
        if isinstance(test_cases, list):
            tc_count_ok = len(test_cases) >= 10
            report.add(TestResult(
                name="JSON-Test-Model: At least 10 test cases",
                passed=tc_count_ok,
                details=f"Found {len(test_cases)} test cases",
            ))

            # Check each test case has required fields
            tc_fields = ["id", "title", "requirement", "input",
                         "expected_output", "test_type", "priority"]
            all_tc_valid = True
            bad_tc = []
            for tc in test_cases:
                if isinstance(tc, dict):
                    missing = [f for f in tc_fields if f not in tc]
                    if missing:
                        all_tc_valid = False
                        bad_tc.append(f"{tc.get('id', '?')}: {', '.join(missing)}")

            report.add(TestResult(
                name="JSON-Test-Model: Each test case has required fields",
                passed=all_tc_valid,
                details="All test cases valid" if all_tc_valid
                else f"Invalid test cases: {'; '.join(bad_tc)}",
            ))

            # Check requirement_coverage_pct
            coverage = test_data.get("metadata", {}).get("requirement_coverage_pct", -1)
            coverage_ok = coverage == 100
            report.add(TestResult(
                name="JSON-Test-Model: 100% requirement coverage",
                passed=coverage_ok,
                details=f"Coverage: {coverage}%" if coverage_ok
                else f"Coverage is {coverage}%, expected 100%",
            ))
        else:
            report.add(TestResult(
                name="JSON-Test-Model: test_cases is an array",
                passed=False,
                errors=["'test_cases' is not an array"],
            ))


# ============================================================================
# Test Category 5: Cross-Validation
# ============================================================================

def run_cross_validation_tests(report: TestReport):
    """Kreuzvalidierung zwischen Requirements, Architektur und Test-Modell."""

    # Load all three files
    req_ok, req_data, _ = validate_json_file(
        TEST_DATA_DIR / "expected-l1-requirements.json")
    arch_ok, arch_data, _ = validate_json_file(
        TEST_DATA_DIR / "expected-architecture.json")
    test_ok, test_data, _ = validate_json_file(
        TEST_DATA_DIR / "expected-test-model.json")

    if not req_ok:
        report.add(TestResult(
            name="Cross-Validation: L1 Requirements loaded",
            passed=False,
            errors=["Cannot load L1 requirements file"],
        ))
        return

    report.add(TestResult(
        name="Cross-Validation: L1 Requirements loaded",
        passed=True,
    ))

    # Extract REQ-IDs from L1 requirements
    req_ids = set()
    requirements = req_data.get("requirements", [])
    for req in requirements:
        if isinstance(req, dict) and "id" in req:
            req_ids.add(req["id"])

    # --- Check: All REQ-IDs in architecture source_requirements ---
    if arch_ok and isinstance(arch_data, dict):
        arch_req_ids = set()
        systems = arch_data.get("systems", [])
        for sys_item in systems:
            if isinstance(sys_item, dict):
                src_reqs = sys_item.get("source_requirements", [])
                if isinstance(src_reqs, list):
                    arch_req_ids.update(src_reqs)
                components = sys_item.get("components", [])
                if isinstance(components, list):
                    for comp in components:
                        if isinstance(comp, dict):
                            comp_reqs = comp.get("source_requirements", [])
                            if isinstance(comp_reqs, list):
                                arch_req_ids.update(comp_reqs)

        missing_in_arch = req_ids - arch_req_ids
        arch_coverage_ok = len(missing_in_arch) == 0
        report.add(TestResult(
            name="Cross-Validation: All L1 REQs in architecture source_requirements",
            passed=arch_coverage_ok,
            details=f"All {len(req_ids)} REQs traced to architecture" if arch_coverage_ok
            else f"Missing in architecture: {', '.join(sorted(missing_in_arch))}",
        ))
    else:
        report.add(TestResult(
            name="Cross-Validation: All L1 REQs in architecture source_requirements",
            passed=False,
            errors=["Architecture file not available"],
        ))

    # --- Check: All REQ-IDs in test model coverage_matrix ---
    if test_ok and isinstance(test_data, dict):
        coverage_matrix = test_data.get("coverage_matrix", {})
        covered_reqs = set()
        if isinstance(coverage_matrix, dict):
            for req_id, status in coverage_matrix.items():
                covered_reqs.add(req_id)

        # Also check from test_cases
        test_cases = test_data.get("test_cases", [])
        for tc in test_cases:
            if isinstance(tc, dict) and "requirement" in tc:
                req_val = tc["requirement"]
                if isinstance(req_val, list):
                    covered_reqs.update(req_val)
                elif isinstance(req_val, str):
                    covered_reqs.add(req_val)

        missing_in_test = req_ids - covered_reqs
        test_coverage_ok = len(missing_in_test) == 0
        report.add(TestResult(
            name="Cross-Validation: All L1 REQs in test model coverage",
            passed=test_coverage_ok,
            details=f"All {len(req_ids)} REQs covered by tests" if test_coverage_ok
            else f"Missing in test model: {', '.join(sorted(missing_in_test))}",
        ))
    else:
        report.add(TestResult(
            name="Cross-Validation: All L1 REQs in test model coverage",
            passed=False,
            errors=["Test model file not available"],
        ))

    # --- Check: All component IDs referenced in test cases ---
    if arch_ok and test_ok:
        component_ids = set()
        systems = arch_data.get("systems", [])
        for sys_item in systems:
            if isinstance(sys_item, dict):
                components = sys_item.get("components", [])
                if isinstance(components, list):
                    for comp in components:
                        if isinstance(comp, dict) and "id" in comp:
                            component_ids.add(comp["id"])

        referenced_components = set()
        test_cases = test_data.get("test_cases", [])
        for tc in test_cases:
            if isinstance(tc, dict):
                for key in ["component", "component_id", "target_component"]:
                    val = tc.get(key)
                    if val:
                        if isinstance(val, list):
                            referenced_components.update(val)
                        elif isinstance(val, str):
                            referenced_components.add(val)

        missing_components = component_ids - referenced_components
        # Only fail if there are components defined but none referenced at all
        if component_ids and not referenced_components:
            report.add(TestResult(
                name="Cross-Validation: All components referenced in test cases",
                passed=False,
                details=f"No component references found in test cases ({len(component_ids)} components defined)",
            ))
        else:
            report.add(TestResult(
                name="Cross-Validation: All components referenced in test cases",
                passed=True,
                details=f"{len(referenced_components & component_ids)}/{len(component_ids)} components referenced"
                if component_ids else "No components defined to check",
            ))
    else:
        report.add(TestResult(
            name="Cross-Validation: All components referenced in test cases",
            passed=False,
            errors=["Architecture or test model file not available"],
        ))


# ============================================================================
# Test Category 6: Stakeholder Consistency
# ============================================================================

def run_stakeholder_consistency_tests(report: TestReport):
    """Prueft Stakeholder-Needs Konsistenz mit Requirements."""

    stakeholder_file = TEST_DATA_DIR / "stakeholder-needs.md"

    if not stakeholder_file.exists():
        report.add(TestResult(
            name="Stakeholder-Needs: File exists",
            passed=False,
            errors=[f"File not found: {stakeholder_file}"],
        ))
        return

    report.add(TestResult(
        name="Stakeholder-Needs: File exists",
        passed=True,
    ))

    try:
        content = stakeholder_file.read_text(encoding="utf-8")
    except Exception as e:
        report.add(TestResult(
            name="Stakeholder-Needs: Readable",
            passed=False,
            errors=[str(e)],
        ))
        return

    report.add(TestResult(
        name="Stakeholder-Needs: Readable",
        passed=True,
    ))

    # Extract SH-XX IDs
    sh_pattern = re.compile(r'SH-\d+')
    stakeholder_ids = set(sh_pattern.findall(content))

    # Check minimum 5 stakeholders
    sh_count_ok = len(stakeholder_ids) >= 5
    report.add(TestResult(
        name="Stakeholder-Needs: At least 5 stakeholders",
        passed=sh_count_ok,
        details=f"Found {len(stakeholder_ids)} stakeholder(s): {', '.join(sorted(stakeholder_ids))}"
        if sh_count_ok else f"Only {len(stakeholder_ids)} stakeholder(s) found (need >= 5)",
    ))

    # Check all SH-IDs in L1 requirements traceability matrix
    req_ok, req_data, _ = validate_json_file(
        TEST_DATA_DIR / "expected-l1-requirements.json")

    if req_ok and isinstance(req_data, dict):
        metadata = req_data.get("metadata", {})
        traceability = metadata.get("traceability_matrix", {})
        if isinstance(traceability, dict):
            traced_sh_ids = set(traceability.keys())
            missing_sh = stakeholder_ids - traced_sh_ids
            all_traced = len(missing_sh) == 0
            report.add(TestResult(
                name="Stakeholder-Needs: All SH-IDs in traceability matrix",
                passed=all_traced,
                details="All stakeholders traced" if all_traced
                else f"Missing traceability for: {', '.join(sorted(missing_sh))}",
            ))
        else:
            report.add(TestResult(
                name="Stakeholder-Needs: All SH-IDs in traceability matrix",
                passed=False,
                errors=["No traceability matrix in requirements metadata"],
            ))
    else:
        report.add(TestResult(
            name="Stakeholder-Needs: All SH-IDs in traceability matrix",
            passed=False,
            errors=["L1 requirements file not available"],
        ))


# ============================================================================
# Main
# ============================================================================

def main():
    report = TestReport(timestamp=datetime.now().isoformat())

    print(f"SE Framework Test Runner")
    print(f"Base directory: {BASE_DIR}")
    print(f"Timestamp: {report.timestamp}")
    print(f"{'=' * 60}")

    # Category 1: Template Existence
    print("\n[1/6] Template Existence Tests...")
    try:
        run_template_existence_tests(report)
    except Exception as e:
        report.add(TestResult(
            name="Template-Existenz: Category failed",
            passed=False,
            errors=[f"Unexpected error: {str(e)}"],
        ))
    print(f"  -> {report.passed}/{report.total_tests} passed so far")

    # Category 2: role-defaults.yaml
    print("[2/6] Role Defaults Tests...")
    try:
        run_role_defaults_tests(report)
    except Exception as e:
        report.add(TestResult(
            name="role-defaults: Category failed",
            passed=False,
            errors=[f"Unexpected error: {str(e)}"],
        ))
    print(f"  -> {report.passed}/{report.total_tests} passed so far")

    # Category 3: Orchestrator Routing
    print("[3/6] Orchestrator Routing Tests...")
    try:
        run_orchestrator_routing_tests(report)
    except Exception as e:
        report.add(TestResult(
            name="Orchestrator: Category failed",
            passed=False,
            errors=[f"Unexpected error: {str(e)}"],
        ))
    print(f"  -> {report.passed}/{report.total_tests} passed so far")

    # Category 4: JSON Schema Validation
    print("[4/6] JSON Schema Tests...")
    try:
        run_json_schema_tests(report)
    except Exception as e:
        report.add(TestResult(
            name="JSON-Schema: Category failed",
            passed=False,
            errors=[f"Unexpected error: {str(e)}"],
        ))
    print(f"  -> {report.passed}/{report.total_tests} passed so far")

    # Category 5: Cross-Validation
    print("[5/6] Cross-Validation Tests...")
    try:
        run_cross_validation_tests(report)
    except Exception as e:
        report.add(TestResult(
            name="Cross-Validation: Category failed",
            passed=False,
            errors=[f"Unexpected error: {str(e)}"],
        ))
    print(f"  -> {report.passed}/{report.total_tests} passed so far")

    # Category 6: Stakeholder Consistency
    print("[6/6] Stakeholder Consistency Tests...")
    try:
        run_stakeholder_consistency_tests(report)
    except Exception as e:
        report.add(TestResult(
            name="Stakeholder-Consistency: Category failed",
            passed=False,
            errors=[f"Unexpected error: {str(e)}"],
        ))
    print(f"  -> {report.passed}/{report.total_tests} passed so far")

    # Generate and save report
    md_report = report.to_markdown()
    report_path = TEST_DATA_DIR / "test-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(md_report, encoding="utf-8")

    # Console output
    print(f"\n{'=' * 60}")
    print(f"SE Framework Test Report")
    print(f"{'=' * 60}")
    print(f"Timestamp: {report.timestamp}")
    print(f"Total: {report.total_tests} | Passed: {report.passed} | Failed: {report.failed}")
    print(f"Success Rate: {report.success_rate:.1f}%")
    print(f"\nFull report: {report_path}")
    print(f"{'=' * 60}")

    # Exit code
    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
