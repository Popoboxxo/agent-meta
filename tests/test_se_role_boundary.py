"""Test SE Role Boundary: se-critic detects forbidden terms in requirements output."""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Fixtures: sample requirement payloads
# ---------------------------------------------------------------------------

def _make_req(req_id: str, statement: str, domain: str = "system",
              arch_impact: bool = False, arch_trigger: str = "",
              acceptance_criteria: list | None = None) -> dict:
    """Helper to build a single requirement dict."""
    req = {
        "req_id": req_id,
        "statement": statement,
        "domain": domain,
        "priority": "mandatory",
        "rationale": f"Stakeholder need for {req_id}",
        "arch_impact": arch_impact,
        "scope": "system",
    }
    if arch_trigger:
        req["arch_trigger"] = arch_trigger
    if acceptance_criteria:
        req["acceptance_criteria"] = acceptance_criteria
    else:
        req["acceptance_criteria"] = []
    return req


# ---------------------------------------------------------------------------
# Forbidden terms list (mirrors se-critic.md)
# ---------------------------------------------------------------------------

FORBIDDEN_ARCHITECTURE_PATTERNS = {
    "microservice", "event-bus", "event-sourcing", "monolith",
    "CQRS", "hexagonal", "layered",
}
FORBIDDEN_TECHNOLOGIES = {
    "PostgreSQL", "MySQL", "MongoDB", "DynamoDB",
    "RabbitMQ", "Kafka", "Redis", "S3", "Docker", "Kubernetes", "nginx",
}
FORBIDDEN_PROTOCOLS = {
    "REST", "gRPC", "GraphQL", "MQTT", "AMQP",
    "WebSocket", "SOAP", "JWT", "OAuth2", "mTLS",
}
FORBIDDEN_DEPLOYMENT = {
    "replicas", "load-balancer", "auto-scaling",
    "helm chart", "terraform", "pod", "container",
}
FORBIDDEN_DATA_MODEL = {
    "users table", "foreign key", "normalized",
    "denormalized", "index on", "primary key",
}

ALL_FORBIDDEN = (
    FORBIDDEN_ARCHITECTURE_PATTERNS
    | FORBIDDEN_TECHNOLOGIES
    | FORBIDDEN_PROTOCOLS
    | FORBIDDEN_DEPLOYMENT
    | FORBIDDEN_DATA_MODEL
)


def _check_role_boundary(requirements: list[dict]) -> dict:
    """Simulate the se-critic role boundary check.

    Returns: dict with 'passed' (bool) and 'violations' (list).
    """
    violations = []
    for req in requirements:
        statement = req.get("statement", "")
        req_id = req.get("req_id", "UNKNOWN")
        for term in ALL_FORBIDDEN:
            if term.lower() in statement.lower():
                violations.append({
                    "req_id": req_id,
                    "violation_type": _classify_violation(term),
                    "description": f"'{term}' found in {req_id} statement.",
                    "forbidden_term": term,
                })
    return {
        "passed": len(violations) == 0,
        "violations": violations,
    }


def _classify_violation(term: str) -> str:
    if term in FORBIDDEN_ARCHITECTURE_PATTERNS:
        return "architecture_pattern"
    if term in FORBIDDEN_TECHNOLOGIES:
        return "technology_fixation"
    if term in FORBIDDEN_PROTOCOLS:
        return "protocol_choice"
    if term in FORBIDDEN_DEPLOYMENT:
        return "deployment_topology"
    if term in FORBIDDEN_DATA_MODEL:
        return "data_model"
    return "unknown"


# ---------------------------------------------------------------------------
# Tests — Clean requirements (no violations)
# ---------------------------------------------------------------------------

