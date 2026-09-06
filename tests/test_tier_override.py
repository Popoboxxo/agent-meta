"""Tests for DelegationSyntaxEngine.resolve_tier_override() (issue #346).

Per-task tier override: the optional A2A envelope field
``payload.tier_override`` overrides the role→tier resolution for exactly one
dispatch. Guardrails under test:

1. Preset bounds — tier must exist in the ACTIVE tier preset
   (config/tier-presets.yaml, widened by providers.<provider>.tiers).
2. Security-critical downgrade block — roles from
   config/role-defaults.yaml → tier-override-policy.security-critical-roles
   (default: security-auditor, code-reviewer) can only be overridden to the
   same or a higher tier.
3. Audit-log duty — every override attempt (applied OR rejected) returns an
   audit record.

The engine is dormant by design (no runtime interception point); these tests
pin the semantics of its reference implementation.
"""

from pathlib import Path

from scripts.lib.delegation_syntax import DelegationSyntaxEngine

REPO_ROOT = Path(__file__).resolve().parents[1]


def _envelope(target: str = "developer", tier_override=None):
    payload = {"t": "Fix the thing"}
    if tier_override is not None:
        payload["tier_override"] = tier_override
    return {
        "protocol_version": "1.0.0",
        "handoff_id": "HOFF-20260906-001",
        "source_agent": "orchestrator",
        "target_agent": target,
        "payload": payload,
        "delegation_depth": 1,
    }


# ---------------------------------------------------------------------------
# No-op behaviour
# ---------------------------------------------------------------------------

def test_absent_override_is_noop_without_audit():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(_envelope(), role="developer")
    assert result == {
        "requested": None,
        "effective": None,
        "applied": False,
        "errors": [],
        "audit": None,
    }


def test_non_dict_payload_is_noop():
    engine = DelegationSyntaxEngine()
    envelope = _envelope()
    envelope["payload"] = [{"t": "batch task"}]
    result = engine.resolve_tier_override(envelope, role="developer")
    assert result["applied"] is False
    assert result["audit"] is None


# ---------------------------------------------------------------------------
# Guardrail 1: preset bounds (real config/tier-presets.yaml)
# ---------------------------------------------------------------------------

def test_valid_override_within_preset_is_applied():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="max"), role="developer", active_preset="Normal"
    )
    assert result["applied"] is True
    assert result["effective"] == "max"
    assert result["errors"] == []


def test_unknown_tier_is_rejected():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="gigantic"), role="developer", active_preset="Normal"
    )
    assert result["applied"] is False
    assert any("Unknown tier" in e for e in result["errors"])


def test_non_string_override_is_rejected():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override=7), role="developer", active_preset="Normal"
    )
    assert result["applied"] is False
    assert result["errors"]
    assert result["audit"]["reason"].startswith("type error")


def test_preset_bounds_block_tier_missing_from_global_tiers():
    """'ultra' is not in the Normal preset's global tiers: map — rejected
    without provider context."""
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="ultra"), role="developer", active_preset="Normal"
    )
    assert result["applied"] is False
    assert result["effective"] is None
    assert any("not defined in active tier-preset" in e for e in result["errors"])


def test_preset_bounds_widen_via_provider_tiers():
    """With provider context the Normal preset's provider-specific tier map
    (Claude has 'ultra') widens the bounds — override applies."""
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="ultra"),
        role="developer",
        active_preset="Normal",
        provider="Claude",
    )
    assert result["applied"] is True
    assert result["effective"] == "ultra"


def test_unknown_preset_name_is_rejected():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="max"),
        role="developer",
        active_preset="Does Not Exist",
    )
    assert result["applied"] is False
    assert any("not found" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Guardrail 2: security-critical downgrade block (real config/role-defaults.yaml)
# ---------------------------------------------------------------------------

def test_security_auditor_downgrade_is_blocked():
    """security-auditor defaults to 'powerful' (role-defaults.yaml) — any
    lower tier must be rejected."""
    engine = DelegationSyntaxEngine()
    for lower in ("nano", "fast", "balanced"):
        result = engine.resolve_tier_override(
            _envelope(target="security-auditor", tier_override=lower),
            role="security-auditor",
            active_preset="Normal",
        )
        assert result["applied"] is False, f"'{lower}' must not be applied"
        assert any("downgrade" in e.lower() for e in result["errors"])


def test_code_reviewer_downgrade_is_blocked():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(target="code-reviewer", tier_override="nano"),
        role="code-reviewer",
        active_preset="Normal",
    )
    assert result["applied"] is False
    assert any("security-critical" in e for e in result["errors"])


def test_security_role_same_or_higher_tier_is_allowed():
    engine = DelegationSyntaxEngine()
    for tier in ("powerful", "max", "ultra"):
        result = engine.resolve_tier_override(
            _envelope(target="security-auditor", tier_override=tier),
            role="security-auditor",
            active_preset="Normal",
            provider="Claude",  # 'ultra' exists only in the provider map
        )
        assert result["applied"] is True, f"'{tier}' must be allowed"


