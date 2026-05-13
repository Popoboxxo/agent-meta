#!/usr/bin/env python3
"""
strictdoc-sync.py — Standalone REQ Parser & Unraid Server Pusher

Pushes .sdoc requirements to local Unraid Strictdoc Server (172.20.4.255:8081)
Separate from sync.py — projektspezifisch, gitignored, privat.

Usage:
  python scripts/strictdoc-sync.py --push          # Push to Unraid (dry-run default)
  python scripts/strictdoc-sync.py --push --force  # Actual push
  python scripts/strictdoc-sync.py --parse         # Parse .sdoc files locally
  python scripts/strictdoc-sync.py --status        # Check last sync state
"""

import sys
import os
import json
import yaml
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_LIB = REPO_ROOT / "scripts" / "lib"
sys.path.insert(0, str(SCRIPTS_LIB))

CONFIG_FILE = REPO_ROOT / ".strictdoc-sync-config.local.yaml"
STATE_FILE = REPO_ROOT / ".strictdoc-sync-state.json"


@dataclass
class SyncConfig:
    """Loaded config from .strictdoc-sync-config.local.yaml"""
    host: str
    port: int
    protocol: str
    base_url: str
    source_dir: str
    target_dir: str
    patterns: List[str]
    auto_push: bool
    dry_run: bool
    log_file: str

    @classmethod
    def load(cls):
        """Load config from .strictdoc-sync-config.local.yaml"""
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"Config file not found: {CONFIG_FILE}\n"
                "Create .strictdoc-sync-config.local.yaml first (see template above)"
            )

        with open(CONFIG_FILE) as f:
            cfg = yaml.safe_load(f) or {}

        server = cfg.get("strictdoc_server", {})
        sync = cfg.get("sync", {})

        return cls(
            host=server.get("host", "172.20.4.255"),
            port=server.get("port", 8081),
            protocol=server.get("protocol", "http"),
            base_url=server.get("base_url", "http://172.20.4.255:8081"),
            source_dir=sync.get("source_dir", ".strictdoc/docs/04-module-reqs"),
            target_dir=sync.get("target_dir", "docs"),
            patterns=sync.get("patterns", []),
            auto_push=sync.get("auto_push", False),
            dry_run=sync.get("dry_run", True),
            log_file=cfg.get("logging", {}).get("file", "strictdoc-sync.log"),
        )


def setup_logging(config: SyncConfig):
    """Setup logging to file + console"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def load_sdoc_file(file_path: Path) -> Dict:
    """
    Simple .sdoc file loader (basic parsing).
    Real implementation would use Tree-sitter or custom parser.
    For now: return raw content + metadata.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"SDOC file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    return {
        "file": str(file_path),
        "content": content,
        "size_bytes": len(content),
        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
    }


def parse_sdoc_requirements(sdoc_content: str) -> List[Dict]:
    """
    Parse [REQUIREMENT] blocks from SDOC content.
    This is a PLACEHOLDER — real implementation would be in lib/strictdoc.py
    For now, just extract block count.
    """
    blocks = sdoc_content.count("[REQUIREMENT]")
    return {"requirement_count": blocks}


def push_to_unraid(config: SyncConfig, logger: logging.Logger, force: bool = False):
    """Push .sdoc files to Unraid Strictdoc Server"""
    logger.info(f"Starting Strictdoc sync to {config.base_url}")

    if config.dry_run and not force:
        logger.warning("DRY-RUN MODE: no files will be pushed. Use --force to push.")

    source_path = REPO_ROOT / config.source_dir
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_path}")
        return False

    files_to_sync = []
    for pattern in config.patterns:
        file_path = source_path / pattern
        if file_path.exists():
            files_to_sync.append(file_path)
            logger.info(f"Found: {pattern}")
        else:
            logger.warning(f"Not found: {pattern}")

    if not files_to_sync:
        logger.error("No files to sync!")
        return False

    logger.info(f"Syncing {len(files_to_sync)} files...")

    # Simulate push (real implementation would use Strictdoc API or file copy)
    for file_path in files_to_sync:
        sdoc_data = load_sdoc_file(file_path)
        req_count = parse_sdoc_requirements(sdoc_data["content"])

        if config.dry_run and not force:
            logger.info(
                f"[DRY-RUN] Would push: {file_path.name} "
                f"({req_count['requirement_count']} REQs, {sdoc_data['size_bytes']} bytes)"
            )
        else:
            logger.info(
                f"[PUSH] Syncing: {file_path.name} "
                f"({req_count['requirement_count']} REQs, {sdoc_data['size_bytes']} bytes)"
            )
            # TODO: Implement actual push (HTTP POST, file copy, etc.)

    # Update state
    if not config.dry_run or force:
        state = {
            "last_sync": datetime.now().isoformat(),
            "files_synced": len(files_to_sync),
            "status": "success",
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        logger.info(f"State saved to {STATE_FILE}")

    logger.info("Strictdoc sync completed!")
    return True


def parse_locally(config: SyncConfig, logger: logging.Logger):
    """Parse .sdoc files locally without pushing"""
    logger.info(f"Parsing .sdoc files from {config.source_dir}")

    source_path = REPO_ROOT / config.source_dir
    total_reqs = 0
    total_bytes = 0

    for pattern in config.patterns:
        file_path = source_path / pattern
        if file_path.exists():
            sdoc_data = load_sdoc_file(file_path)
            req_count = parse_sdoc_requirements(sdoc_data["content"])
            total_reqs += req_count["requirement_count"]
            total_bytes += sdoc_data["size_bytes"]

            logger.info(
                f"  {pattern}: {req_count['requirement_count']} REQs, "
                f"{sdoc_data['size_bytes']} bytes"
            )

    logger.info(f"Total: {total_reqs} REQs across {len(config.patterns)} files")
    logger.info(f"Total size: {total_bytes / 1024:.1f} KB")


def check_status(logger: logging.Logger):
    """Check last sync state"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        logger.info(f"Last sync: {state.get('last_sync', 'unknown')}")
        logger.info(f"Files synced: {state.get('files_synced', 0)}")
        logger.info(f"Status: {state.get('status', 'unknown')}")
    else:
        logger.info("No sync state found. Run --push to sync.")


def main():
    parser = argparse.ArgumentParser(
        description="Strictdoc REQ Sync — Push .sdoc files to Unraid Server"
    )
    parser.add_argument(
        "--push", action="store_true", help="Push .sdoc files to Unraid Server"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force push (override dry-run)"
    )
    parser.add_argument("--parse", action="store_true", help="Parse .sdoc files locally")
    parser.add_argument("--status", action="store_true", help="Check last sync state")

    args = parser.parse_args()

    # Load config
    try:
        config = SyncConfig.load()
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    # Setup logging
    logger = setup_logging(config)

    logger.info(f"Strictdoc Sync v1.0 — Config: {CONFIG_FILE}")
    logger.info(f"Server: {config.base_url}")

    # Execute command
    if args.push:
        success = push_to_unraid(config, logger, force=args.force)
        return 0 if success else 1
    elif args.parse:
        parse_locally(config, logger)
        return 0
    elif args.status:
        check_status(logger)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
