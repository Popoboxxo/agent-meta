#!/usr/bin/env python3
"""Identity and policy readers for the deployed orchestrator guard.

Issue #1238b2: importable replacements for the former inline Python readers.
Each subcommand is an independent, side-effect-free policy primitive; grant and
strict-mode readers retain their original fail-closed defaults.
"""
from __future__ import annotations

import json
import re
import sys


def _sentinel(stdin: str) -> int:
    # Bytes-in (surrogateescape), like hook_json_get: invalid UTF-8 must not
    # crash this read and silently drop a legitimate sentinel.
    content = stdin.lstrip()
    line = content.split('\n', 1)[0].strip()
    match = re.match(
        r'^#agent-meta:agent=([A-Za-z0-9_-]+)(?:\s+id=([A-Za-z0-9._-]+))?$',
        line,
    )
    if not match:
        print('')
        return 0
    role, instance_id = match.group(1), match.group(2) or ''
    if instance_id and not (
        re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,39}', instance_id)
        and '..' not in instance_id
    ):
        print('')
        return 0
    print(role + '|' + instance_id)
    return 0


def _allowlist_mode(argv: list[str]) -> int:
    if len(argv) != 1:
        return 1
    try:
        with open(argv[0]) as handle:
            data = json.load(handle)
        print(data.get('mode', 'off'))
    except Exception:
        print('off')
    return 0


def _allowlist_eligible(argv: list[str]) -> int:
    if len(argv) != 2:
        return 1
    try:
        with open(argv[0]) as handle:
            data = json.load(handle)
        print('1' if argv[1] in data.get('eligible_roles', []) else '0')
    except Exception:
        print('0')
    return 0


def _allowlist_grant(argv: list[str]) -> int:
    if len(argv) != 2:
        return 1
    try:
        with open(argv[0]) as handle:
            data = json.load(handle)
        print('1' if argv[1] in data.get('authority_overrides', {}) else '0')
    except Exception:
        print('0')
    return 0


def _resolve_mode(orchestrator: dict, provider: str):
    override = orchestrator.get('provider-overrides', {}).get(provider, {})
    mode = override.get('mode')
    if mode is not None:
        return mode
    return orchestrator.get('mode')


def _fallback_strict_scan(config_file: str) -> bool:
    # A line scan, not a YAML parser: anything it cannot judge resolves strict.
    try:
        with open(config_file, encoding='utf-8-sig') as handle:
            lines = handle.read().splitlines()
    except Exception:
        return True
    in_block = False
    for raw in lines:
        if raw.lstrip().startswith('#') or not raw.strip():
            continue
        line = raw.split(' #', 1)[0].rstrip()
        stripped = line.lstrip()
        key, _, value = stripped.partition(':')
        key = key.strip().strip(chr(34) + chr(39))
        value = value.strip().strip(chr(34) + chr(39))
        if len(line) == len(stripped):  # top-level key
            in_block = key == 'orchestrator'
            if in_block and value:
                return True  # inline/flow/anchored value: ambiguous
            continue
        if not in_block:
            continue
        if key == '<<' or value[:1] in ('{', '[', '&', '*', '!'):
            return True  # merge key, flow style, anchor/alias, tag: ambiguous
        if key == 'mode' and value.lower() == 'strict':
            return True
        if key == 'strict' and value.lower() not in (
            'false', 'no', 'off', '0', '~', 'null', ''
        ):
            return True
    return False


def _strict(argv: list[str]) -> int:
    if len(argv) != 2:
        return 1
    config_file, provider = argv
    try:
        import yaml

        with open(config_file) as handle:
            config = yaml.safe_load(handle) or {}
        orchestrator = config.get('orchestrator', {})
        mode = _resolve_mode(orchestrator, provider)
        if mode is not None:
            mode = str(mode).strip().lower()
            print('true' if mode == 'strict' else 'false')
        else:
            strict = orchestrator.get('strict', False)
            enabled = orchestrator.get('enabled', True)
            print('true' if strict and enabled else 'false')
    except Exception as exc:
        strict = _fallback_strict_scan(config_file)
        verdict = (
            'strict indicator found or scan inconclusive, failing closed (STRICT=true)'
            if strict else 'no strict indicator found (STRICT=false)'
        )
        sys.stderr.write(
            'ORCHESTRATOR_GUARD: warning: could not read project.yaml with PyYAML ('
            + type(exc).__name__ + '); conservative stdlib line scan: '
            + verdict + '.\n'
        )
        print('true' if strict else 'false')
    return 0


def _ask_enabled(argv: list[str]) -> int:
    if len(argv) != 1:
        return 1
    try:
        import yaml

        with open(argv[0], encoding='utf-8-sig') as handle:
            config = yaml.safe_load(handle) or {}
        value = (config.get('orchestrator') or {}).get('destructive-ask', False)
        if isinstance(value, dict):
            value = value.get('enabled', False)
        print(
            '1'
            if str(value).strip().lower() in ('true', '1', 'yes', 'on')
            else '0'
        )
    except Exception:
        print('0')
    return 0


def _ask_json(argv: list[str]) -> int:
    if len(argv) != 1:
        return 1
    command = argv[0]
    command = re.sub(
        r'(?i)\b(token|password|passwd|secret|api[_-]?key)([=:]\s*)(\S+)',
        r'\1\2<redacted>',
        command,
    )
    print(
        json.dumps(
            {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'ask',
                    'permissionDecisionReason': command
                    + ' (class=ask, issue #1217)',
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str], stdin: str) -> int:
    """Run one named guard policy primitive and return its exit code."""
    if not argv:
        return 1
    command, args = argv[0], argv[1:]
    readers = {
        'sentinel': _sentinel,
        'allowlist-mode': _allowlist_mode,
        'allowlist-eligible': _allowlist_eligible,
        'allowlist-grant': _allowlist_grant,
        'ask-enabled': _ask_enabled,
        'strict': _strict,
        'ask-json': _ask_json,
    }
    reader = readers.get(command)
    if reader is None:
        return 1
    if command == 'sentinel':
        return reader(stdin)
    return reader(args)


if __name__ == "__main__":
    sys.exit(
        main(
            sys.argv[1:],
            sys.stdin.buffer.read().decode('utf-8', 'surrogateescape'),
        )
    )