def test_non_security_role_downgrade_is_allowed():
    """Per-task downgrade for regular roles is the point of the feature."""
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="nano"), role="developer", active_preset="Normal"
    )
    assert result["applied"] is True
    assert result["effective"] == "nano"


def test_role_falls_back_to_target_agent():
    """Without an explicit role the guard uses target_agent."""
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(target="code-reviewer", tier_override="fast"), active_preset="Normal"
    )
    assert result["applied"] is False
    assert result["audit"]["role"] == "code-reviewer"


# ---------------------------------------------------------------------------
# Guardrail 3: audit record (applied AND rejected)
# ---------------------------------------------------------------------------

def test_audit_record_fields_on_acceptance():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override=" max "),  # whitespace must be normalized
        role="developer",
        active_preset="Normal",
    )
    audit = result["audit"]
    assert audit["event"] == "tier_override"
    assert audit["role"] == "developer"
    assert audit["requested"] == "max"
    assert audit["active_preset"] == "Normal"
    assert audit["decision"] == "applied"
    assert audit["reason"]


def test_audit_record_fields_on_rejection():
    engine = DelegationSyntaxEngine()
    result = engine.resolve_tier_override(
        _envelope(tier_override="nano"),
        role="security-auditor",
        active_preset="Normal",
    )
    audit = result["audit"]
    assert audit["event"] == "tier_override"
    assert audit["requested"] == "nano"
    assert audit["decision"] == "rejected"
    assert "downgrade" in audit["reason"]


# ---------------------------------------------------------------------------
# Config-driven policy (synthetic config dir, no repo-config dependency)
# ---------------------------------------------------------------------------

_TIER_PRESETS_YAML = """
Normal:
  description: test preset
  tiers:
    nano: model-nano
    fast: model-fast
    balanced: model-balanced
    powerful: model-powerful
    max: model-max
"""


def _write_tmp_config(tmp_path: Path, role_defaults_yaml: str) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "tier-presets.yaml").write_text(_TIER_PRESETS_YAML, encoding="utf-8")
    (config_dir / "role-defaults.yaml").write_text(role_defaults_yaml, encoding="utf-8")
    return config_dir


def test_policy_from_config_overrides_default(tmp_path):
    """A project can re-declare security-critical roles via config."""
    config_dir = _write_tmp_config(
        tmp_path,
        "roles:\n"
        "  developer:\n"
        "    model: balanced\n"
        "tier-override-policy:\n"
        "  security-critical-roles:\n"
        "  - developer\n",
    )
    engine = DelegationSyntaxEngine(config_dir=config_dir)
    result = engine.resolve_tier_override(
        _envelope(tier_override="nano"), role="developer", active_preset="Normal"
    )
    assert result["applied"] is False
    assert any("downgrade" in e.lower() for e in result["errors"])


def test_explicitly_empty_policy_list_disables_guard(tmp_path):
    config_dir = _write_tmp_config(
        tmp_path,
        "roles:\n"
        "  security-auditor:\n"
        "    model: powerful\n"
        "tier-override-policy:\n"
        "  security-critical-roles: []\n",
    )
    engine = DelegationSyntaxEngine(config_dir=config_dir)
    result = engine.resolve_tier_override(
        _envelope(tier_override="nano"),
        role="security-auditor",
        active_preset="Normal",
    )
    assert result["applied"] is True


def test_missing_policy_block_falls_back_to_builtin_roles(tmp_path):
    """Without any tier-override-policy block the built-in default
    (security-auditor, code-reviewer) applies."""
    config_dir = _write_tmp_config(
        tmp_path,
        "roles:\n"
        "  security-auditor:\n"
        "    model: powerful\n"
        "  developer:\n"
        "    model: balanced\n",
    )
    engine = DelegationSyntaxEngine(config_dir=config_dir)
    blocked = engine.resolve_tier_override(
        _envelope(tier_override="nano"),
        role="security-auditor",
        active_preset="Normal",
    )
    assert blocked["applied"] is False
    allowed = engine.resolve_tier_override(
        _envelope(tier_override="nano"), role="developer", active_preset="Normal"
    )
    assert allowed["applied"] is True


def test_non_tier_role_model_skips_rank_comparison(tmp_path):
    """Roles whose default is a raw model ID (not an abstract tier) are not
    rank-compared — model IDs carry no intrinsic ordering."""
    config_dir = _write_tmp_config(
        tmp_path,
        "roles:\n"
        "  security-auditor:\n"
        "    model: claude-some-concrete-model\n"
        "tier-override-policy:\n"
        "  security-critical-roles:\n"
        "  - security-auditor\n",
    )
    engine = DelegationSyntaxEngine(config_dir=config_dir)
    result = engine.resolve_tier_override(
        _envelope(tier_override="nano"),
        role="security-auditor",
        active_preset="Normal",
    )
    assert result["applied"] is True
