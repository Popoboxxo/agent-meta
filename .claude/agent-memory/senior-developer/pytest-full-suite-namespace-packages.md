---
name: pytest-full-suite-namespace-packages
description: Full tests/ suite fails collection (30 scripts.lib ImportErrors) unless run with -o consider_namespace_packages=true
metadata:
  type: feedback
---

Running the whole suite at once needs `-o consider_namespace_packages=true`, else ~30 modules fail collection with `ModuleNotFoundError: No module named 'scripts.lib'`.

**Why:** the suite mixes two import styles — some test modules do `from scripts.lib...` (needs `scripts` importable as a namespace package from repo root), others do `sys.path.insert(0, .../scripts)` and `from lib...`. Under pytest's default prepend import-mode the two collide during aggregate collection (they pass individually). `consider_namespace_packages=true` makes `scripts` resolve as a namespace package and clears it.

**How to apply:** full local run =
`python3 -m pytest tests/ -p no:homeassistant -o consider_namespace_packages=true -q`
(`-p no:homeassistant` avoids the OpenSSL `lib` vs `scripts/lib` plugin collision — see [[admin-server-test-run-gotcha]]). Add `--ignore=external/` if collecting from repo root. Single-file runs need neither flag. Full run ~2.5min. See also [[admin-server-test-run-gotcha]].
