---
type: "Concept"
title: "Architektur: agent-meta Admin-UI — Technische Spezifikation"
description: "- Admin-Server läuft nur auf localhost (127.0.0.1) - Kein Auth-Layer — physikalischer Maschinenzugriff = berechtigt - Super-Admin-Mode ist ein Dateisystem-Check, kein..."
tags: [concept, status:planned]
timestamp: "2026-07-27"
resource: "../../sources/docs/concepts/planned/admin-ui-architecture.md"
migrated_from: "docs/concepts/planned/admin-ui-architecture.md"
---
# Architektur: agent-meta Admin-UI — Technische Spezifikation

> Status: **Architektur-Entwurf v1.0** | 2026-06-14
> Ergänzt: `admin-ui-concept.md` — dieses Dokument beschreibt die technische Umsetzung im Detail.

---

## 1. System-Design

### 1.1 Komponenten-Diagramm

```
┌──────────────────────────────────────────────────────────────┐
│                     WEB BROWSER                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  admin-ui.html (Single File, ~3000-5000 LOC)            │  │
│  │                                                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │  │
│  │  │ Sidebar  │  │ Router   │  │ Content Panels        │ │  │
│  │  │ (nav)    │  │ (#/hash) │  │                       │ │  │
│  │  │          │  │          │  │ ┌───────────────────┐  │ │  │
│  │  │ • Project│  │          │  │ │ <config-form>     │  │ │  │
│  │  │ • Roles  │  │          │  │ │ (schema-driven)   │  │ │  │
│  │  │ • Models │  │          │  │ └───────────────────┘  │ │  │
│  │  │ • ...    │  │          │  │ ┌───────────────────┐  │ │  │
│  │  │          │  │          │  │ │ <delegation-      │  │ │  │
│  │  │ [SA]     │  │          │  │ │  canvas>          │  │ │  │
│  │  │ RolesDef │  │          │  │ └───────────────────┘  │ │  │
│  │  │ Provider │  │          │  │ ┌───────────────────┐  │ │  │
│  │  │ Skills   │  │          │  │ │ <pipeline-editor> │  │ │  │
│  │  │ MCP      │  │          │  │ └───────────────────┘  │ │  │
│  │  └──────────┘  └──────────┘  └───────────────────────┘ │  │
│  │                                                         │  │
│  │  StateManager  ←→  API  ←→  SchemaValidator             │  │
│  │  (event bus)        (fetch)  (client-side)               │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
        │ HTTP/SSE                          ▲ File Watch
        ▼                                  │ (polling)
┌──────────────────────────────────────────────────────────────┐
│              admin-server.py (Python 3.8+, stdlib)            │
│                                                               │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ HTTP Server│  │ Config Mgr   │  │ Sync Executor         │  │
│  │ (Threading │  │ (Read/Write  │  │ (subprocess.run)      │  │
│  │  MixIn)    │  │  YAML/JSON)  │  │                        │  │
│  └────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                               │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Mode Det.  │  │ Backup Mgr   │  │ File Watcher          │  │
│  │ (SA vs     │  │ (.backup/)   │  │ (polling, Phase 6)    │  │
│  │  Project)  │  │              │  │                        │  │
│  └────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│                   FILE SYSTEM                                  │
│                                                               │
│  .meta-config/project.yaml          ←→  /api/config/project   │
│  .meta-config/export.yaml           ←→  /api/config/export    │
│  .agent-meta/config/role-defaults.yaml  ←→  [SA] 角色默认     │
│  .agent-meta/config/ai-providers.yaml   ←→  [SA] Provider     │
│  .agent-meta/config/skills-registry.yaml←→  [SA] Skills       │
│  .agent-meta/config/mcp-registry.yaml   ←→  [SA] MCP          │
│  .agent-meta/config/dod-presets.yaml    ←→  [SA] DoD          │
│  .agent-meta/config/delegation-syntax.yaml←→ [SA] Delegation  │
│  .agent-meta/agents/1-generic/*.md     ←→  [SA] Templates     │
│  .opencode/3-project/*.md              ←→  /api/extensions    │
│  sync.log                              ←→  Diff-Source         │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Datenfluss: Config Edit + Sync

```
User ändert Feld          Client                  Server                Filesystem
     │                      │                       │                      │
     │  input event         │                       │                      │
     │─────────────────────►│                       │                      │
     │                      │                       │                      │
     │                      │  validate (schema)    │                      │
     │                      │─────┐                 │                      │
     │                      │     │ local validation│                      │
     │                      │◄────┘                 │                      │
     │                      │                       │                      │
     │                      │  field markiert dirty │                      │
     │                      │  "Save"-Button aktiv  │                      │
     │                      │                       │                      │
     │  click "Save"        │                       │                      │
     │─────────────────────►│                       │                      │
     │                      │                       │                      │
     │                      │  PUT /api/config/     │                      │
     │                      │  {json}               │                      │
     │                      │──────────────────────►│                      │
     │                      │                       │                      │
     │                      │                       │  Backup (optional)   │
     │                      │                       │─────────────────────►│
     │                      │                       │                      │
     │                      │                       │  Write YAML          │
     │                      │                       │─────────────────────►│
     │                      │                       │                      │
     │                      │                       │  sync.py --dry-run   │
     │                      │                       │─────┐                │
     │                      │                       │     │ subprocess      │
     │                      │                       │◄────┘                │
     │                      │                       │                      │
     │                      │  200 {status, diff,   │                      │
     │                      │        warnings}      │                      │
     │                      │◄──────────────────────│                      │
     │                      │                       │                      │
     │  Diff-Ansicht        │                       │                      │
     │  (farbig, side-by-   │                       │                      │
     │   side)              │                       │                      │
     │◄─────────────────────│                       │                      │
     │                      │                       │                      │
     │  "Sync ausführen"    │                       │                      │
     │─────────────────────►│                       │                      │
     │                      │                       │                      │
     │                      │  POST /api/sync/run   │                      │
     │                      │  (SSE stream)         │                      │
     │                      │──────────────────────►│                      │
     │                      │                       │                      │
     │                      │                       │  sync.py (real)      │
     │                      │                       │─────────────────────►│
     │                      │                       │                      │
     │                      │  SSE: event stream    │                      │
     │                      │◄──────────────────────│                      │
     │                      │  data: [WRITE] ...    │                      │
     │                      │  data: [INFO] ...     │                      │
     │                      │  data: [DONE]         │                      │
     │                      │                       │                      │
     │  Live-Output         │                       │                      │
     │◄─────────────────────│                       │                      │
