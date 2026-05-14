# Learning Capture Template

Use this template when a session produces insights relevant beyond a single project.

```markdown
## <Learning Title>

**Context:** Which project(s) and situation  
**Problem:** What went wrong or was unclear  
**Solution:** What fixed it or the recommended approach  
**Applies to:** Which projects should follow this  
**Date:** YYYY-MM-DD  
**Source:** Commit hash or session reference
```

## Example

```markdown
## BUG-001: Mediasoup announcedAddress must match Docker host IP

**Context:** sharkord-vid-with-friends — voice channel initialization  
**Problem:** Mediasoup transport creation failed silently because `announcedAddress` was set to `127.0.0.1` inside Docker  
**Solution:** Use `HOST_LAN_IP` env variable in `docker-compose.dev.yml`; never hardcode `127.0.0.1` for WebRTC  
**Applies to:** ALL Sharkord plugins using voice/streaming  
**Date:** 2026-05-14  
**Source:** vid-with-friends@a1b2c3d
```
