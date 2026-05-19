"""Rule embedding for providers without native rules directories (e.g. opencode)."""

from pathlib import Path

from .log import SyncLog


def _strip_rule_frontmatter(content: str) -> str:
    """Remove YAML frontmatter block from a rule file."""
    if not content.startswith('---'):
        return content
    end = content.find('\n---', 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip('\n')


def _collect_embedded_rules_md(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str = "Claude",
    provider_config: dict | None = None,
) -> str:
    """Collect all active rules and return them as concatenated markdown.

    Used to embed rules into AGENTS.md for providers without a native rules directory
    (e.g. opencode). Respects `opencode: skip` rule option and speech-mode config.
    """
    from .config import substitute
    from .rules import collect_rule_sources, resolve_rules, SPEECH_DIR

    pc = (provider_config or {}).get(provider, {})
    provider_vars = {
        'EXTENSION_DIR': pc.get('extension_dir', '.claude/3-project'),
        'SNIPPETS_DIR': pc.get('snippets_dir', '.claude/snippets'),
        'PENDING_TASKS_FILE': pc.get('pending_tasks_file', '.claude/pending-tasks.md'),
        'SKILLS_DIR': pc.get('skills_dir', '.claude/skills'),
    }
    merged_vars = {**variables, **provider_vars}

    platforms = config.get('platforms', [])
    sources = collect_rule_sources(agent_meta_root, platforms)
    rule_options = resolve_rules(config, agent_meta_root)

    sections: list[str] = []

    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        opts = rule_options.get(rule_stem, {})
        if opts.get('opencode') == 'skip':
            continue
        content = source_path.read_text(encoding='utf-8')
        rel_source = f'rules/{source_path.parts[-2]}/{source_path.name}'
        content = substitute(content, merged_vars, rel_source, log)
        body = _strip_rule_frontmatter(content).strip()
        if body:
            sections.append(body)

    # Include speech-mode rule if configured (not handled by collect_rule_sources)
    mode = config.get('speech-mode', 'full')
    if mode != 'full':
        speech_path = agent_meta_root / SPEECH_DIR / f'{mode}.md'
        if speech_path.exists():
            body = _strip_rule_frontmatter(speech_path.read_text(encoding='utf-8')).strip()
            if body:
                sections.append(body)

    return '\n\n---\n\n'.join(sections)


def _build_opencode_managed_block(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str = "Claude",
    provider_config: dict | None = None,
) -> str:
    """Build the managed block for AGENTS.md: agent hints + all embedded rules."""
    from .config import substitute
    from .context_claude import _load_claude_md_managed_template

    template = _load_claude_md_managed_template(agent_meta_root)
    managed = substitute(template, variables, 'AGENTS.md managed block', log)

    rules_md = _collect_embedded_rules_md(agent_meta_root, config, variables, log,
                                            provider=provider, provider_config=provider_config)
    if rules_md:
        managed = managed.replace(
            '<!-- agent-meta:managed-end -->',
            f'\n## Regeln\n\n{rules_md}\n<!-- agent-meta:managed-end -->',
        )

    return managed
