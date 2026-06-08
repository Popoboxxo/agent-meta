# Tests for agent-meta sync.py

Test suite for the agent-meta sync framework. Covers the Python modules in `scripts/lib/`
with unit tests and end-to-end integration tests.

## Quick Start

```bash
# Install test dependencies
pip install pytest pyyaml

# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/integration/ -v

# Run a specific test file
python -m pytest tests/unit/test_config.py -v

# Run with coverage (if pytest-cov is installed)
pip install pytest-cov
python -m pytest tests/ --cov=scripts/lib --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (temp dirs, sample configs)
├── unit/
│   ├── test_config.py       # config loading, substitute(), conditional blocks
│   ├── test_dod.py          # DoD preset loading and resolution
│   ├── test_providers.py    # Provider config loading and resolution
│   ├── test_io.py           # YAML/JSON loading, safe_path, content_hash
│   ├── test_log.py          # SyncLog collection and writing
│   ├── test_bootstrap.py    # BootstrapEngine for provider bootstrap
│   └── test_agents.py       # Frontmatter parsing, composition, XML wrapping
└── integration/
    └── test_sync_e2e.py     # End-to-end sync simulation, multi-provider tests
```

## Fixtures

`conftest.py` provides reusable fixtures for all tests:

| Fixture | What it provides |
|---------|-----------------|
| `temp_dir` | Temporary directory (auto-cleanup) |
| `agent_meta_root` | Minimal agent-meta root with VERSION, config/, agents/, rules/ |
| `sample_dod_presets_yaml` | Sample dod-presets.yaml with 'full' and 'rapid-prototyping' |
| `sample_providers_yaml` | Minimal ai-providers.yaml with Claude + Gemini |
| `sample_role_defaults_yaml` | Minimal role-defaults.yaml |
| `sample_project_yaml` | Project config with DoD: rapid-prototyping |
| `sample_agent_template` | A generic agent template with placeholders |
| `sample_variables` | Pre-built variable dict for substitution tests |

## Writing New Tests

### Unit Test Example

```python
from scripts.lib.config import substitute
from scripts.lib.log import SyncLog

def test_my_feature(sample_variables):
    log = SyncLog()
    result = substitute("Hello {{PROJECT_NAME}}", sample_variables, "test", log)
    assert result == "Hello TestProject"
```

### Integration Test Example

```python
def test_end_to_end(full_agent_meta_root, full_project_root):
    """See test_sync_e2e.py for full example of sync setup and verification."""
    from scripts.lib.config import load_config, build_variables
    from scripts.lib.agents import sync_agents_for_provider
    from scripts.lib.providers import load_providers_config

    config = load_config(config_path)
    variables, _ = build_variables(config, full_agent_meta_root)
    provider_config = load_providers_config(full_agent_meta_root)
    log = SyncLog()

    sync_agents_for_provider(
        full_agent_meta_root, project_root, config, variables,
        log, dry_run=False, provider="Claude", provider_config=provider_config,
    )

    # Verify output
    assert (project_root / ".claude" / "agents" / "orchestrator.md").exists()
```

## CI/CD

Tests run on GitHub Actions:

- **Push** to `main`/`master` (when scripts/, config/, agents/, or tests/ change)
- **Pull Request** to `main`/`master`
- **Manual trigger** via `workflow_dispatch`

Python versions: 3.11, 3.12

## Conventions

- Test file names: `test_<module>.py` for unit tests, `test_<feature>.py` for integration
- Test class names: `Test<Feature>` (PascalCase)
- Test method names: `test_<what_happens>` (snake_case)
- Use `conftest.py` fixtures — avoid duplicating setup
- Use `SyncLog` for tests that exercise log-aware functions
- Temporary directories auto-cleanup via pytest fixtures
- No external dependencies beyond `pytest` and `pyyaml`
