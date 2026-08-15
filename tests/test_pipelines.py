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


def test_validate_pipelines_reports_dict_stages_instead_of_crashing():
    # Regression test for audit #403: a malformed override (e.g. a stale
    # per-stage override fragment adopted as a whole pipeline by
    # apply_overrides()) can leave 'stages' as a dict instead of a list.
    # This must surface as a clean validation error, not an AttributeError.
    pipelines = {"p1": {"stages": {"review": {"loop": {"max_iterations": 5}}}}}
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("'stages' must be a list" in e and "dict" in e for e in errors)


def test_validate_pipelines_reports_string_stages_instead_of_crashing():
    pipelines = {"p1": {"stages": "not-a-list"}}
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("'stages' must be a list" in e and "str" in e for e in errors)


def test_validate_pipelines_malformed_stages_referenced_via_run_pipeline_does_not_crash():
    # A second pipeline with valid stages that run_pipeline-references the
    # malformed one must not crash while walking the composition graph.
    pipelines = {
        "p1": {"stages": {"review": {"loop": {"max_iterations": 5}}}},
        "p2": {"stages": [{"id": "x", "agent": "developer", "task": "t",
                            "mode": "sequential", "run_pipeline": "p1"}]},
    }
    errors = validate_pipelines(pipelines, available_roles=["developer"])
    assert any("'stages' must be a list" in e for e in errors)


def test_build_variables_surfaces_malformed_pipeline_override_as_warning():
    # Regression test for audit #402: a malformed quality-pipelines override
    # (e.g. targeting a pipeline name that no longer exists after a rename,
    # exactly what happened in .meta-config/project.yaml before PR #401's
    # follow-up fix) used to be swallowed by a bare `except Exception: pass`
    # in build_variables(), leaving PIPELINE_MATCH_TABLE silently unset with
    # zero indication of why. It must now show up in the warnings list.
    from pathlib import Path

    from scripts.lib.config import build_variables

    repo_root = Path(__file__).resolve().parents[1]
    config = {
        "quality-pipelines": {
            "overrides": {
                "this-pipeline-does-not-exist": {
                    "stages": {"review": {"loop": {"max_iterations": 5}}}
                }
            }
        }
    }
    variables, warnings = build_variables(config, repo_root)
    assert any("quality-pipelines" in w for w in warnings)
    assert "PIPELINE_MATCH_TABLE" in variables


def test_validate_pipelines_all_role_defaults_pipelines_are_clean():
    # End-to-end guard: every pipeline actually shipped in
    # config/role-defaults.yaml must validate cleanly against its own
    # roles. Catches structural drift (e.g. the #402/#403 regression)
    # without needing one hand-written test per pipeline.
    from pathlib import Path

    import yaml

    from scripts.lib.pipelines import load_quality_pipelines

    repo_root = Path(__file__).resolve().parents[1]
    pipelines = load_quality_pipelines(str(repo_root))
    assert pipelines, "expected at least one pipeline in config/role-defaults.yaml"

    with open(repo_root / "config" / "role-defaults.yaml", encoding="utf-8") as f:
        roles_cfg = yaml.safe_load(f)
    all_roles = list(roles_cfg.get("roles", {}).keys())

    errors = validate_pipelines(pipelines, all_roles)
    assert errors == [], f"Unexpected validation errors: {errors}"


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


def test_generate_pipeline_block_dod_flag_survivor_renders_as_plain_instruction():
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
    # Must NOT render as an unresolved conditional wrapper — the flag is
    # already decided at sync time, nothing left to evaluate at runtime.
    assert "Conditional execution" not in block
    assert "Condition evaluated by" not in block


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


def test_validate_pipelines_only_orchestrator_is_circular_guard():
    from scripts.lib.pipelines import validate_pipelines

    # "feature" must no longer trigger the circular-orchestration guard —
    # it is being retired as a role in this plan.
    pipelines = {
        "p1": {"stages": [{"id": "x", "agent": "feature", "task": "t", "mode": "sequential"}]}
    }
    errors = validate_pipelines(pipelines, available_roles=["feature"])
    assert not any("circular delegation" in e for e in errors)

    # "orchestrator" must still trigger it.
    pipelines2 = {
        "p1": {"stages": [{"id": "x", "agent": "orchestrator", "task": "t", "mode": "sequential"}]}
    }
    errors2 = validate_pipelines(pipelines2, available_roles=["orchestrator"])
    assert any("circular delegation" in e for e in errors2)


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


