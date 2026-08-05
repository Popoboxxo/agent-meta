"""Test suite for quality pipeline configuration management."""

from scripts.lib.pipelines import (
    KNOWN_PROVIDERS,
    _pipeline_active_for_provider,
    build_pipeline_variables,
    validate_pipelines,
)


def test_known_providers_constant():
    assert KNOWN_PROVIDERS == ("Claude", "Opencode", "Gemini", "Continue", "Mammouth")


def test_pipeline_active_for_provider_no_field_means_everywhere_active():
    pipeline = {"stages": []}
    for provider in KNOWN_PROVIDERS:
        assert _pipeline_active_for_provider(pipeline, provider) is True


def test_pipeline_active_for_provider_exclude():
    pipeline = {"providers": {"default": "active", "exclude": ["Claude"]}}
    assert _pipeline_active_for_provider(pipeline, "Claude") is False
    assert _pipeline_active_for_provider(pipeline, "Opencode") is True


def test_pipeline_active_for_provider_include_only():
    pipeline = {"providers": {"default": "inactive", "include": ["Gemini"]}}
    assert _pipeline_active_for_provider(pipeline, "Gemini") is True
    assert _pipeline_active_for_provider(pipeline, "Claude") is False


def test_build_pipeline_variables_empty_block_for_excluded_provider():
    pipelines = {
        "concept-to-review": {
            "description": "test",
            "providers": {"default": "active", "exclude": ["Claude"]},
            "stages": [{"id": "plan", "agent": "planner", "task": "Plan", "mode": "sequential"}],
        }
    }
    variables = build_pipeline_variables(pipelines, {})
    blocks = variables["PIPELINE_CONCEPT_TO_REVIEW_PROVIDER_BLOCKS"]
    assert blocks["Claude"] == ""
    assert blocks["Opencode"] != ""


def test_validate_pipelines_rejects_unknown_provider():
    pipelines = {
        "p1": {
            "providers": {"default": "active", "exclude": ["NotAProvider"]},
            "stages": [],
        }
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("NotAProvider" in e for e in errors)


def test_validate_pipelines_rejects_bad_default_value():
    pipelines = {"p1": {"providers": {"default": "sometimes"}, "stages": []}}
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("providers.default" in e for e in errors)


def test_generate_pipeline_block_skips_inactive_dod_flag_stage():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {"id": "always", "agent": "git", "task": "Branch anlegen", "mode": "sequential"},
            {
                "id": "req",
                "agent": "requirements",
                "task": "REQ-ID vergeben",
                "mode": "conditional",
                "condition": {"dod_flag": "req-traceability"},
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode", active_dod={"req-traceability": False})
    assert "Branch anlegen" in block
    assert "REQ-ID vergeben" not in block


def test_generate_pipeline_block_includes_active_dod_flag_stage():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "req",
                "agent": "requirements",
                "task": "REQ-ID vergeben",
                "mode": "conditional",
                "condition": {"dod_flag": "req-traceability"},
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode", active_dod={"req-traceability": True})
    assert "REQ-ID vergeben" in block


def test_generate_pipeline_block_dod_flag_defaults_to_active_when_missing():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "req",
                "agent": "requirements",
                "task": "REQ-ID vergeben",
                "mode": "conditional",
                "condition": {"dod_flag": "req-traceability"},
            },
        ]
    }
    # active_dod does not mention "req-traceability" at all
    block = _generate_pipeline_block(pipeline, "Opencode", active_dod={})
    assert "REQ-ID vergeben" in block


def test_generate_pipeline_block_payload_flag_annotation():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "scope",
                "agent": "ideation",
                "task": "Idee scopen",
                "mode": "conditional",
                "condition": {"payload_flag": "needs_scoping"},
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    # payload_flag stages stay in the text (unlike dod_flag) — orchestrator
    # decides at runtime whether to skip them.
    assert "Idee scopen" in block
    assert "needs_scoping" in block


def test_validate_pipelines_detects_direct_cycle():
    from scripts.lib.pipelines import validate_pipelines

    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}]},
        "b": {"stages": [{"id": "y", "run_pipeline": "a", "mode": "run_pipeline"}]},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("circular" in e.lower() for e in errors)


def test_validate_pipelines_detects_missing_referenced_pipeline():
    from scripts.lib.pipelines import validate_pipelines

    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "does-not-exist", "mode": "run_pipeline"}]},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("does-not-exist" in e for e in errors)


def test_validate_pipelines_enforces_default_max_depth():
    from scripts.lib.pipelines import validate_pipelines

    # a -> b -> c -> d -> e is 4 hops; default max_depth is 4, so 5 pipelines
    # (depth 5 reached) must fail, depth 4 must pass.
    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}]},
        "b": {"stages": [{"id": "x", "run_pipeline": "c", "mode": "run_pipeline"}]},
        "c": {"stages": [{"id": "x", "run_pipeline": "d", "mode": "run_pipeline"}]},
        "d": {"stages": [{"id": "x", "run_pipeline": "e", "mode": "run_pipeline"}]},
        "e": {"stages": []},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("max_depth" in e for e in errors)


def test_validate_pipelines_max_depth_override_allows_deeper_nesting():
    from scripts.lib.pipelines import validate_pipelines

    pipelines = {
        "a": {
            "max_depth": 5,
            "stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}],
        },
        "b": {"stages": [{"id": "x", "run_pipeline": "c", "mode": "run_pipeline"}]},
        "c": {"stages": [{"id": "x", "run_pipeline": "d", "mode": "run_pipeline"}]},
        "d": {"stages": [{"id": "x", "run_pipeline": "e", "mode": "run_pipeline"}]},
        "e": {"stages": []},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert errors == []


def test_generate_pipeline_block_renders_nested_pipeline_indented():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipelines = {
        "outer": {
            "stages": [{"id": "implement", "run_pipeline": "inner", "mode": "run_pipeline"}]
        },
        "inner": {
            "stages": [{"id": "step", "agent": "developer", "task": "Feature implementieren", "mode": "sequential"}]
        },
    }
    block = _generate_pipeline_block(pipelines["outer"], "Opencode", all_pipelines=pipelines)
    assert "enthält Pipeline `inner`" in block
    assert "Feature implementieren" in block


def test_generate_pipeline_block_run_pipeline_missing_reference_is_marked():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {"stages": [{"id": "implement", "run_pipeline": "ghost", "mode": "run_pipeline"}]}
    block = _generate_pipeline_block(pipeline, "Opencode", all_pipelines={})
    assert "nicht aufgelöst" in block
