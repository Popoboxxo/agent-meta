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


def test_generate_pipeline_block_cuts_off_at_root_max_depth():
    """Rendering must honour the ROOT pipeline's max_depth for the whole chain,
    not re-derive a fresh default at every nesting level (mirrors
    _validate_pipeline_composition()'s semantics — see task-4 review finding 2).
    """
    from scripts.lib.pipelines import _generate_pipeline_block

    # a -> b -> c -> d -> e is a 5-hop chain. Root "a" overrides max_depth to 6,
    # so validate_pipelines() would accept it in full. Intermediate pipelines
    # deliberately set no max_depth of their own (implicit default 4) to prove
    # the root override — not a per-level recomputed default — governs rendering.
    pipelines = {
        "a": {
            "max_depth": 6,
            "stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}],
        },
        "b": {"stages": [{"id": "x", "run_pipeline": "c", "mode": "run_pipeline"}]},
        "c": {"stages": [{"id": "x", "run_pipeline": "d", "mode": "run_pipeline"}]},
        "d": {"stages": [{"id": "x", "run_pipeline": "e", "mode": "run_pipeline"}]},
        "e": {
            "stages": [
                {"id": "leaf", "agent": "developer", "task": "Leaf-Stage erreicht", "mode": "sequential"}
            ]
        },
    }
    block = _generate_pipeline_block(pipelines["a"], "Opencode", all_pipelines=pipelines)
    # The full chain must resolve (root max_depth=6 covers 5 hops) — no
    # intermediate level may cut off early using its own default-4.
    assert "Leaf-Stage erreicht" in block
    assert "max_depth" not in block


def test_generate_pipeline_block_render_cutoff_when_depth_exceeds_max_depth():
    """Covers the _depth >= _max_depth render branch directly (not just via
    validate_pipelines' separate walk)."""
    from scripts.lib.pipelines import _generate_pipeline_block

    pipelines = {
        "a": {
            "max_depth": 2,
            "stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}],
        },
        "b": {"stages": [{"id": "x", "run_pipeline": "c", "mode": "run_pipeline"}]},
        "c": {"stages": [{"id": "x", "run_pipeline": "d", "mode": "run_pipeline"}]},
        "d": {"stages": []},
    }
    block = _generate_pipeline_block(pipelines["a"], "Opencode", all_pipelines=pipelines)
    assert "max_depth=2 erreicht" in block


def test_build_pipeline_variables_resolves_run_pipeline_via_all_pipelines():
    """Integration test proving all_pipelines actually reaches
    _generate_pipeline_block() through build_pipeline_variables() (task-4
    review finding 1) — a run_pipeline composition must render the sub-pipeline
    content, not the "nicht aufgelöst" fallback."""
    from scripts.lib.pipelines import build_pipeline_variables

    pipelines = {
        "outer": {
            "stages": [{"id": "implement", "run_pipeline": "inner", "mode": "run_pipeline"}]
        },
        "inner": {
            "stages": [
                {"id": "step", "agent": "developer", "task": "Feature implementieren", "mode": "sequential"}
            ]
        },
    }
    variables = build_pipeline_variables(pipelines, active_dod={})
    provider_blocks = variables["PIPELINE_OUTER_PROVIDER_BLOCKS"]
    for provider, block in provider_blocks.items():
        assert "nicht aufgelöst" not in block, f"provider={provider}"
        assert "Feature implementieren" in block, f"provider={provider}"


def test_inject_pipeline_blocks_resolves_run_pipeline_via_all_pipelines():
    """Integration test proving all_pipelines reaches _generate_pipeline_block()
    through inject_pipeline_blocks() as well (task-4 review finding 1)."""
    from scripts.lib.pipelines import inject_pipeline_blocks

    pipelines = {
        "outer": {
            "stages": [{"id": "implement", "run_pipeline": "inner", "mode": "run_pipeline"}]
        },
        "inner": {
            "stages": [
                {"id": "step", "agent": "developer", "task": "Feature implementieren", "mode": "sequential"}
            ]
        },
    }
    content = "{{PIPELINE_OUTER_BLOCK}}"
    result = inject_pipeline_blocks(content, pipelines, "Opencode", active_dod={})
    assert "nicht aufgelöst" not in result
    assert "Feature implementieren" in result