def test_generate_pipeline_block_run_pipeline_respects_provider_filter():
    """Final-review finding F1: run_pipeline recursion must honour the
    referenced sub-pipeline's own `providers` filter instead of always
    inlining it regardless of the current provider."""
    from scripts.lib.pipelines import _generate_pipeline_block

    pipelines = {
        "outer": {
            "stages": [{"id": "implement", "run_pipeline": "inner", "mode": "run_pipeline"}]
        },
        "inner": {
            "providers": {"default": "inactive", "include": ["Gemini"]},
            "stages": [
                {"id": "step", "agent": "developer", "task": "Feature implementieren", "mode": "sequential"}
            ],
        },
    }
    block = _generate_pipeline_block(pipelines["outer"], "Claude", all_pipelines=pipelines)
    assert "Feature implementieren" not in block
    assert "inaktiv" in block
    assert "inner" in block

    active_block = _generate_pipeline_block(pipelines["outer"], "Gemini", all_pipelines=pipelines)
    assert "Feature implementieren" in active_block
    assert "inaktiv" not in active_block


def test_generate_pipeline_block_default_max_depth_cuts_off_five_chain():
    """Final-review finding F2: with the default max_depth=4, a 5-pipeline
    chain (root + 4 hops) must be cut off exactly at the last hop — mirroring
    validate_pipelines(), which rejects this chain as exceeding max_depth."""
    from scripts.lib.pipelines import _generate_pipeline_block

    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}]},
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
    assert "Leaf-Stage erreicht" not in block
    assert "max_depth=4 erreicht" in block


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


def test_validate_pipelines_plan_driven_rejects_unknown_fallback_agent():
    pipelines = {
        "p1": {
            "stages": [
                {
                    "id": "implement",
                    "mode": "plan-driven",
                    "plan-driven": {"fallback_agent": "ghost-role"},
                }
            ]
        }
    }
    errors = validate_pipelines(pipelines, available_roles=["developer"])
    assert any("ghost-role" in e for e in errors)


def test_validate_pipelines_plan_driven_rejects_unknown_allowed_agent():
    pipelines = {
        "p1": {
            "stages": [
                {
                    "id": "implement",
                    "mode": "plan-driven",
                    "plan-driven": {
                        "fallback_agent": "developer",
                        "allowed_agents": ["developer", "ghost-role"],
                    },
                }
            ]
        }
    }
    errors = validate_pipelines(pipelines, available_roles=["developer"])
    assert any("ghost-role" in e for e in errors)


def test_validate_pipelines_plan_driven_accepts_known_roles():
    pipelines = {
        "p1": {
            "stages": [
                {
                    "id": "implement",
                    "mode": "plan-driven",
                    "plan-driven": {
                        "fallback_agent": "developer",
                        "allowed_agents": ["junior-developer", "developer", "senior-developer"],
                    },
                }
            ]
        }
    }
    errors = validate_pipelines(
        pipelines, available_roles=["junior-developer", "developer", "senior-developer"]
    )
    assert errors == []


def test_generate_pipeline_block_plan_driven_rendering():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "implement",
                "mode": "plan-driven",
                "plan-driven": {
                    "fallback_agent": "developer",
                    "allowed_agents": ["junior-developer", "developer", "senior-developer"],
                },
            }
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    assert "Plan-driven" in block
    assert "developer" in block
    assert "Plan-Validierung (vor Delegation)" in block
    assert "Prüfe: payload.plan_ref-Pfad existiert" in block
    assert "Prüfe: Plan-Frontmatter `pipeline_stages` enthält `implement`" in block


def test_sync_agents_passes_real_dod_resolved_to_inject_pipeline_blocks(monkeypatch):
    import scripts.lib.agents as agents_mod

    captured = {}

    def _fake_inject(content, pipelines, provider, active_dod):
        captured["active_dod"] = active_dod
        return content

    monkeypatch.setattr(agents_mod, "inject_pipeline_blocks", _fake_inject, raising=False)
    # This test only asserts the call-site wiring, not the full sync pipeline;
    # if sync_agents_for_provider is not directly unit-testable in isolation,
    # assert instead via source inspection:
    import inspect

    source = inspect.getsource(agents_mod.sync_agents_for_provider)
    assert "inject_pipeline_blocks(content, effective, provider, {})" not in source
    assert "resolve_dod(" in source


