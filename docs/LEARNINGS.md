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

*Add new learnings via PR against this file. Reference the originating plugin and commit for traceability.*
