"""Pins for the optimizer chain (Tasks 27 / 2e.1, 29 / 2e.3, 30 / 2e.4).

Three blocks are covered by this module:

* **Task 27 / 2e.1 (IC-26, IC-27, AC-79, AC-91)** -- the read-only proposal
  role ``meta-optimizer``: exactly ``Read, Glob, Grep, TodoWrite``, no
  ``model:`` field, no write/execute/apply instruction of its own (the
  executing step belongs to ``agent-meta-manager``), the H-4 wording,
  name-only addressability, the IC-26 output-contract markers, the mandatory
  "not applicable" labeling and the verbatim-warning rule.
* **Task 29 / 2e.3 (IC-27, AC-59)** -- the ``config-patch-proposal-v1``
  hand-off contract: the JSON schema, the producer/consumer wiring and the
  consumer declaration in ``agent-meta-manager``.
* **Task 30 / 2e.4 (IC-27, AC-59, AC-90)** -- the §10c workflow of
  ``agent-meta-manager`` (Analyse -> Vorschau -> Anwendung): the three
  commands, the mandatory rules, the approval semantics, the preview payload,
  the apply report and the artifact contract.

**Pinning principle:** a contract statement is pinned by the *tokens* it must
contain, not by one exact spelling. A semantically equivalent rephrasing
therefore stays green (no false red), while a removed or weakened contract
statement still turns the gate red (no false green). The only deliberately
literal pins are the German quotes of the relayed user reply (``wörtlich`` /
``weitergeleiteten Nutzerantwort``) -- they are part of the IC-27 contract
wording and are documented as such.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.lib.frontmatter import parse_frontmatter_file
from scripts.lib.roles import load_roles_config
from scripts.lib.standalone import _CONDITIONAL_FALSE_FLAGS

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "agents" / "1-generic" / "meta-optimizer.md"

_H4_DESCRIPTION = (
    "Read-only config optimizer: reads a `sync.py --optimize-config` proposal and "
    "presents token-compact, evidence-backed variants of the project config with "
    "mandatory warnings — never edits or applies anything."
)
_H4_SHORT_DESC = "Proposes compact project-config variants (proposal only)"
_H4_NAME_ONLY_REASON = (
    "Config optimization meta role; produces proposals only and is invoked "
    "explicitly by name, never by routine task keywords."
)
_NOT_APPLICABLE = "nicht anwendbar — manuelle Nutzeränderung bzw. Framework-Issue"
_EXPECTED_TOOLS = ["Read", "Glob", "Grep", "TodoWrite"]


def _text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _body() -> str:
    return _text().split("---", 2)[2]


def _roles() -> dict:
    return load_roles_config(REPO_ROOT)["roles"]


def test_template_exists_with_valid_frontmatter():
    assert TEMPLATE.is_file()
    fm = parse_frontmatter_file(TEMPLATE)
    assert fm["name"] == "template-meta-optimizer"
    assert fm["version"] == "1.0.0"
    assert fm["prompt_mode"] == "modern"
    assert fm["description"] == _H4_DESCRIPTION
    assert fm["hint"] == _H4_SHORT_DESC
    assert fm["reference_standards"] == ["Clean Code: separation of concerns"]


def test_tools_are_exact_and_have_no_write_execute_or_agent():
    fm = parse_frontmatter_file(TEMPLATE)
    assert list(fm["tools"]) == _EXPECTED_TOOLS
    for forbidden in ("Bash", "Write", "Edit", "Agent"):
        assert forbidden not in fm["tools"], forbidden


def test_no_model_field():
    fm = parse_frontmatter_file(TEMPLATE)
    assert "model" not in fm
    head = _text().split("---", 2)[1]
    assert not re.search(r"^model\s*:", head, re.MULTILINE)


def test_required_placeholders_and_extension_pointer():
    text = _text()
    body = _body()
    assert (
        "> **Extension:** If `{{EXTENSION_DIR}}/{{PREFIX}}-meta-optimizer-ext.md` "
        "exists → read and apply immediately."
    ) in text
    for placeholder in (
        "{{PROJECT_CONTEXT}}",
        "{{PROJECT_GOAL}}",
        "{{PROMPT_INJECTION_DEFENSE_BLOCK}}",
        "{{OUTPUT_GUARD_BLOCK}}",
    ):
        assert placeholder in body, placeholder


def test_output_contract_markers():
    body = _body()
    for marker in (
        "STATUS:",
        "RESULT:",
        "ARTIFACTS: none",
        "PROPOSALS:",
        "PROOF:",
        "NEXT:",
        "config-patch-proposal-v1",
    ):
        assert marker in body, marker
    # IC-26: PROOF reports level, byte-equality, roundtrip and the scope note.
    for proof_field in ("level_reached", "byte_equal_files/files_compared",
                        "roundtrip ok/nok", "scope_note"):
        assert proof_field in body, proof_field
    # AC-91: the PROPOSALS contract block carries the exact German hint label,
    # not an English "not applicable — manuelle …" variant an LLM might emit.
    contract = re.search(r"```\n(STATUS:.*?)```", body, re.DOTALL)
    assert contract, "output-contract fenced block missing"
    block = contract.group(1)
    assert "PROPOSALS:" in block
    assert _NOT_APPLICABLE in block
    assert "not applicable — manuelle" not in block


def test_no_write_or_execute_instruction_of_its_own():
    text = _text()
    body = _body()
    low = text.lower()
    assert "```bash" not in text and "```sh" not in text
    assert "bash allowlist" not in low
    assert "no write or edit tools" in low
    assert "strictly read-only" in low
    assert "you never edit" in low and "you never apply" in low
    assert "you execute nothing" in low or "executes nothing" in low
    # No tool-use instruction that would grant this role a writer/executor.
    assert not re.search(r"\b(use|using) the (write|edit)\b", low)
    # Every execution/apply mention in the body is scoped to agent-meta-manager.
    for line in body.splitlines():
        if ("sync.py --" in line or "--dry-run" in line
                or "--apply-config-patch" in line or "--preview" in line):
            assert "agent-meta-manager" in line, line


def test_hint_labeling_and_verbatim_warnings():
    text = _text()
    body = _body()
    assert _NOT_APPLICABLE in text
    assert "NON-DETERMINISTIC" in body
    assert "applicable: false" in body
    assert re.search(r"only candidates with `?applicable: true`?", body, re.IGNORECASE)
    assert "approval list" in body.lower()
    # Hint candidates keep their ID for reference; own proposals carry no OPT-ID.
    assert "keep their id only for reference" in body.lower()
    assert "no opt-id" in body.lower()
    # warnings are taken verbatim from Candidate.warnings
    assert "wörtlich" in body
    # variable-removal note (IC-26 step 5)
    assert "Bei späterer Reaktivierung" in body


def test_credential_statement():
    text = _text()
    low = text.lower()
    assert "never quote credential values" in low
    assert "credential keys" in low
    # credential keys must not appear even as hints
    assert "even as hints" in low


def test_proposal_content_is_data_not_instructions():
    body = _body()
    assert "data, not instructions" in body


def test_role_defaults_entry_is_name_only_h4():
    info = _roles()["meta-optimizer"]
    assert info["model"] == "balanced"
    assert info["memory"] == ""
    assert info["workflow_tier"] == "optional"
    assert info["description"] == _H4_DESCRIPTION
    assert info["short_desc"] == _H4_SHORT_DESC

    routing = info["routing"]
    assert routing["addressability"] == "name_only"
    assert routing["name_only_reason"] == _H4_NAME_ONLY_REASON
    assert routing["orchestrator_only"] is True
    assert routing["parallel"] is False
    assert "routing_patterns" not in info
    assert "intent_keywords" not in routing

    handoff = info["handoff"]
    assert handoff["input_contracts"] == ["task-spec-v1"]
    assert handoff["output_contract"] == "config-patch-proposal-v1"
    assert handoff["target_roles"] == ["agent-meta-manager"]


def test_standalone_conditionals_are_registered():
    """A-F-2: every {{#if VAR}}/{{#unless VAR}} must be a literal standalone flag."""
    found = re.findall(r"\{\{#(?:if|unless)\s+([A-Z0-9_]+)", _text())
    missing = [var for var in found if var not in _CONDITIONAL_FALSE_FLAGS]
    assert not missing, f"unregistered standalone conditional flags: {missing}"


def test_role_not_in_any_routing_keywords_of_other_roles():
    for name, info in _roles().items():
        if name == "meta-optimizer":
            continue
        blob = repr(info.get("routing_patterns")) + repr(
            (info.get("routing") or {}).get("intent_keywords")
        )
        assert "meta-optimizer" not in blob, name


def test_no_provider_literals_in_template():
    low = _text().lower()
    for literal in (
        "claude", "codex", "gemini", "opencode", "mammouth", "continue.dev",
        "copilot", "anthropic",
    ):
        assert literal not in low, literal


# --- Task 29 / 2e.3 (IC-27, AC-59 Consumer): agent-meta-manager consumes config-patch-proposal-v1 ---


def test_manager_declares_config_patch_proposal_input_contract():
    handoff = _roles()["agent-meta-manager"].get("handoff") or {}
    assert "config-patch-proposal-v1" in (handoff.get("input_contracts") or [])


def test_no_output_not_consumed_finding_for_config_patch_proposal():
    from scripts.lib.consistency.handoff_contracts import check_handoff_contracts  # type: ignore
    findings = check_handoff_contracts(REPO_ROOT)
    bad = [f for f in findings if f.check == "handoff.output-not-consumed" and "config-patch-proposal-v1" in f.message]
    assert not bad, bad


def test_config_patch_proposal_schema_exists_and_pins_the_contract():
    schema_path = REPO_ROOT / "schemas" / "handoffs" / "config-patch-proposal.schema.json"
    assert schema_path.is_file(), schema_path
    data = json.loads(schema_path.read_text(encoding="utf-8"))

    assert data["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert data["type"] == "object"
    assert "config-patch-proposal-v1" in data["title"]
    assert "config-patch-proposal-v1" in data["description"]

    # Top-level contract markers: STATUS / RESULT / PROPOSALS / PROOF / NEXT.
    assert set(data["required"]) == {"st", "rs", "pr", "pf", "nx"}
    assert data["properties"]["st"]["enum"] == ["done", "partial", "failed"]
    assert data["properties"]["ar"]["maxItems"] == 0

    # The two sub-objects are reachable without resolving a $ref.
    proposal = data["definitions"]["proposal"]
    proof = data["definitions"]["proof"]
    assert proposal["type"] == "object"
    assert proof["type"] == "object"

    assert set(proposal["required"]) == {
        "id", "kind", "sc", "dt", "ap", "al", "pl", "mk", "wn", "yb", "ib", "vr", "ra",
    }
    assert proposal["properties"]["kind"]["enum"] == [
        "no-effect",
        "dead-variable-content-loss",
        "duplicate-value",
        "relocate-to-ext",
        "relocate-to-doc",
        "semantic-merge",
        "inactive-scope",
        "structural-simplify",
        "info-only",
    ]
    assert proposal["properties"]["sc"]["enum"] == [
        "variables",
        "roles",
        "providers",
        "auto_commit",
        "hooks",
        "repo_containment",
        "orchestrator",
        "structural-other",
    ]
    assert proposal["properties"]["al"]["enum"] == ["confirm", "confirm-runtime"]
    assert proposal["properties"]["pl"]["enum"] == ["none", "L0", "L1", "L2", "L3"]
    assert proposal["properties"]["mk"]["items"]["enum"] == [
        "runtime-reader",
        "refilled-by-defaults",
        "inactive-scope",
        "reactivation-loss-warning",
    ]
    assert proposal["properties"]["id"]["pattern"] == "^OPT-[a-z-]+:.+$"
    assert proposal["properties"]["dt"]["type"] == "boolean"
    assert proposal["properties"]["ap"]["type"] == "boolean"

    assert set(proof["required"]) == {"lvl", "beq", "cmp", "rto", "snt"}
    assert proof["properties"]["lvl"]["enum"] == ["none", "L0", "L1", "L2", "L3"]
    assert proof["properties"]["rto"]["enum"] == ["ok", "nok"]
    assert proof["properties"]["beq"]["minimum"] == 0
    assert proof["properties"]["cmp"]["minimum"] == 0


def test_config_patch_proposal_stays_a_phase_2_contract():
    roles = _roles()
    producers = [
        name
        for name, info in roles.items()
        if (info.get("handoff") or {}).get("output_contract") == "config-patch-proposal-v1"
    ]
    assert producers == ["meta-optimizer"]
    # Phase 0 / 0e roles must neither produce nor consume the phase-2 contract.
    for phase0_role in ("meta-doctor", "template-auditor"):
        info = roles.get(phase0_role) or {}
        handoff = info.get("handoff") or {}
        assert handoff.get("output_contract") != "config-patch-proposal-v1", phase0_role
        assert "config-patch-proposal-v1" not in (handoff.get("input_contracts") or []), phase0_role


# --- Task 30 / 2e.4 (IC-27, AC-59, AC-90, AC-91): agent-meta-manager optimizer workflow ---

#: The manager is the only applying role (IC-27 Rev. 3.1); the section below is
#: the single place that documents the Analyse -> Vorschau -> Anwendung chain.
_MANAGER_TEMPLATE = REPO_ROOT / "agents" / "1-generic" / "agent-meta-manager.md"
_OPTIMIZER_HEADING = "## 10c. Optimizer-Vorschläge anwenden (Advisory Mode)"

#: The three command fragments (IC-27 Rev. 3.1 steps 1/4/5). The placeholders
#: stay unresolved in the template -- they are substituted at sync time.
_CMD_ANALYSE = "--optimize-config --json --out {{TMP_SINK_PATH}}/meta-optimizer/<ts>/"
_CMD_PREVIEW = "--dry-run"
_CMD_APPLY = "--preview"

#: A line carries a negation if it contains a negation word in English or
#: German. Case-insensitive and word-bounded, so a contract-compliant
#: phrasing ("is not changed", "must not be edited", "without …") is accepted
#: instead of only the five literal spellings of "never".
_NEGATION_RE = re.compile(
    r"\b(?:never|not|no|without|nothing|nie|nicht|kein(?:e|er|es)?|ohne)\b",
    re.IGNORECASE,
)

#: A rule bullet of the "Mandatory rules" list: ``- **<label>:** <body>``.
#: The label keeps its backticks (e.g. ``**`confirm-runtime`:**``); the
#: trailing colon is stripped by the parser.
_RULE_BULLET_RE = re.compile(
    r"^-\s+\*\*(?P<label>[^*]+)\*\*:?\s*(?P<body>.+)$", re.MULTILINE
)

#: One of the three numbered IC-27 steps: ``1. **Analyse** …``.
_STEP_RE = re.compile(r"^(?P<num>\d+)\.\s+\*\*(?P<verb>[^*]+)\*\*", re.MULTILINE)

#: "… is not an approval" / "keine Freigabe" -- the IC-27 wording that an
#: orchestrator message or a proposal hand-off must NOT be able to produce.
_APPROVAL_DENIAL_RE = re.compile(
    r"\b(?:not|no|never|isn't|is\s+not)\s+(?:an?\s+)?(?:explicit\s+)?"
    r"(?:user\s+|relayed\s+|weitergeleitete[nr]?\s+)?(?:approval|Freigabe)\b"
    r"|\bkeine\s+freigabe\b|\bnicht\s+die\s+freigabe\b",
    re.IGNORECASE,
)

#: The word "release" is already bound to the version/GitHub-release workflow
#: (§14) and must not serve as a synonym for "approval". A mention is only
#: allowed inside a *denial* ("is not an approval or a release"); a positive
#: use ("is a release", "counts as a release") is a contract violation.
_RELEASE_TOKEN_RE = re.compile(r"\brelease\b", re.IGNORECASE)
_RELEASE_DENIAL_RE = re.compile(
    r"\b(?:not|never|no|isn't|is\s+not|nor|neither)\b[^.;\n]{0,80}?\brelease\b"
    r"|\brelease\b[^.;\n]{0,40}?\b(?:is\s+not|isn't|never|cannot|can't)\b",
    re.IGNORECASE,
)

#: The write tools whose use on ``project.yaml`` the optimizer path forbids.
#: Case-insensitive on purpose: the tool names are a contract, their spelling
#: ("``Edit``" vs. "the ``edit`` tool") is not.
_EDIT_TOOL_RE = re.compile(r"\b(?:Edit|Write)\b", re.IGNORECASE)

#: The scope marker that makes an ``Edit``/``Write`` prohibition applicable to
#: the optimizer proposal path only (and not to ``project.yaml`` in general).
#: The vocabulary is deliberately open: a semantically equivalent naming of the
#: proposal path ("the suggested changes", "the diff", "the patch", "der
#: Vorschlag") must not fall through. ``sync.py`` invocations are stripped
#: before the check, so that the *apply command* ("--apply-config-patch") can
#: not act as a scope marker for an unscoped ban.
_SCOPE_RE = re.compile(
    r"\b(?:optimizer|optimiz\w*|optimis\w*|proposal\w*|candidate\w*|hunk\w*|"
    r"patch(?:es)?|diffs?|suggest\w*|vorschl\w*|vorschlag\w*)\b",
    re.IGNORECASE,
)

#: A ``sync.py`` invocation inside a sentence -- removed before the scope
#: check, so that the documented apply command cannot smuggle in a scope.
_COMMAND_RE = re.compile(r"`?sync\.py\b[^`\n]*`?")

#: "This role is the **only applier**" -- the claim that ``agent-meta-manager``
#: is the one role that applies optimizer proposals. Pinned by tokens (an
#: "only" marker + an apply word, in one sentence, without a negation), so that
#: "the only role that applies" is accepted as well.
_ONLY_APPLIER_RE = re.compile(
    r"\b(?:only|single|sole|unique)\b"
    r"(?![^.;\n]{0,40}?\b(?:never|not|no|without|nothing|nicht|kein)\b)"
    r"[^.;\n]{0,40}?\b(?:applier|applies)\b",
    re.IGNORECASE,
)

#: A usage/prohibition statement about ``--fill-defaults``. An occurrence of
#: the flag that carries no negation word is only harmless if it makes no such
#: statement (a descriptive mention); a prohibition or a usage without a
#: negation word is a contract violation.
_FLAG_STATEMENT_RE = re.compile(
    r"\b(?:use|using|pass|passing|run|running|invoke|invoking|call|calling|"
    r"apply|applying|execute|executing|provide|providing|set|setting|"
    r"forbidden|prohibited|disallowed|verboten|untersagt)\b",
    re.IGNORECASE,
)


def _manager_text() -> str:
    return _MANAGER_TEMPLATE.read_text(encoding="utf-8")


def _sentences(text: str) -> list:
    """Split a text into sentences (``.``/``;``/``:``/newline terminated).

    Sentence granularity is what makes the scope check meaningful: a
    prohibition is only valid for the subject its own sentence names.
    """
    parts = re.split(r"(?<=[.;:\n])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def _rule_body(rules: dict, needle: str) -> str:
    """Return the body of the mandatory rule whose label contains *needle*."""
    matches = [
        body for label, body in rules.items() if needle.lower() in label.lower()
    ]
    assert len(matches) == 1, (
        f"expected exactly one mandatory rule matching {needle!r}, got {len(matches)}"
    )
    return matches[0]


def _release_violations(body: str) -> list:
    """Return the sentences that use "release" as a synonym for approval.

    A mention of "release" is allowed inside a denial ("is not an approval or a
    release"); every other mention ("is a release", "counts as a release") is a
    contract violation -- the word belongs to the version/release workflow
    (§14), not to the approval vocabulary of IC-27.
    """
    violations = []
    for sentence in _sentences(body):
        denials = list(_RELEASE_DENIAL_RE.finditer(sentence))
        for match in _RELEASE_TOKEN_RE.finditer(sentence):
            if not any(d.start() <= match.start() < d.end() for d in denials):
                violations.append(sentence)
                break
    return violations


def _flag_occurrence_is_allowed(line: str) -> bool:
    """Return True if a ``--fill-defaults`` occurrence on *line* is harmless.

    Allowed are

    * a line that carries a negation word (the prohibition itself, or a
      sentence that denies a usage), and
    * a descriptive mention that makes no usage/prohibition statement
      ("the sync CLI offers ``--fill-defaults``; it is documented in the CLI
      reference").

    Not allowed is a prohibition or usage statement without a negation word:
    the contract would then be expressed, but not as a denial.
    """
    if _NEGATION_RE.search(line):
        return True
    return not _FLAG_STATEMENT_RE.search(line)


def _rule_line_body(line: str) -> str:
    """Return the body of a mandatory-rule bullet (without its label).

    A rule bullet names its subject in the label ("**No `--fill-defaults`:**"),
    so the negation that makes the rule a denial has to stand in the body --
    the label alone is a topic, not a denial.
    """
    match = _RULE_BULLET_RE.match(line)
    if not match:
        return line
    return match.group("body")


def _optimizer_section() -> str:
    """Extract §10c from the manager template.

    Regex-based (like ``tests/test_meta_doctor_role.py::_consumer_section``) so
    the assertions do not depend on the formatting of the rest of the template.
    """
    m = re.search(
        r"\n" + re.escape(_OPTIMIZER_HEADING) + r"\n(.*?)(?=\n## |\Z)",
        _manager_text(),
        re.DOTALL,
    )
    assert m, "optimizer section '## 10c. ...' missing in agent-meta-manager"
    return m.group(1)


def _mandatory_rules() -> dict:
    """Map the mandatory-rule label -> body text of the §10c rule list.

    Only the bullet list below "Mandatory rules:" is parsed; the numbered
    steps above it are covered by :func:`_step_chunks`.
    """
    sec = _optimizer_section()
    assert "Mandatory rules:" in sec, "§10c has no 'Mandatory rules:' list"
    rules = {}
    for match in _RULE_BULLET_RE.finditer(sec.split("Mandatory rules:", 1)[1]):
        rules[match.group("label").strip().rstrip(":")] = match.group("body").strip()
    return rules


def _step_chunks() -> dict:
    """Map the step number -> full chunk text of the three IC-27 steps."""
    sec = _optimizer_section()
    starts = list(_STEP_RE.finditer(sec))
    chunks = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(sec)
        chunks[match.group("num")] = sec[match.start():end]
    return chunks


def test_manager_optimizer_section_exists_after_the_doctor_consumer_section():
    text = _manager_text()
    assert text.count(_OPTIMIZER_HEADING) == 1, "§10c heading must exist exactly once"
    doctor = re.search(r"\n## [^\n]*doctor-findings-v1[^\n]*\n", text)
    assert doctor, "doctor consumer section missing"
    assert text.index(_OPTIMIZER_HEADING) > doctor.end(), (
        "§10c must come after the doctor consumer section"
    )
    # The new heading must not steal the doctor section from its own test.
    assert "doctor-findings-v1" not in _OPTIMIZER_HEADING


def test_manager_optimizer_section_has_exactly_three_steps_in_order():
    sec = _optimizer_section()
    steps = re.findall(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*", sec, re.MULTILINE)
    assert steps == [("1", "Analyse"), ("2", "Vorschau"), ("3", "Anwendung")], steps


def test_manager_optimizer_section_pins_the_three_commands():
    sec = _optimizer_section()
    for command in (_CMD_ANALYSE, _CMD_PREVIEW, _CMD_APPLY):
        assert command in sec, command


def test_manager_optimizer_section_requires_ids_from_the_relayed_user_reply():
    """IC-27 Rev. 3.1: the accepted IDs must stand in the relayed user reply.

    **Deliberately literal pin (documented convention):** the two German
    quotes (``wörtlich`` / ``weitergeleiteten Nutzerantwort``) are part of the
    IC-27 contract wording -- they mark the *verbatim* transfer of the user's
    confirmation and are quoted as such in the spec. An English-only
    rephrasing of the rule is therefore rejected on purpose; every other pin of
    this module is token-based.
    """
    sec = _optimizer_section()
    assert "wörtlich" in sec
    assert "weitergeleiteten Nutzerantwort" in sec


def test_manager_optimizer_section_never_edits_project_yaml():
    """The optimizer path must forbid hand-editing ``project.yaml`` (IC-27).

    Two contracts are pinned here:

    1. A prohibition exists -- a line mentions ``project.yaml`` + ``Edit`` and
       carries a negation (any accepted negation spelling, see ``_NEGATION_RE``).
    2. The prohibition is **scoped to the optimizer proposal path**. A blanket
       ban ("``project.yaml`` is never changed via ``Edit``") contradicts §8b/§8b.2
       (model blast modes), §13 (SE cascade) and the admin-UI shortcut, which all
       change ``project.yaml`` by other documented paths. Every sentence that
       bans ``Edit``/``Write`` on ``project.yaml`` must therefore name the
       proposal/optimizer scope it applies to.
    """
    sec = _optimizer_section()
    hits = [
        line
        for line in sec.splitlines()
        if "project.yaml" in line
        and _EDIT_TOOL_RE.search(line)
        and _NEGATION_RE.search(line)
    ]
    assert hits, "no 'project.yaml' + 'Edit' + negation line in the optimizer section"

    for sentence in _sentences(sec):
        if "project.yaml" not in sentence:
            continue
        if not _EDIT_TOOL_RE.search(sentence):
            continue
        if not _NEGATION_RE.search(sentence):
            continue
        # The documented apply command is not a scope marker: strip it before
        # looking for the scope, so that an unscoped ban cannot smuggle in a
        # scope through "--apply-config-patch".
        scope_text = _COMMAND_RE.sub(" ", sentence)
        assert _SCOPE_RE.search(scope_text), (
            "the Edit/Write prohibition on project.yaml is not scoped to the "
            f"optimizer proposal path: {sentence!r}"
        )


def test_manager_optimizer_section_never_uses_fill_defaults():
    """Section scope: §10c must not *use* ``--fill-defaults`` (IC-27).

    The flag may only appear on a prohibition line inside the section; in no
    command block of the section at all. The template-wide guard lives in
    :func:`test_manager_template_only_mentions_fill_defaults_as_a_prohibition`
    (global scope -- it prevents the flag from showing up as a command anywhere
    in the template, including sections unrelated to the optimizer).
    """
    sec = _optimizer_section()
    for block in re.findall(r"```bash\n(.*?)```", sec, re.DOTALL):
        assert "--fill-defaults" not in block, block
    for line in sec.splitlines():
        if "--fill-defaults" in line:
            assert _flag_occurrence_is_allowed(line), line


def test_manager_template_only_mentions_fill_defaults_as_a_prohibition():
    """Global scope: ``--fill-defaults`` may only occur on a prohibition line.

    This is a template-wide guard (not a §10c guard): it catches the flag
    leaking into a command of *any* section of the manager template.

    The occurrence *count* is deliberately not pinned -- a second, harmless
    mention (a documentation note) must not turn the gate red. What is pinned
    is the contract:

    1. the flag occurs at least once (dropping the prohibition entirely turns
       the gate red too), and
    2. every occurrence is a denial, not a usage -- a prohibition sentence
       without a negation word is a violation, and
    3. the flag never occurs in a bash code block (a real usage).
    """
    text = _manager_text()
    flag_lines = [
        line for line in text.splitlines() if "--fill-defaults" in line
    ]
    assert flag_lines, (
        "the '--fill-defaults' prohibition disappeared from the manager template"
    )
    for line in flag_lines:
        assert _flag_occurrence_is_allowed(line), line
    for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
        assert "--fill-defaults" not in block, block


def test_manager_optimizer_section_pins_the_preview_payload():
    """IC-27 Rev. 3.1 step 4: what ``preview.json`` carries.

    The preview is the artifact the user confirms; its payload (recomputed
    hunks, the ID list, the mandatory texts, the ``confirm-runtime`` IDs) is
    what makes that confirmation meaningful, so it is pinned on step 2.

    The payload is pinned by its *tokens*, not by one spelling: "the accepted
    ID list" and "the list of accepted IDs" state the same contract.
    """
    chunk = _step_chunks()["2"]
    assert "preview.json" in chunk
    for label, tokens in (
        ("the recomputed hunks", (r"\bhunks?\b",)),
        ("the ID list", (r"\bIDs?\b", r"\b(?:list|accepted|enumerat\w*)\b")),
        ("the mandatory texts", (r"\b(?:mandatory|required|warning)\b", r"\btexts?\b")),
        ("the confirm-runtime IDs", (r"confirm-runtime",)),
    ):
        for token in tokens:
            assert re.search(token, chunk, re.IGNORECASE), f"{label}: {token}"


def test_manager_optimizer_section_pins_the_mandatory_rules():
    """Each mandatory rule of IC-27 Rev. 3.1 is pinned on its own bullet.

    The assertions address the *rule bullet* (not the whole section), so a
    rule cannot be satisfied by a word that happens to occur in another rule
    (e.g. "wörtlich" in the IDs rule does not satisfy the warnings rule).
    """
    rules = _mandatory_rules()

    # The mandatory warnings of the accepted candidates are shown verbatim.
    warnings = _rule_body(rules, "warnings")
    assert "warnings" in warnings.lower()
    assert "verbatim" in warnings.lower() or "wörtlich" in warnings.lower()

    # The runtime candidates need their own confirmation -- the relayed
    # confirmation that names them replaces the separate confirmation. The
    # label carries the `confirm-runtime` token, the body the semantics.
    runtime = _rule_body(rules, "confirm-runtime")
    assert "replaces the separate confirmation" in runtime.lower()
    assert "relayed confirmation" in runtime.lower()

    # The preview is a precondition of the apply -- pinned on the rule, not on
    # the section (the section mentions "preview" in the commands anyway).
    preview_first = _rule_body(rules, "preview first")
    assert "preview" in preview_first.lower()
    assert "confirm" in preview_first.lower()

    # The apply step is bound to the preview file.
    assert "--preview <preview.json>" in _optimizer_section()

    # Every mandatory rule carries a label, so the dict is not empty.
    assert rules, "no mandatory rules parsed"


def test_manager_optimizer_section_requires_an_approval_not_a_handoff():
    """IC-27 Rev. 3.1: a hand-off or an orchestrator message is not an approval.

    The denial must use the *approval* vocabulary of the repo
    (``approval_source: relayed``, orchestrator "approve"), not "release" --
    "release" is already bound to the version/GitHub-release workflow (§14) and
    does not carry the approval semantics.

    "release" is only tolerated inside a denial ("is not an approval or a
    release"); a positive use ("is a release") is a contract violation.
    """
    body = _rule_body(_mandatory_rules(), "ids")
    assert "config-patch-proposal-v1" in body
    assert "orchestrator" in body
    assert _APPROVAL_DENIAL_RE.search(body), body
    assert not _release_violations(body), body
    # The IDs themselves are never invented, guessed or completed. Pinned by
    # the tokens of the obligation (denial + add/guess/complete + ID), not by
    # one exact wording.
    sentences = [
        sentence
        for sentence in _sentences(body)
        if re.search(r"\bIDs?\b", sentence)
        and all(
            re.search(rf"\b{verb}\w*\b", sentence, re.IGNORECASE)
            for verb in ("add", "guess", "complete")
        )
    ]
    assert sentences, (
        "the IDs rule must forbid adding, guessing or completing an ID: " + body
    )
    assert any(_NEGATION_RE.search(sentence) for sentence in sentences), body


def test_manager_optimizer_section_requires_the_apply_report():
    """IC-27 Rev. 3.1 step 5: report ``applied.json``, backup path, ``rejected``."""
    chunk = _step_chunks()["3"]
    assert "applied.json" in chunk
    assert "approval_source: relayed" in chunk
    assert re.search(r"\bbackup\b", chunk, re.IGNORECASE), chunk
    assert "rejected" in chunk


def test_manager_optimizer_section_requires_the_artifact_contract():
    """IC-27 Rev. 3.1 step 1: the run path is returned as an artifact list.

    Pinned by the artifact names plus the ``ARTIFACTS`` marker, not by the
    placeholder spelling (``<path>`` / ``<dir>`` / ``<pfad>``).
    """
    chunk = _step_chunks()["1"]
    assert "ARTIFACTS" in chunk
    for name in ("proposal.json", "proposal.diff", "proof.json"):
        assert name in chunk, name


def test_manager_optimizer_section_states_that_the_manager_is_the_only_applier():
    sec = _optimizer_section()
    assert "meta-optimizer" in sec
    assert _ONLY_APPLIER_RE.search(sec), sec


def test_manager_version_bumped_to_1_25_0():
    fm = parse_frontmatter_file(_MANAGER_TEMPLATE)
    assert str(fm["version"]) == "1.25.0"