def test_generate_pipeline_block_no_approval_gate_by_default():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {"id": "implement", "agent": "developer", "task": "Feature bauen", "mode": "sequential"},
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    assert "Abnahme erforderlich" not in block


def test_generate_pipeline_block_stage_requires_approval_renders_gate():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "implement",
                "agent": "developer",
                "task": "Feature bauen",
                "mode": "sequential",
                "requires_approval": True,
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    assert "Abnahme erforderlich vor Stage 'implement'" in block
    # Gate must precede the stage's own rendered line.
    assert block.index("Abnahme erforderlich") < block.index("Feature bauen")


def test_generate_pipeline_block_pipeline_approval_default_applies_to_all_stages():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "approval_default": True,
        "stages": [
            {"id": "implement", "agent": "developer", "task": "Feature bauen", "mode": "sequential"},
            {"id": "commit", "agent": "git", "task": "Commit + PR", "mode": "sequential"},
        ],
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    assert "Abnahme erforderlich vor Stage 'implement'" in block
    assert "Abnahme erforderlich vor Stage 'commit'" in block


def test_generate_pipeline_block_stage_requires_approval_overrides_pipeline_default():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "approval_default": True,
        "stages": [
            {
                "id": "implement",
                "agent": "developer",
                "task": "Feature bauen",
                "mode": "sequential",
                "requires_approval": False,
            },
        ],
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    assert "Abnahme erforderlich" not in block


def test_validate_pipelines_rejects_non_bool_approval_default():
    pipelines = {"p1": {"approval_default": "yes", "stages": []}}
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("approval_default" in e and "boolean" in e for e in errors)


def test_validate_pipelines_rejects_non_bool_requires_approval():
    pipelines = {
        "p1": {
            "stages": [
                {"id": "implement", "agent": "developer", "task": "t", "mode": "sequential",
                 "requires_approval": "yes"}
            ]
        }
    }
    errors = validate_pipelines(pipelines, available_roles=["developer"])
    assert any("requires_approval" in e and "boolean" in e for e in errors)


def test_role_defaults_pipelines_render_no_approval_gate_by_default():
    # Backward-compat guard: no shipped base pipeline sets approval_default/
    # requires_approval, so no generated block may contain a gate line.
    from scripts.lib.pipelines import build_pipeline_variables, load_quality_pipelines

    pipelines = load_quality_pipelines(".")
    variables = build_pipeline_variables(pipelines, active_dod={})
    for var_name, value in variables.items():
        if not var_name.endswith("_PROVIDER_BLOCKS"):
            continue
        for provider, block in value.items():
            assert "Abnahme erforderlich" not in block, f"{var_name}/{provider}"


def test_generate_pipeline_detail_blocks_aggregates_active_pipelines():
    from scripts.lib.pipelines import generate_pipeline_detail_blocks

    pipelines = {
        "p1": {"stages": [{"id": "x", "agent": "developer", "task": "Task A", "mode": "sequential"}]},
        "p2": {"stages": [{"id": "y", "agent": "git", "task": "Task B", "mode": "sequential"}]},
    }
    result = generate_pipeline_detail_blocks(pipelines, "Opencode", active_dod={})
    assert "`p1`" in result
    assert "`p2`" in result
    assert "Task A" in result
    assert "Task B" in result


def test_generate_pipeline_detail_blocks_skips_disabled_and_inactive_provider():
    from scripts.lib.pipelines import generate_pipeline_detail_blocks

    pipelines = {
        "disabled": {"enabled": False, "stages": [{"id": "x", "agent": "developer", "task": "Nope", "mode": "sequential"}]},
        "claude-only": {
            "providers": {"default": "inactive", "include": ["Claude"]},
            "stages": [{"id": "y", "agent": "developer", "task": "OnlyClaude", "mode": "sequential"}],
        },
    }
    result = generate_pipeline_detail_blocks(pipelines, "Opencode", active_dod={})
    assert "Nope" not in result
    assert "OnlyClaude" not in result
    assert "disabled" not in result
    assert "claude-only" not in result


