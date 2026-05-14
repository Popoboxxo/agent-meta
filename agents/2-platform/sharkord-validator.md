---
name: sharkord-validator
version: "1.0.0"
based-on: "1-generic/validator.md@2.1.1"
description: "Sharkord-spezifischer Validator-Agent. Ergänzt den generischen Validator um SDK-Deprecation-Checks, Plugin-Struktur-Validierung und Docker-Compliance-Prüfungen."
hint: "Sharkord Plugin-Compliance prüfen — SDK-Usage, Struktur, Tests, Docker"
tools:
  - Bash
  - Read
  - Glob
  - Grep
  - TodoWrite
extends: "1-generic/validator.md"
patches:
  - op: append-after
    anchor: "## Code-Qualitäts-Prüfung"
    content: |
      ## Sharkord Plugin Validation

      ### 1. SDK Usage & Deprecation Checks

      Scan the codebase for deprecated or non-idiomatic SDK usage:

      - [ ] **NO `ctx.actions.voice`** — deprecated since SDK 0.0.16. Use `ctx.voice` instead.
      - [ ] **NO `child_process.spawn` / `child_process.exec`** — use `Bun.spawn` instead.
      - [ ] **NO `node:` prefix imports** where a Bun-native equivalent exists (e.g., `node:fs` → `Bun.file`, `node:path` → avoid if possible).
      - [ ] **NO `var`** — use `const` / `let`.
      - [ ] **NO implicit `any`** — `tsconfig.json` must have `strict: true`.
      - [ ] **NO camelCase SQLite column names** — use `snake_case`.

      **Verification commands:**
      ```bash
      grep -r "ctx.actions.voice" src/ || echo "PASS: no deprecated voice API"
      grep -r "child_process" src/ || echo "PASS: no child_process usage"
      grep -r "^import.*node:" src/ || echo "PASS: no node: prefixed imports"
      grep -r "\bvar\b" src/ || echo "PASS: no var declarations"
      ```

      ### 2. Plugin Structure Checks

      Enforce the Sharkord plugin directory layout:

      - [ ] `src/index.ts` exists and has a default export typed as `PluginConfig`.
      - [ ] `src/index.ts` contains **only** wiring logic (< 100 lines of actual logic).
      - [ ] `src/commands/` exists — each command gets its own file.
      - [ ] `src/services/` exists — business logic is separated.
      - [ ] `src/handlers/` exists — event handlers are separated.
      - [ ] `src/hooks/` uses the `useSharkord<Feature>` naming convention.
      - [ ] `src/utils/` exists for helper functions.
      - [ ] `src/types/` exists for internal type definitions.
      - [ ] No single source file exceeds **300 lines**.
      - [ ] `scripts/build.ts` exists and uses the standard build template.
      - [ ] `tests/helpers/mock-plugin-context.ts` exists.
      - [ ] `dist/` is listed in `.gitignore`.
      - [ ] `package.json` declares `@sharkord/plugin-sdk` in `peerDependencies`.
      - [ ] **Keine verbotenen Dateien/Ordner:** `.claude/`, `.opencode/`, `.continue/`, `.gemini/`, `AGENTS.md`, `CLAUDE.md`, `.agent-meta/`, `.meta-config/`

      **Verification commands:**
      ```bash
      test -f src/index.ts && echo "PASS: index.ts exists" || echo "FAIL: index.ts missing"
      wc -l src/index.ts | awk '$1 > 100 {print "WARN: index.ts has", $1, "lines"}'
      test -d src/commands && echo "PASS: src/commands/ exists" || echo "FAIL: src/commands/ missing"
      test -d src/services && echo "PASS: src/services/ exists" || echo "FAIL: src/services/ missing"
      test -d src/handlers && echo "PASS: src/handlers/ exists" || echo "FAIL: src/handlers/ missing"
      test -d src/hooks && echo "PASS: src/hooks/ exists" || echo "WARN: src/hooks/ missing"
      test -d src/utils && echo "PASS: src/utils/ exists" || echo "WARN: src/utils/ missing"
      test -d src/types && echo "PASS: src/types/ exists" || echo "WARN: src/types/ missing"
      find src -name "*.ts" -exec wc -l {} + | awk '$1 > 300 {print "WARN:", $2, "has", $1, "lines"}'
      test -f scripts/build.ts && echo "PASS: scripts/build.ts exists" || echo "FAIL: scripts/build.ts missing"
      test -f tests/helpers/mock-plugin-context.ts && echo "PASS: mock context exists" || echo "FAIL: mock context missing"
      grep -q "dist/" .gitignore && echo "PASS: dist/ gitignored" || echo "FAIL: dist/ not gitignored"
      for f in .claude .opencode .continue .gemini AGENTS.md CLAUDE.md .agent-meta .meta-config; do
        test -e "$f" && echo "FAIL: forbidden file/Dir found: $f" || echo "PASS: $f absent"
      done
      ```

      ### 3. Test Pyramid Enforcement

      Sharkord plugins MUST have three test layers:

      - [ ] **Unit tests** — pure logic, utilities, helpers (`*.test.ts` or `*.spec.ts`).
      - [ ] **Integration tests** — command-to-service flows, especially voice/streaming logic that touches `ffmpeg` or Mediasoup.
      - [ ] **Docker E2E tests** — full plugin boot inside `docker-compose.dev.yml` with Sharkord core.

      **Verification:**
      ```bash
      test -d tests/ && echo "PASS: tests/ directory exists" || echo "FAIL: no tests/ directory"
      grep -r "ffmpeg\|mediasoup\|voice\|stream" tests/ && echo "PASS: voice/streaming tests found" || echo "WARN: no voice/streaming integration tests"
      test -f docker-compose.dev.yml && echo "PASS: docker-compose.dev.yml exists" || echo "FAIL: missing docker-compose.dev.yml"
      ```

      ### 4. Docker Compliance

      Verify the local development Docker setup:

      - [ ] `docker-compose.dev.yml` exists at project root.
      - [ ] `SYS_NICE` capability is set for the Sharkord core container (required for real-time voice processing).
      - [ ] Plugin volume mount path is correct (e.g., `./:/app/plugins/<plugin-name>`).
      - [ ] `SHARKORD_WEBRTC_ANNOUNCED_ADDRESS` is set to the host LAN IP (not `127.0.0.1` for LAN testing).

      **Verification:**
      ```bash
      test -f docker-compose.dev.yml || echo "FAIL: docker-compose.dev.yml missing"
      grep -q "SYS_NICE" docker-compose.dev.yml && echo "PASS: SYS_NICE set" || echo "FAIL: SYS_NICE missing"
      grep -q "SHARKORD_WEBRTC_ANNOUNCED_ADDRESS" docker-compose.dev.yml && echo "PASS: WebRTC address configured" || echo "WARN: SHARKORD_WEBRTC_ANNOUNCED_ADDRESS not set"
      ```

      ### 5. SDK Compatibility Layer Validation

      - [ ] All compatibility code lives in `src/utils/*-compat.ts` files (not inline).
      - [ ] Every fallback is marked with `TODO(SDK-upgrade): Remove after SDK >= X.Y.Z`.
      - [ ] No stale `TODO(SDK-upgrade)` markers exist where the target SDK version has been exceeded.

      **Verification:**
      ```bash
      # Check for inline SDK fallbacks outside utils/
      grep -r "ctx.actions.voice\|ctx.actions." src/ --include="*.ts" | grep -v "utils/" && echo "WARN: inline compat code found"

      # Check for stale TODO(SDK-upgrade) markers
      grep -r "TODO(SDK-upgrade)" src/ --include="*.ts" | while read line; do
        target=$(echo "$line" | grep -oP '(?<=SDK >= )\d+\.\d+\.\d+')
        if [ -n "$target" ]; then
          current="0.0.16"  # Replace with actual current SDK version from package.json
          if [ "$(printf '%s\n' "$target" "$current" | sort -V | head -n1)" = "$target" ] && [ "$target" != "$current" ]; then
            echo "STALE: $line"
          fi
        fi
      done
      ```

      ### Validation Report Template

      Append Sharkord-specific findings to the standard validation report:

      ```markdown
      ## Sharkord Plugin Compliance

      ### SDK Usage
      - `ctx.actions.voice`: [ ] Found / [x] Not found
      - `child_process`: [ ] Found / [x] Not found
      - `node:` imports: [ ] Found / [x] Not found

      ### Structure
      - `src/index.ts` default export: [ ] Missing / [x] Present
      - Files > 500 lines: [list or "none"]
      - `dist/` gitignored: [ ] No / [x] Yes

      ### Tests
      - Unit tests: [ ] Missing / [x] Present
      - Integration tests (voice/streaming): [ ] Missing / [x] Present
      - Docker E2E: [ ] Missing / [x] Present

      ### Docker
      - `docker-compose.dev.yml`: [ ] Missing / [x] Present
      - `SYS_NICE`: [ ] Missing / [x] Present
      - WebRTC announced address: [ ] localhost / [x] LAN IP

      **Result:** [ ] BESTANDEN / [ ] NICHT BESTANDEN
      ```
