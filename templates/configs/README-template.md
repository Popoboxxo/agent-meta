<!--
Reference template for README.md — read by the `documenter` agent, never
sync-processed. Placeholders below are resolved by the documenter agent itself
from the target project config/context (not by sync.py) — one named exception:
the agent-meta badge's `{{AGENT_META_VERSION}}` is sync-embedded, not project-derived.

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
- agent-meta: opt-in only -- rendered ONLY when `agent-meta` is explicitly
           listed in readme.badges. Value comes from AGENT_META_VERSION
           (the value embedded at sync time, refreshed by the preceding
           re-sync -- never a separate live read).
           - unknown value -> label `agent-meta`, message `unknown` (no `v`
             prefix). The value is unknown when it is missing, empty, or the
             sentinel `"unknown"`/`vunknown` (read_version() returns the
             literal "unknown" when no VERSION file exists):
             [![agent-meta unknown](https://img.shields.io/badge/agent--meta-unknown-blue.svg)](https://github.com/{{AGENT_META_REPO}}/releases)
             The releases page is the always-valid link fallback; omit the link
             entirely when the repo guard below is not met. Never fabricate a
             `.../releases/tag/vunknown` link -- the tag link is valid only for
             a real version.
           - escaping is mandatory, but applies ONLY to the badge IMAGE segment
             (the blank value, no `v`): a literal `-` becomes `--` there,
             THEN a single literal `v` is prepended. The label is already
             literal `agent--meta` and must NOT be escaped again (double
             escaping yields `agent----meta`). Raw 0.101.0-beta.6 -> escaped
             0.101.0--beta.6 -> message v0.101.0--beta.6 (never `vv`).
             The link target is NEVER escaped (it keeps the raw value).
           - link target: the tag-specific
             https://github.com/{{AGENT_META_REPO}}/releases/tag/v<version>
             -- the RAW version value, no shields escaping (the real git tag
             for 0.101.0-beta.6 is v0.101.0-beta.6; an escaped
             v0.101.0--beta.6 link would 404). Use it only when
             AGENT_META_REPO is non-empty and contains a `/`; otherwise
             render the badge without a link.
-->
[![Version](https://img.shields.io/badge/version-{{VERSION}}-blue.svg)]()
[![Stack](https://img.shields.io/badge/stack-{{PROJECT_LANGUAGES}}-green.svg)]()
<!-- [![License](https://img.shields.io/badge/license-{{LICENSE_NAME}}-gray.svg)]() -- only if LICENSE file exists -->
<!-- [![agent-meta v{{AGENT_META_VERSION}}](https://img.shields.io/badge/agent--meta-v<escaped-version>-blue.svg)](https://github.com/{{AGENT_META_REPO}}/releases/tag/v{{AGENT_META_VERSION}}) -- opt-in only: emit only when `agent-meta` is listed in readme.badges -->
<!-- example note: the label `agent--meta` above is already escaped and is NOT escaped again -- only the blank substituted version value is `-`->`--` mapped in the image segment, then a single literal `v` is prepended, so a pre-release renders as `v0.101.0--beta.6` (raw `0.101.0-beta.6`, never `vv`). The tag link is used only for a real version; for a missing/empty version or the sentinel `"unknown"`/`vunknown`, emit the badge with label `agent-meta`, message `unknown` and the releases-page link fallback, never a `vunknown` tag link. -->

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
