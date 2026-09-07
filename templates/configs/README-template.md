<!--
Reference template for README.md — read by the `documenter` agent, never
sync-processed. Placeholders below are resolved by the documenter agent
itself from the target project's .meta-config/project.yaml and generated
context file (CLAUDE.md/AGENTS.md), not by sync.py.

Managed-block principle (same as .gitignore, issue #682 §3/§4): this
template lists the REQUIRED sections. The documenter agent adds only the
sections that are missing from an existing README.md -- it never
overwrites hand-written prose in a section that already exists.
-->

# {{PROJECT_NAME}}

> {{PROJECT_SHORT}} — one-line description.

<!--
Badges row — only emit a badge if it is actually true, never a
placeholder that resolves to a broken image:
- version: always safe (project's own version, e.g. from VERSION file or package manifest)
- stack:   always safe (primary language/runtime, e.g. from PROJECT_LANGUAGES)
- license: ONLY if a `LICENSE` file exists in the project root
- ci:      ONLY if a recognizable CI config exists (.github/workflows/*.yml,
           .gitlab-ci.yml, .circleci/config.yml, ...) -- not part of the
           default badge set, opt-in only (readme.badges: [..., ci])
-->
[![Version](https://img.shields.io/badge/version-{{VERSION}}-blue.svg)]()
[![Stack](https://img.shields.io/badge/stack-{{PROJECT_LANGUAGES}}-green.svg)]()
<!-- [![License](https://img.shields.io/badge/license-{{LICENSE_NAME}}-gray.svg)]() -- only if LICENSE file exists -->

<!--
Optional warning/important callout -- only if readme.warnings: true in
project.yaml. Omit entirely otherwise, do not render an empty callout.
-->
<!--
> [!WARNING]
> ## {{WARNING_TITLE}}
> {{WARNING_BODY}}
-->

## Setup / Quickstart

```bash
{{DEV_COMMANDS}}
{{TEST_COMMANDS}}
```

## Structure

See [`docs/CODEBASE_OVERVIEW.md`](docs/CODEBASE_OVERVIEW.md) / [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full module layout. <!-- only link the file(s) that actually exist -->