def test_inject_pipeline_blocks_replaces_aggregate_marker():
    from scripts.lib.pipelines import inject_pipeline_blocks

    pipelines = {
        "p1": {"stages": [{"id": "x", "agent": "developer", "task": "Feature bauen", "mode": "sequential"}]},
    }
    content = "before\n{{PIPELINE_DETAIL_BLOCKS}}\nafter"
    result = inject_pipeline_blocks(content, pipelines, "Opencode", active_dod={})
    assert "{{PIPELINE_DETAIL_BLOCKS}}" not in result
    assert "Feature bauen" in result
    assert "before" in result and "after" in result


def test_orchestrator_template_wires_pipeline_detail_blocks_marker():
    # Regression guard for review finding C1: the aggregate per-pipeline
    # stage-detail rendering (_generate_pipeline_block via
    # generate_pipeline_detail_blocks) previously had NO template consumer
    # anywhere — computed but never substituted into any generated file.
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    content = (repo_root / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    assert "{{PIPELINE_DETAIL_BLOCKS}}" in content


def test_build_variables_wires_roles_config_into_plan_producer_coupling_check():
    # Regression guard for review finding C2: validate_pipelines() was being
    # called from build_variables() with only 2 positional args, so its
    # optional roles_config-driven plan-producer-coupling check (a real,
    # tested code path in pipelines.py) never actually ran in production —
    # a plan-driven pipeline with no declared producer role would silently
    # pass validation. A custom pipeline with a plan-driven stage and no
    # producer role declaring `produces.plan.pipeline` for it must surface
    # a warning end-to-end through build_variables().
    from pathlib import Path

    from scripts.lib.config import build_variables

    repo_root = Path(__file__).resolve().parents[1]
    config = {
        "quality-pipelines": {
            "custom-pipelines": {
                "custom-plan-driven": {
                    "stages": [
                        {
                            "id": "implement",
                            "mode": "plan-driven",
                            "plan-driven": {"fallback_agent": "developer"},
                        }
                    ]
                }
            }
        }
    }
    variables, warnings = build_variables(config, repo_root)
    assert any("custom-plan-driven" in w and "produces.plan.pipeline" in w for w in warnings)


def test_check_plan_producer_coupling_survives_malformed_stages_dict():
    # Regression test discovered while fixing review finding C2: wiring
    # roles_config through to validate_pipelines() makes
    # check_plan_producer_coupling() actually run in production for the
    # first time — it must not crash on the same malformed 'stages' shape
    # (dict instead of list) that validate_pipelines()'s own loop already
    # guards against (audit #402/#403).
    from scripts.lib.pipelines import check_plan_producer_coupling

    pipelines = {"p1": {"stages": {"review": {"loop": {"max_iterations": 5}}}}}
    warnings = check_plan_producer_coupling(pipelines, {"roles": {}})
    assert warnings == []


def test_feature_lifecycle_pipeline_definition_is_valid():
    import yaml
    from scripts.lib.pipelines import load_quality_pipelines, validate_pipelines

    agent_meta_root = "."  # repo root; test runs from repo root under pytest
    pipelines = load_quality_pipelines(agent_meta_root)
    assert "standard-feature" not in pipelines
    assert "feature-lifecycle" in pipelines

    fl = pipelines["feature-lifecycle"]
    expected_keywords = {
        "Feature implementieren", "Feature bauen", "neues Feature", "Funktion bauen",
        "Feature Lifecycle", "komplexes Feature", "Feature Pipeline",
    }
    assert expected_keywords.issubset(set(fl["signal_keywords"]))

    stage_ids = [s["id"] for s in fl["stages"]]
    assert stage_ids == ["branch", "requirement", "tests", "implement", "verify", "validate-and-document", "commit"]

    implement_stage = next(s for s in fl["stages"] if s["id"] == "implement")
    assert implement_stage["mode"] == "plan-driven"
    assert implement_stage["plan-driven"]["fallback_agent"] == "developer"

    requirement_stage = next(s for s in fl["stages"] if s["id"] == "requirement")
    assert requirement_stage["condition"] == {"dod_flag": "req-traceability"}

    # role-defaults.yaml roles: `feature` must be gone.
    with open("config/role-defaults.yaml", encoding="utf-8") as f:
        roles_cfg = yaml.safe_load(f)
    assert "feature" not in roles_cfg.get("roles", {})

    # Full validation must be clean against the roles this pipeline references.
    all_roles = set(roles_cfg.get("roles", {}).keys())
    errors = validate_pipelines({"feature-lifecycle": fl}, list(all_roles))
    assert errors == [], f"Unexpected validation errors: {errors}"
