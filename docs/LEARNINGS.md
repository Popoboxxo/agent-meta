# LEARNINGS.md — Cross-Plugin Lessons Learned

> This file lives in the meta-repo and aggregates lessons from bugs, incidents, and discoveries across all plugins.

## Format

Use `.agent-meta/templates/learning-capture.md` for new entries.

---

## BUG-001: Mediasoup announcedAddress must match Docker host IP

**Context:** sharkord-vid-with-friends — voice channel initialization  
**Problem:** Mediasoup transport creation failed silently because `announcedAddress` was set to `127.0.0.1` inside Docker  
**Solution:** Use `HOST_LAN_IP` env variable in `docker-compose.dev.yml`; never hardcode `127.0.0.1` for WebRTC  
**Applies to:** ALL Sharkord plugins using voice/streaming  
**Date:** 2026-05-14  
**Source:** vid-with-friends@a1b2c3d

---

## DISCOVERY-001: Timestamp builds vs. 1:1 copy builds

**Context:** Release process for vid-with-friends vs. hero-introducer  
**Problem:** Inconsistent build outputs across plugins made automated release verification difficult  
**Solution:** Standardized two build variants (Variant A: Timestamp, Variant B: 1:1 Copy) with clear decision criteria  
**Applies to:** ALL Sharkord plugins  
**Date:** 2026-05-14  
**Source:** sharkord-release.md v1.3.2

---

## DISCOVERY-002: Provider-Configs können implizite Verzeichnisse haben

**Context:** agent-meta sync.py — `clean_generated_files()` in `scripts/lib/io.py`
**Problem:** Provider-Configs wie Claude haben keine expliziten `rules_dir`/`hooks_dir`/`commands_dir` Keys. Der Sync-Code nutzt Fallback-Defaults (`has_rules` Flag + Provider-Naming-Konvention `.{provider}/{dirname}`). Neue Funktionen die über Provider-Verzeichnisse iterieren MÜSSEN diese implizite Auflösung nachbilden, sonst werden Verzeichnisse übersehen.
**Solution:** `_resolve_dir()` Hilfsfunktion in `clean_generated_files()` die zuerst explizite Keys prüft, dann aus `has_*` Flags + Provider-Namen inferiert (`.{provider.lower()}/{dir_name}`). Diese Logik muss in allen neuen Funktionen repliziert werden die Provider-Verzeichnisse scannen.
**Applies to:** Alle zukünftigen sync.py-Erweiterungen die über Provider-Output-Verzeichnisse iterieren (clean, audit, migrate)
**Date:** 2026-05-17
**Source:** agent-meta@feat/super-fix-session

---

*Add new learnings via PR against this file. Reference the originating plugin and commit for traceability.*