def test_clean_requirement_passes():
    """A clean behavioral requirement has no forbidden terms."""
    reqs = [
        _make_req("REQ-L1-001",
            "The system shall heat 500ml water to 90C within 120 seconds.",
            domain="system"),
        _make_req("REQ-L1-002",
            "The system shall decouple acceptance from processing.",
            domain="system", arch_impact=True,
            arch_trigger="decoupled async processing"),
        _make_req("REQ-L1-020",
            "The system shall require passwords with at least 12 characters.",
            domain="software"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is True
    assert len(result["violations"]) == 0


# ---------------------------------------------------------------------------
# Tests — Violations
# ---------------------------------------------------------------------------

def test_technology_fixation_detected():
    """Requirements naming a specific technology must be flagged."""
    reqs = [
        _make_req("REQ-L1-005",
            "The system shall use RabbitMQ as message broker to queue orders.",
            domain="software"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    assert len(result["violations"]) == 1
    v = result["violations"][0]
    assert v["req_id"] == "REQ-L1-005"
    assert v["violation_type"] == "technology_fixation"
    assert "RabbitMQ" in v["forbidden_term"]


def test_protocol_choice_detected():
    """Requirements specifying a protocol must be flagged."""
    reqs = [
        _make_req("REQ-L1-010",
            "The system shall expose a REST API for client communication.",
            domain="software"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    assert result["violations"][0]["violation_type"] == "protocol_choice"
    assert result["violations"][0]["forbidden_term"] == "REST"


def test_deployment_topology_detected():
    """Requirements specifying deployment topology must be flagged."""
    reqs = [
        _make_req("REQ-L1-012",
            "The system shall deploy as Kubernetes with 3 replicas.",
            domain="system"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    violations = {v["violation_type"] for v in result["violations"]}
    assert "technology_fixation" in violations  # "Kubernetes"
    assert "deployment_topology" in violations   # "replicas"


def test_architecture_pattern_detected():
    """Requirements choosing an architecture pattern must be flagged."""
    reqs = [
        _make_req("REQ-L1-015",
            "The system shall use a microservice architecture with event-bus.",
            domain="system"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    types = {v["violation_type"] for v in result["violations"]}
    assert "architecture_pattern" in types  # "microservice" or "event-bus"


def test_data_model_detected():
    """Requirements designing data models must be flagged."""
    reqs = [
        _make_req("REQ-L1-025",
            "The users table shall have a foreign key on sessions.",
            domain="software"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    assert result["violations"][0]["violation_type"] == "data_model"


def test_multiple_violations_in_one_req():
    """A single requirement can have multiple violations."""
    reqs = [
        _make_req("REQ-L1-030",
            "The system shall use PostgreSQL with REST and JWT auth, deployed as Kubernetes with 3 replicas.",
            domain="system"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    assert len(result["violations"]) >= 3  # PostgreSQL, REST, JWT, Kubernetes, replicas


def test_mixed_clean_and_dirty_requirements():
    """Some clean, some violating — check identifies only the dirty ones."""
    reqs = [
        _make_req("REQ-L1-001", "The system shall heat water within 120s.", domain="system"),
        _make_req("REQ-L1-005", "Uses RabbitMQ for queuing.", domain="software"),
        _make_req("REQ-L1-020", "Passwords with at least 12 chars.", domain="software"),
    ]
    result = _check_role_boundary(reqs)
    assert result["passed"] is False
    assert len(result["violations"]) == 1
    assert result["violations"][0]["req_id"] == "REQ-L1-005"


# ---------------------------------------------------------------------------
# Test — arch_impact field presence
# ---------------------------------------------------------------------------

def test_arch_impact_field_default():
    """When arch_impact is not set, it defaults to False."""
    req = _make_req("REQ-L1-001", "Heat water.", arch_impact=False)
    assert req["arch_impact"] is False


def test_arch_impact_with_trigger():
    """When arch_impact is True, arch_trigger must be present."""
    req = _make_req("REQ-L1-005", "Decouple acceptance from processing.",
                    arch_impact=True,
                    arch_trigger="decoupled async processing")
    assert req["arch_impact"] is True
    assert req["arch_trigger"] == "decoupled async processing"


# ---------------------------------------------------------------------------
# Test — scope classification
# ---------------------------------------------------------------------------

def test_scope_defaults_to_system():
    """Default scope is 'system'."""
    req = _make_req("REQ-L1-001", "Heat water.")
    assert req.get("scope", "system") == "system"


def test_scope_component_for_leaf():
    """Component scope is for refinement-level requirements."""
    req = _make_req("REQ-L3-042", "Validate auth token format.", domain="software")
    req["scope"] = "component"
    assert req["scope"] == "component"