```

---

## 2. Server-Implementierung

### 2.1 Modul-Struktur `scripts/admin-server.py`

```python
#!/usr/bin/env python3
"""
agent-meta Admin UI Server
==========================
Zero-dependency HTTP server for visual config management.
Start: python scripts/sync.py --admin
       python scripts/admin-server.py --port 8766
"""

import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# PyYAML — einzige externe Dependency (bereits in agent-meta verwendet)
try:
    import yaml
except ImportError:
    print("  !  PyYAML is required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── Constants ──────────────────────────────────────────────────

AGENT_META_ROOT = Path(__file__).resolve().parent.parent  # scripts/../
DEFAULT_PORT = 8766
ALLOWED_CONFIG_FILES = [
    "project", "export", "role-defaults", "ai-providers",
    "skills-registry", "mcp-registry", "dod-presets",
    "rules-presets", "delegation-syntax"
]

# File mapping: API name → filesystem path (relative to project root or agent-meta root)
CONFIG_FILE_MAP = {
    "project":           ".meta-config/project.yaml",
    "export":            ".meta-config/export.yaml",
    "role-defaults":     ".agent-meta/config/role-defaults.yaml",
    "ai-providers":      ".agent-meta/config/ai-providers.yaml",
    "skills-registry":   ".agent-meta/config/skills-registry.yaml",
    "mcp-registry":      ".agent-meta/config/mcp-registry.yaml",
    "dod-presets":       ".agent-meta/config/dod-presets.yaml",
    "rules-presets":     ".agent-meta/config/rules-presets.yaml",
    "delegation-syntax": ".agent-meta/config/delegation-syntax.yaml",
}

SUPER_ADMIN_ONLY = [
    "role-defaults", "ai-providers", "skills-registry",
    "mcp-registry", "dod-presets", "rules-presets", "delegation-syntax"
]


# ── Mode Detection ─────────────────────────────────────────────

def detect_mode(project_root: Path) -> str:
    """Detect whether we're in the agent-meta framework repo or a target repo."""
    indicators = [
        (project_root / "agents" / "1-generic").is_dir(),
        (project_root / ".agent-meta" / "agents" / "1-generic").is_dir(),
    ]
    return "super_admin" if any(indicators) else "project"


# ── Config Manager ─────────────────────────────────────────────

class ConfigManager:
    """Read/write YAML config files with backup and atomic writes."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.agent_meta_root = project_root / ".agent-meta"
        self.agent_meta_root_alt = project_root  # fallback (self-hosting)

    def resolve_path(self, config_name: str) -> Path | None:
        """Resolve a config name to a filesystem path."""
        if config_name not in CONFIG_FILE_MAP:
            return None

        rel_path = CONFIG_FILE_MAP[config_name]
        full_path = self.project_root / rel_path

        # For .agent-meta/ paths, try framework-root fallback
        if not full_path.exists() and rel_path.startswith(".agent-meta/"):
            rel_sub = rel_path[len(".agent-meta/"):]  # e.g., config/role-defaults.yaml
            alt_path = self.project_root / rel_sub
            if alt_path.exists():
                return alt_path

        return full_path

    def read(self, config_name: str) -> dict | None:
        """Read a config file and return its contents as a dict."""
        path = self.resolve_path(config_name)
        if not path or not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def write(self, config_name: str, data: dict, backup: bool = True) -> bool:
        """Write a config dict to YAML. Returns True on success."""
        path = self.resolve_path(config_name)
        if not path:
            return False

        # Backup
        if backup and path.exists():
            backup_dir = self.project_root / ".meta-config" / ".backup"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = backup_dir / f"{config_name}.{timestamp}.yaml"
            backup_path.write_bytes(path.read_bytes())

        # Atomic write via temp file
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        tmp_path.replace(path)
        return True


# ── Sync Executor ──────────────────────────────────────────────

class SyncExecutor:
    """Execute sync.py as a subprocess and stream output."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sync_script = project_root / ".agent-meta" / "scripts" / "sync.py"
        # Fallback for self-hosting
        if not self.sync_script.exists():
            self.sync_script = project_root / "scripts" / "sync.py"

    def dry_run(self, on_line=None) -> dict:
        """Run sync.py --dry-run and return structured result.
        
        If on_line is a callable, each output line is passed to it (for SSE streaming).
        Returns: {"success": bool, "output": str, "actions": int, "warnings": int}
        """
        try:
            proc = subprocess.Popen(
                [sys.executable, str(self.sync_script), "--dry-run"],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
            )
            output_lines = []
            for line in proc.stdout:
                output_lines.append(line)
                if on_line:
                    on_line(line.rstrip('\n'))
            proc.wait()
            
            full_output = ''.join(output_lines)
            return {
                "success": proc.returncode == 0,
                "output": full_output,
                "actions": full_output.count("[WRITE   ]") + full_output.count("[COPY    ]") +
                          full_output.count("[UPDATE  ]") + full_output.count("[DELETE  ]"),
                "warnings": full_output.count("warning(s)"),
            }
        except Exception as e:
            return {"success": False, "output": str(e), "actions": 0, "warnings": 0}

    def run(self, on_line=None) -> dict:
        """Run sync.py (real) and stream output."""
        return self.dry_run(on_line=on_line)  # Same logic, different subprocess call


# ── HTTP Request Handler ───────────────────────────────────────

class AdminRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the admin UI server."""
    
    # Class-level references, set by AdminServer
    config_manager: ConfigManager = None
    sync_executor: SyncExecutor = None
    mode: str = "project"
    project_root: Path = None

    def log_message(self, format, *args):
        """Suppress default logging to stderr."""
        pass  # Optional: log to file

    def _send_json(self, data: dict, status: int = 200):
        """Send a JSON response."""
        body = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def _send_html(self, html_path: Path, status: int = 200):
        """Send an HTML file."""
        if not html_path.exists():
            self._send_json({"error": "Not found"}, 404)
            return
        body = html_path.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, generator):
        """Send Server-Sent Events from a generator."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        for event in generator:
            self.wfile.write(f"data: {json.dumps(event)}\n\n".encode('utf-8'))
            self.wfile.flush()

    def _read_body(self) -> dict:
        """Read and parse JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body)

    def _check_super_admin(self, config_name: str) -> bool:
        """Check if the requested config requires super admin mode."""
        if config_name in SUPER_ADMIN_ONLY and self.__class__.mode != "super_admin":
            self._send_json({
                "error": "This config is only available in Super Admin mode",
                "required_mode": "super_admin",
                "current_mode": self.__class__.mode,
            }, 403)
            return False
        return True

    # ── Routing ────────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        qs = parse_qs(parsed.query)

        # Static UI
        if path == "" or path == "/":
            ui_path = self.__class__.project_root / "docs" / "admin-ui.html"
            if ui_path.exists():
                return self._send_html(ui_path)
            return self._send_json({"error": "admin-ui.html not found"}, 404)

        # API: mode detection
        if path == "/api/mode":
            return self._send_json({"mode": self.__class__.mode})

        # API: config read
        if path.startswith("/api/config/"):
            config_name = path.split("/api/config/")[1]
            if not self._check_super_admin(config_name):
                return
            data = self.__class__.config_manager.read(config_name)
            if data is None:
                return self._send_json({"error": f"Config '{config_name}' not found"}, 404)
            return self._send_json(data)

        # API: agents hierarchy
        if path == "/api/agents/hierarchy":
            return self._send_json(self._build_agent_hierarchy())

        # API: schema
        if path == "/api/schema/project":
            schema_path = self.__class__.project_root / ".agent-meta" / "config" / "project-config.schema.json"
            if not schema_path.exists():
                schema_path = self.__class__.project_root / "config" / "project-config.schema.json"
            if schema_path.exists():
                return self._send_json(json.loads(schema_path.read_text(encoding='utf-8')))
            return self._send_json({"error": "Schema not found"}, 404)

        # API: extensions list
        if path == "/api/extensions":
            return self._send_json(self._list_extensions())

        return self._send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path.startswith("/api/config/"):
            config_name = path.split("/api/config/")[1]
            if not self._check_super_admin(config_name):
                return
            data = self._read_body()
            if not data:
                return self._send_json({"error": "Empty body"}, 400)
            success = self.__class__.config_manager.write(config_name, data)
            if success:
                return self._send_json({"status": "saved", "config": config_name})
            return self._send_json({"error": f"Failed to write '{config_name}'"}, 500)

        return self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == "/api/sync/dry-run":
            def on_line(line):
                pass  # For SSE mode: self.wfile.write(...)
            result = self.__class__.sync_executor.dry_run()
            return self._send_json(result)

        if path == "/api/sync/run":
            result = self.__class__.sync_executor.run()
            return self._send_json(result)

        return self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── Helper Methods ─────────────────────────────────────────

    def _build_agent_hierarchy(self) -> dict:
        """Build agent hierarchy from sources (reuses viz.py logic)."""
        # Import viz module dynamically
        sys.path.insert(0, str(self.__class__.project_root / "scripts"))
        try:
            from lib.viz import build_agent_hierarchy
            from lib.config import load_config
            
            config = load_config(self.__class__.project_root)
            return build_agent_hierarchy(
                self.__class__.project_root / ".agent-meta",
                self.__class__.project_root,
                config,
            )
        except Exception as e:
            return {"error": str(e)}

    def _list_extensions(self) -> list:
        """List all extension files in 3-project directories."""
        extensions = []
        for provider_dir in [".opencode/3-project", ".claude/3-project"]:
            ext_dir = self.__class__.project_root / provider_dir
            if ext_dir.exists():
                for f in ext_dir.glob("*.md"):
                    extensions.append({
                        "name": f.name,
                        "provider": provider_dir.split('/')[0].lstrip('.'),
                        "size": f.stat().st_size,
                    })
        return extensions


# ── Server Bootstrap ───────────────────────────────────────────

class AdminServer:
    """Main server class — configures and starts the HTTP server."""

    def __init__(self, project_root: Path, port: int = DEFAULT_PORT):
        self.project_root = project_root.resolve()
        self.port = port
        self.mode = detect_mode(self.project_root)

        # Setup class-level references for the request handler
        AdminRequestHandler.config_manager = ConfigManager(self.project_root)
        AdminRequestHandler.sync_executor = SyncExecutor(self.project_root)
        AdminRequestHandler.mode = self.mode
        AdminRequestHandler.project_root = self.project_root

        self.httpd = HTTPServer(("127.0.0.1", self.port), AdminRequestHandler)

    def start(self):
        """Start the HTTP server (blocking)."""
        print(f"  i  agent-meta Admin UI")
        print(f"  i  Mode:    {self.mode}")
        print(f"  i  URL:     http://localhost:{self.port}")
        print(f"  i  Root:    {self.project_root}")
        print(f"  i  Press Ctrl+C to stop")
        print()
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  i  Server stopped.")
            self.httpd.server_close()


# ── CLI Entry Point ────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="agent-meta Admin UI Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--root", type=str, default=".", help="Project root directory")
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    server = AdminServer(project_root, args.port)
    server.start()


if __name__ == "__main__":
    main()
```

### 2.2 Integration in `sync.py`

```python
# In sync.py, nach dem argparse-Setup:

parser.add_argument("--admin", action="store_true",
                    help="Start admin UI server after sync")
parser.add_argument("--admin-only", action="store_true",
                    help="Start admin UI server without running sync")
parser.add_argument("--admin-port", type=int, default=8766,
                    help="Port for admin UI server (default: 8766)")

# ... in main():
if args.admin_only:
    from lib.admin_server import AdminServer
    AdminServer(project_root, args.admin_port).start()
    return

# ... nach sync:
if args.admin:
    from lib.admin_server import AdminServer
    print("\n  i  Starting admin UI server...")
    AdminServer(project_root, args.admin_port).start()
```

---

## 3. Frontend-Architektur

### 3.1 State Management

```javascript
/**
 * Central state manager — single source of truth for all UI state.
 * Event-driven: Components subscribe to state changes.
 */
class StateManager {
    constructor() {
        this._state = {
            mode: null,           // 'super_admin' | 'project'
            configs: {},          // config_name → data (cached from API)
            dirty: new Set(),     // Set of config_names with unsaved changes
            undoStack: [],        // [{config_name, old_value, new_value}, ...]
            redoStack: [],
            selectedRole: null,   // Currently selected role in graph editor
            syncRunning: false,
            syncOutput: '',       // Last sync.py output
            validationErrors: {}, // config_name → [{path, message}, ...]
        };
        this._listeners = new Map();  // event → Set<callback>
    }

    get(key) { return this._state[key]; }
    
    set(key, value) {
        const old = this._state[key];
        this._state[key] = value;
        this._emit(key, value, old);
    }

    on(event, callback) {
        if (!this._listeners.has(event)) this._listeners.set(event, new Set());
        this._listeners.get(event).add(callback);
    }

    _emit(event, newVal, oldVal) {
        const listeners = this._listeners.get(event);
        if (listeners) listeners.forEach(cb => cb(newVal, oldVal));
    }

    // Config-specific helpers
    markDirty(configName) { this._state.dirty.add(configName); this._emit('dirty', this._state.dirty); }
    markClean(configName) { this._state.dirty.delete(configName); this._emit('dirty', this._state.dirty); }
    
    pushUndo(configName, before) {
        this._state.undoStack.push({ config: configName, before, timestamp: Date.now() });
        if (this._state.undoStack.length > 50) this._state.undoStack.shift();
        this._state.redoStack = [];
    }
}
```

### 3.2 Router

```javascript
/**
 * Hash-based SPA router — maps #/section to content panels.
 */
class Router {
    constructor(stateManager, routes) {
        this.state = stateManager;
        this.routes = routes;  // { path: { title, component, superAdminOnly } }
        window.addEventListener('hashchange', () => this._resolve());
    }

    _resolve() {
        const hash = window.location.hash.slice(1) || '/';
        const route = this.routes[hash] || this.routes['/'];
        
        if (route.superAdminOnly && this.state.get('mode') !== 'super_admin') {
            window.location.hash = '#/';
            return;
        }
        
        document.title = `${route.title} — agent-meta Admin`;
        this.state.set('currentRoute', hash);
        
        // Show/hide sidebar items
        document.querySelectorAll('[data-route]').forEach(el => {
            el.classList.toggle('active', el.dataset.route === hash);
        });
        
        // Mount component
        const main = document.querySelector('#content');
        if (main && route.component) {
            main.innerHTML = '';
            main.appendChild(route.component());
        }
    }
}
```

### 3.3 API Client

```javascript
/**
 * Fetch wrapper with JSON parsing, error handling, and SSE support.
 */
class API {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;  // e.g., 'http://localhost:8766'
    }

    async get(path) {
        const res = await fetch(`${this.baseUrl}${path}`);
        if (!res.ok) throw new APIError(res.status, await res.json());
        return res.json();
    }

    async put(path, data) {
        const res = await fetch(`${this.baseUrl}${path}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new APIError(res.status, await res.json());
        return res.json();
    }

    async post(path, data) {
        const res = await fetch(`${this.baseUrl}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new APIError(res.status, await res.json());
        return res.json();
    }

    /**
     * Stream SSE events. Returns an AbortController for cancellation.
     * @param {string} path - SSE endpoint
     * @param {function} onEvent - callback({event, data})
     * @param {function} onError - callback(error)
     */
    streamSSE(path, onEvent, onError) {
        const controller = new AbortController();
        
        fetch(`${this.baseUrl}${path}`, { signal: controller.signal })
            .then(async response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                onEvent(data);
                            } catch (e) {
                                // Non-JSON line (sync.py output) — send as raw text
                                onEvent({ type: 'raw', text: line.slice(6) });
                            }
                        }
                    }
                }
            })
            .catch(err => {
                if (err.name !== 'AbortError') onError(err);
            });
        
        return controller;
    }
}

class APIError extends Error {
    constructor(status, body) {
        super(body?.error || `HTTP ${status}`);
        this.status = status;
        this.body = body;
    }
}
```

### 3.4 Schema-Driven Form Generator

```javascript
/**
 * Generates HTML form elements from a JSON Schema definition.
 * Supports: type=string/number/boolean/array/object, enum, pattern, required, description.
 */
class SchemaFormGenerator {
    /**
     * @param {object} schema - JSON Schema (Draft-07 subset)
     * @param {object} data - Current data values
     * @param {function} onChange - Callback(path, value) when a field changes
     * @param {array} errors - Validation errors to highlight
     */
    constructor(schema, data, onChange, errors = []) {
        this.schema = schema;
        this.data = data;
        this.onChange = onChange;
        this.errors = errors;
    }

    render() {
        if (this.schema.type === 'object') {
            return this._renderObject(this.schema, this.data, '');
        }
        return document.createTextNode('Unsupported schema type');
    }

    _renderObject(schema, data, path) {
        const container = document.createElement('div');
        container.className = 'schema-object';
        
        const properties = schema.properties || {};
        const required = new Set(schema.required || []);
        
        for (const [key, propSchema] of Object.entries(properties)) {
            const fieldPath = path ? `${path}.${key}` : key;
            const value = data?.[key] ?? propSchema.default;
            const isRequired = required.has(key);
            const fieldErrors = this.errors.filter(e => e.path === fieldPath);
            
            const field = this._renderField(key, propSchema, value, fieldPath, isRequired, fieldErrors);
            container.appendChild(field);
        }
        
        return container;
    }

    _renderField(key, schema, value, path, required, errors) {
        const wrapper = document.createElement('div');
        wrapper.className = `form-field ${errors.length ? 'has-error' : ''}`;
        
        // Label
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        if (required) {
            const star = document.createElement('span');
            star.className = 'required-star';
            star.textContent = ' *';
            label.appendChild(star);
        }
        wrapper.appendChild(label);
        
        // Description tooltip
        if (schema.description) {
            const help = document.createElement('span');
            help.className = 'form-help';
            help.title = schema.description;
            help.textContent = ' ?';
            wrapper.appendChild(help);
        }
        
        // Input element
        let input;
        if (schema.enum) {
            input = this._renderEnum(schema, value, path);
        } else if (schema.type === 'boolean') {
            input = this._renderBoolean(schema, value, path);
        } else if (schema.type === 'integer' || schema.type === 'number') {
            input = this._renderNumber(schema, value, path);
        } else if (schema.type === 'array') {
            input = this._renderArray(schema, value, path);
        } else if (schema.type === 'object') {
            input = this._renderObject(schema, value, path);
        } else {
            input = this._renderString(schema, value, path);
        }
        wrapper.appendChild(input);
        
        // Error messages
        for (const err of errors) {
            const errorEl = document.createElement('div');
            errorEl.className = 'form-error';
            errorEl.textContent = err.message;
            wrapper.appendChild(errorEl);
        }
        
        return wrapper;
    }

    _renderString(schema, value, path) {
        const multiline = schema.description?.length > 60 || (typeof value === 'string' && value.length > 80);
        const el = document.createElement(multiline ? 'textarea' : 'input');
        el.className = 'form-input';
        if (!multiline) el.type = 'text';
        el.value = value ?? '';
        if (schema.pattern) el.pattern = schema.pattern;
        el.addEventListener('input', () => this.onChange(path, el.value));
        return el;
    }

    _renderEnum(schema, value, path) {
        const el = document.createElement('select');
        el.className = 'form-select';
        for (const opt of schema.enum) {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt;
            if (opt === value) option.selected = true;
            el.appendChild(option);
        }
        el.addEventListener('change', () => this.onChange(path, el.value));
        return el;
    }

    _renderBoolean(schema, value, path) {
        const wrapper = document.createElement('label');
        wrapper.className = 'toggle-switch';
        
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = !!value;
        input.addEventListener('change', () => this.onChange(path, input.checked));
        
        const slider = document.createElement('span');
        slider.className = 'toggle-slider';
        
        wrapper.appendChild(input);
        wrapper.appendChild(slider);
        return wrapper;
    }

    _renderNumber(schema, value, path) {
        const el = document.createElement('input');
        el.type = 'number';
        el.className = 'form-input form-input-number';
        el.value = value ?? '';
        if (schema.minimum !== undefined) el.min = schema.minimum;
        if (schema.maximum !== undefined) el.max = schema.maximum;
        el.addEventListener('input', () => this.onChange(path, Number(el.value)));
        return el;
    }

    _renderArray(schema, value, path) {
        // Tag editor for string arrays
        const container = document.createElement('div');
        container.className = 'tag-editor';
        
        const tags = (value || []).filter(v => typeof v === 'string');
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'tag-input';
        input.placeholder = 'Add item...';
        
        const renderTags = () => {
            container.querySelectorAll('.tag').forEach(t => t.remove());
            for (const tag of tags) {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.innerHTML = `${tag} <button class="tag-remove">&times;</button>`;
                tagEl.querySelector('.tag-remove').addEventListener('click', () => {
                    const idx = tags.indexOf(tag);
                    if (idx >= 0) { tags.splice(idx, 1); this.onChange(path, [...tags]); renderTags(); }
                });
                container.insertBefore(tagEl, input);
            }
        };
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                e.preventDefault();
                tags.push(input.value.trim());
                this.onChange(path, [...tags]);
                input.value = '';
                renderTags();
            }
        });
        
        container.appendChild(input);
        renderTags();
        return container;
    }
}
```

### 3.5 Delegation Canvas (Vereinfacht)

```javascript
/**
 * HTML5 Canvas-based node graph editor for agent delegation.
 *
 * Architecture:
 * - Nodes = Agent roles (colored by tier)
 * - Edges = Delegation relationships (directed)
 * - Input ports on left side, output ports on right side
 * - Drag from output port → input port to create edge
 * - Click edge to delete
 * - Drag node to reposition
 *
 * The canvas is layered: background grid → edges → nodes → selection handles
 */
class DelegationCanvas {
    constructor(canvasElement, stateManager) {
        this.canvas = canvasElement;
        this.ctx = canvasElement.getContext('2d');
        this.state = stateManager;
        
        this.nodes = new Map();       // role → {x, y, w, h, role, tier, model}
        this.edges = [];              // {from, to}
        this.dragging = null;         // Currently dragged node
        this.connecting = null;       // Currently drawn edge (from role)
        this.mouseOffset = {x: 0, y: 0};
        this.offset = {x: 0, y: 0};  // Pan offset
        this.zoom = 1.0;
        this.selected = null;
        
        this._setupEventHandlers();
        this._autoLayout();
    }

    _setupEventHandlers() {
        this.canvas.addEventListener('mousedown', this._onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this._onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this._onMouseUp.bind(this));
        this.canvas.addEventListener('wheel', this._onWheel.bind(this));
        this.canvas.addEventListener('dblclick', this._onDoubleClick.bind(this));
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', this._onTouchStart.bind(this));
        this.canvas.addEventListener('touchmove', this._onTouchMove.bind(this));
        this.canvas.addEventListener('touchend', this._onTouchEnd.bind(this));
    }

    _autoLayout() {
        // Simple top-down hierarchical layout
        const roles = Array.from(this.nodes.keys());
        const root = roles.includes('orchestrator') ? 'orchestrator' : roles[0];
        const children = this._getChildren(root);
        
        const centerX = this.canvas.width / 2;
        this.nodes.get(root).x = centerX - 80;
        this.nodes.get(root).y = 60;
        
        const childWidth = this.canvas.width / Math.max(children.length, 1);
        children.forEach((role, i) => {
            const node = this.nodes.get(role);
            node.x = childWidth * i + (childWidth - node.w) / 2;
            node.y = 200;
            
            // Grandchildren
            const grandchildren = this._getChildren(role);
            grandchildren.forEach((gc, j) => {
                const gcNode = this.nodes.get(gc);
                gcNode.x = node.x + (j - (grandchildren.length - 1) / 2) * 180;
                gcNode.y = 340;
            });
        });
        
        this._render();
    }

    _getChildren(role) {
        return this.edges.filter(e => e.from === role).map(e => e.to);
    }

    _render() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        // Clear
        ctx.fillStyle = '#0f0f23';
        ctx.fillRect(0, 0, w, h);
        
        // Grid
        ctx.strokeStyle = 'rgba(42, 42, 74, 0.3)';
        ctx.lineWidth = 0.5;
        const gridSize = 40 * this.zoom;
        for (let x = this.offset.x % gridSize; x < w; x += gridSize) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let y = this.offset.y % gridSize; y < h; y += gridSize) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
        
        // Edges
        for (const edge of this.edges) {
            const from = this.nodes.get(edge.from);
            const to = this.nodes.get(edge.to);
            if (!from || !to) continue;
            
            ctx.strokeStyle = '#4dabf7';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(from.x + from.w, from.y + from.h / 2);
            ctx.lineTo(to.x, to.y + to.h / 2);
            ctx.stroke();
            
            // Arrowhead
            this._drawArrowhead(to.x, to.y + to.h / 2, -1, 0);
        }
        
        // Connecting edge (while dragging a new connection)
        if (this.connecting) {
            const from = this.nodes.get(this.connecting.from);
            const mx = this.dragging?.x || 0;
            const my = this.dragging?.y || 0;
            ctx.strokeStyle = 'rgba(255, 212, 59, 0.8)';
            ctx.lineWidth = 2;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.moveTo(from.x + from.w, from.y + from.h / 2);
            ctx.lineTo(mx, my);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        
        // Nodes
        for (const [role, node] of this.nodes) {
            const isSelected = this.selected === role;
            
            // Background
            const colors = { required: '#e03131', recommended: '#1971c2', optional: '#2a2a4a' };
            ctx.fillStyle = colors[node.tier] || colors.optional;
            ctx.strokeStyle = isSelected ? '#ffd43b' : '#4dabf7';
            ctx.lineWidth = isSelected ? 3 : 1;
            
            // Rounded rect
            const r = 8;
            ctx.beginPath();
            ctx.moveTo(node.x + r, node.y);
            ctx.lineTo(node.x + node.w - r, node.y);
            ctx.arcTo(node.x + node.w, node.y, node.x + node.w, node.y + r, r);
            ctx.lineTo(node.x + node.w, node.y + node.h - r);
            ctx.arcTo(node.x + node.w, node.y + node.h, node.x + node.w - r, node.y + node.h, r);
            ctx.lineTo(node.x + r, node.y + node.h);
            ctx.arcTo(node.x, node.y + node.h, node.x, node.y + node.h - r, r);
            ctx.lineTo(node.x, node.y + r);
            ctx.arcTo(node.x, node.y, node.x + r, node.y, r);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            
            // Label
            ctx.fillStyle = '#eaeaea';
            ctx.font = '13px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(role, node.x + node.w / 2, node.y + node.h / 2 + 5);
            
            // Output port (right side)
            ctx.fillStyle = '#4dabf7';
            ctx.beginPath();
            ctx.arc(node.x + node.w, node.y + node.h / 2, 6, 0, Math.PI * 2);
            ctx.fill();
            
            // Input port (left side)
            ctx.fillStyle = '#4dabf7';
            ctx.beginPath();
            ctx.arc(node.x, node.y + node.h / 2, 6, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    _drawArrowhead(x, y, dx, dy) {
        const ctx = this.ctx;
        const size = 10;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + dx * size - dy * size / 2, y + dy * size - dx * size / 2);
        ctx.lineTo(x + dx * size + dy * size / 2, y + dy * size + dx * size / 2);
        ctx.closePath();
        ctx.fillStyle = '#4dabf7';
        ctx.fill();
    }

    // ... hit-testing, drag handlers, edge creation, etc.
}
```

### 3.6 CSS-Arkitektur

```css
/* ── CSS Custom Properties (Design Tokens) ── */
:root {
    --bg-primary: #0f0f23;
    --bg-secondary: #1a1a2e;
    --bg-tertiary: #16213e;
    --bg-input: #0d1b2a;
    --text-primary: #eaeaea;
    --text-secondary: #a0a0b0;
    --text-muted: #6c6c80;
    --border: #2a2a4a;
    --border-focus: #4dabf7;
    --accent: #4dabf7;
    --success: #69db7c;
    --warning: #ffd43b;
    --error: #ff6b6b;
    --tier-required: #e03131;
    --tier-recommended: #1971c2;
    --tier-optional: #868e96;
    --font-mono: 'Cascadia Code', 'Fira Code', monospace;
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --radius: 8px;
    --transition: 150ms ease;
}

/* ── Layout ── */
body {
    margin: 0;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    display: grid;
    grid-template-columns: 260px 1fr;
    grid-template-rows: 48px 1fr;
    height: 100vh;
    overflow: hidden;
}

/* Header */
#header {
    grid-column: 1 / -1;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 20px;
    gap: 16px;
}

/* Sidebar */
#sidebar {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    padding: 12px 0;
}

/* Content */
#content {
    overflow-y: auto;
    padding: 24px;
}

/* ── Sidebar Navigation ── */
.nav-section {
    padding: 8px 16px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    border-left: 3px solid transparent;
    transition: background var(--transition), border-color var(--transition);
}

.nav-item:hover { background: rgba(255,255,255,0.04); color: var(--text-primary); }
.nav-item.active { background: rgba(77,171,247,0.08); color: var(--text-primary); border-left-color: var(--accent); }

.nav-badge {
    margin-left: auto;
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(255,212,59,0.15);
    color: var(--warning);
}

/* ── Form Elements ── */
.form-field {
    margin-bottom: 16px;
}

.form-label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 4px;
}

.form-input, .form-select, textarea.form-input {
    width: 100%;
    padding: 8px 12px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 0.9rem;
    transition: border-color var(--transition);
}

.form-input:focus, .form-select:focus {
    outline: none;
    border-color: var(--border-focus);
    box-shadow: 0 0 0 2px rgba(77,171,247,0.2);
}

.form-input.dirty { border-color: var(--warning); }
.has-error .form-input { border-color: var(--error); }

.form-error {
    font-size: 0.8rem;
    color: var(--error);
    margin-top: 4px;
}

/* ── Toggle Switch ── */
.toggle-switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
}

.toggle-switch input { opacity: 0; width: 0; height: 0; }

.toggle-slider {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: var(--border);
    border-radius: 12px;
    transition: var(--transition);
    cursor: pointer;
}

.toggle-slider::before {
    content: '';
    position: absolute;
    height: 18px; width: 18px;
    left: 3px; bottom: 3px;
    background: var(--text-primary);
    border-radius: 50%;
    transition: var(--transition);
}

input:checked + .toggle-slider { background: var(--accent); }
input:checked + .toggle-slider::before { transform: translateX(20px); }

/* ── Tag Editor ── */
.tag-editor {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 6px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    min-height: 36px;
}

.tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    background: rgba(77,171,247,0.15);
    border: 1px solid rgba(77,171,247,0.3);
    border-radius: 4px;
    font-size: 0.8rem;
    color: var(--accent);
}

.tag-remove {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
}

.tag-remove:hover { color: var(--error); }

.tag-input {
    flex: 1;
    min-width: 80px;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: 0.85rem;
    outline: none;
}

/* ── Provider Tabs ── */
.provider-tabs {
    display: flex;
    gap: 2px;
    border-bottom: 2px solid var(--border);
    margin-bottom: 20px;
}

.provider-tab {
    padding: 8px 20px;
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 0.9rem;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: color var(--transition), border-color var(--transition);
}

.provider-tab:hover { color: var(--text-primary); }
.provider-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

/* ── Model Override Grid ── */
.model-grid {
    width: 100%;
    border-collapse: collapse;
}

.model-grid th {
    text-align: left;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    border-bottom: 1px solid var(--border);
}

.model-grid td {
    padding: 6px 12px;
    border-bottom: 1px solid rgba(42,42,74,0.3);
    font-size: 0.9rem;
}

.model-grid .role-name { font-weight: 600; color: var(--text-primary); }
.model-grid .override { color: var(--accent); }
.model-grid .default { color: var(--text-muted); }

/* ── Diff Viewer ── */
.diff-viewer {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
    border-radius: var(--radius);
    overflow: hidden;
}

.diff-header {
    padding: 8px 12px;
    background: var(--bg-secondary);
    font-size: 0.8rem;
    color: var(--text-muted);
}

.diff-line {
    padding: 2px 12px;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    white-space: pre;
}

.diff-add { background: rgba(105,219,124,0.1); color: var(--success); }
.diff-remove { background: rgba(255,107,107,0.1); color: var(--error); }
.diff-context { color: var(--text-muted); }

/* ── Toast Notifications ── */
.toast-container {
    position: fixed;
    top: 60px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.toast {
    padding: 12px 20px;
    border-radius: var(--radius);
    font-size: 0.85rem;
    animation: slideIn 0.3s ease;
    max-width: 360px;
}

.toast-success { background: rgba(105,219,124,0.15); border: 1px solid var(--success); color: var(--success); }
.toast-error { background: rgba(255,107,107,0.15); border: 1px solid var(--error); color: var(--error); }
.toast-warning { background: rgba(255,212,59,0.15); border: 1px solid var(--warning); color: var(--warning); }
.toast-info { background: rgba(77,171,247,0.15); border: 1px solid var(--accent); color: var(--accent); }

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* ── Role Grid (Drag-and-Drop) ── */
.role-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.role-column {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    min-height: 200px;
}

.role-column h3 {
    margin: 0 0 12px;
    font-size: 0.9rem;
    color: var(--text-muted);
}

.role-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.role-card {
    padding: 8px 12px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    cursor: grab;
    font-size: 0.85rem;
    transition: border-color var(--transition), box-shadow var(--transition);
}

.role-card:hover { border-color: var(--accent); box-shadow: 0 0 8px rgba(77,171,247,0.15); }
.role-card:active { cursor: grabbing; }
.role-card.dragging { opacity: 0.5; }

.role-card.tier-required { border-color: rgba(224,49,49,0.3); background: rgba(224,49,49,0.08); }
.role-card.tier-recommended { border-color: rgba(25,113,194,0.3); background: rgba(25,113,194,0.08); }
.role-card.tier-optional { border-color: var(--border); background: transparent; }

/* ── Canvas ── */
#delegation-canvas {
    width: 100%;
    height: 600px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: grab;
}

/* ── Responsive ── */
@media (max-width: 900px) {
    body { grid-template-columns: 1fr; }
    #sidebar { display: none; }
}
```

---

## 4. Sicherheits-Konzept

### 4.1 Scope

- Admin-Server läuft **nur auf localhost** (127.0.0.1)
- Kein Auth-Layer — physikalischer Maschinenzugriff = berechtigt
- Super-Admin-Mode ist ein **Dateisystem-Check**, kein Auth-Mechanismus

### 4.2 Write-Protection

```python
# admin-server.py — Sicherheits-Prüfungen vor jedem Schreibzugriff

ALLOWED_WRITE_PATHS = [
    ".meta-config/project.yaml",
    ".meta-config/export.yaml",
    ".agent-meta/config/role-defaults.yaml",
    ".agent-meta/config/ai-providers.yaml",
    ".agent-meta/config/skills-registry.yaml",
    ".agent-meta/config/mcp-registry.yaml",
    ".agent-meta/config/dod-presets.yaml",
    ".agent-meta/config/delegation-syntax.yaml",
    ".opencode/3-project/",
    ".claude/3-project/",
]

def is_write_allowed(project_root: Path, config_name: str) -> bool:
    """Whitelist-basierte Schreibschutz-Prüfung."""
    path = CONFIG_FILE_MAP.get(config_name)
    if not path:
        return False
    # Resolve full path and normalize
    full = (project_root / path).resolve()
    # Must be within project_root
    if not str(full).startswith(str(project_root.resolve())):
        return False
    return True
```

### 4.3 Backup vor jedem Schreibzugriff

Jeder PUT-Request erzeugt einen Timestamp-basierten Backup im `.meta-config/.backup/` Verzeichnis (`.gitignore`-d).

---

## 5. Testing-Strategie

### 5.1 Unit-Tests (Python)

```python
# tests/test_admin_server.py
import json
import tempfile
import unittest
from pathlib import Path
from scripts.admin_server import ConfigManager, detect_mode

class TestModeDetection(unittest.TestCase):
    def test_super_admin_detected_by_agents_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agents" / "1-generic").mkdir(parents=True)
            self.assertEqual(detect_mode(root), "super_admin")

    def test_project_detected_by_submodule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".agent-meta").mkdir()
            self.assertEqual(detect_mode(root), "project")

class TestConfigManager(unittest.TestCase):
    def test_read_write_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir(parents=True)
            
            mgr = ConfigManager(root)
            data = {"key": "value", "nested": {"a": 1}}
            
            mgr.write("project", data)
            result = mgr.read("project")
            
            self.assertEqual(result, data)

    def test_write_creates_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir(parents=True)
            
            mgr = ConfigManager(root)
            mgr.write("project", {"v": 1})
            mgr.write("project", {"v": 2})
            
            backups = list((root / ".meta-config" / ".backup").glob("project.*.yaml"))
            self.assertEqual(len(backups), 1)
```

### 5.2 Frontend-Tests (manuell, später Playwright)

- Jeder Formular-Typ wird mit gültigen/ungültigen Werten getestet
- Drag-n-Drop auf dem Canvas wird manuell validiert
- Cross-Browser: Chromium, Firefox (Phase 2)

---

## 6. Datei-Übersicht (neue & geänderte Dateien)

```
agent-meta/
│
├── scripts/
│   ├── admin-server.py          ★ NEU — HTTP-Server (stdlib)
│   └── sync.py                  Δ GEÄNDERT — --admin Flag
│
├── docs/
│   ├── admin-ui.html            ★ NEU — Single-Page Frontend (~3000 LOC)
│   └── concepts/
│       ├── admin-ui-concept.md      ★ NEU — Konzept-Dokument
│       └── admin-ui-architecture.md ★ NEU — dieses Dokument
│
├── config/
│   └── project-config.schema.json   Δ GEÄNDERT — admin-ui Sektion
│
└── tests/
    └── test_admin_server.py     ★ NEU — Unit-Tests
```

---

## 7. Nächste Schritte

1. **Concept Review** durch den `concept-reviewer`-Agenten
2. **Prototyp:** `admin-server.py` mit GET-Endpoints + `admin-ui.html` mit Schema-Form-Generator
3. **MVP-Validierung:** Projekt-Config lesen/schreiben via UI, Sync triggern
4. **Iteration:** Drag-n-Drop Canvas, Pipeline-Editor, Super-Admin-Features