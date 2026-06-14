#!/usr/bin/env python3
"""CLI tool for exporting SE decomposition graphs via configured adapters.

Usage::

    python scripts/se-export.py --graph path/to/graph.json
    python scripts/se-export.py --graph path/to/graph.json --dry-run
    python scripts/se-export.py --graph path/to/graph.json --config .meta-config/project.yaml

The tool reads the ``se-export`` section from project.yaml, selects the
matching adapter, and calls ``adapter.export_graph(graph)``.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure the repo root is on the Python path so ``scripts.lib`` is importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import yaml  # type: ignore[import]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from scripts.lib.se_export import get_adapter  # noqa: E402


def _load_project_yaml(config_path: Path) -> dict:
    """Load project.yaml and return its parsed content.

    Falls back to JSON if pyyaml is not available (unlikely in practice).

    Args:
        config_path: Path to project.yaml (or .json).

    Returns:
        Parsed configuration dict.

    Raises:
        SystemExit: If the file cannot be found or parsed.
    """
    if not config_path.exists():
        logging.error("Config file not found: %s", config_path)
        sys.exit(1)

    text = config_path.read_text(encoding="utf-8")
    try:
        if _YAML_AVAILABLE and config_path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(text) or {}
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to parse config file %s: %s", config_path, exc)
        sys.exit(1)


def _load_graph(graph_path: Path) -> dict:
    """Load and return the SE decomposition JSON graph.

    Args:
        graph_path: Path to the JSON graph file.

    Returns:
        Parsed graph dict.

    Raises:
        SystemExit: On file-not-found or JSON parse error.
    """
    if not graph_path.exists():
        logging.error("Graph file not found: %s", graph_path)
        sys.exit(1)

    try:
        return json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logging.error("Failed to parse graph JSON %s: %s", graph_path, exc)
        sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export an SE decomposition graph via a configured adapter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--graph",
        required=True,
        metavar="FILE",
        help="Path to the SE decomposition JSON graph file.",
    )
    parser.add_argument(
        "--config",
        default=".meta-config/project.yaml",
        metavar="FILE",
        help="Path to project.yaml (default: .meta-config/project.yaml).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log planned operations without writing files or making API calls.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging output.",
    )
    return parser


def main() -> None:
    """Entry point for the se-export CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    config_path = Path(args.config)
    graph_path = Path(args.graph)

    project_config = _load_project_yaml(config_path)
    se_export_config: dict = project_config.get("se-export", {})

    if not se_export_config:
        logging.error(
            "No 'se-export' section found in %s. Add one and retry.", config_path
        )
        sys.exit(1)

    # Inject dry-run flag into config so adapters can honour it
    if args.dry_run:
        se_export_config = {**se_export_config, "dry_run": True}

    graph = _load_graph(graph_path)

    logging.info(
        "Using adapter: %s", se_export_config.get("type", "(unknown)")
    )

    if args.dry_run:
        logging.info("[dry-run] No writes or API calls will be made.")

    try:
        adapter = get_adapter(se_export_config)
    except ValueError as exc:
        logging.error("Adapter configuration error: %s", exc)
        sys.exit(1)

    try:
        id_map = adapter.export_graph(graph)
    except RuntimeError as exc:
        logging.error("Export failed: %s", exc)
        sys.exit(1)

    logging.info("Export complete. %d requirements exported.", len(id_map))
    if args.verbose:
        for req_id, ext_id in id_map.items():
            logging.debug("  %s -> %s", req_id, ext_id)


if __name__ == "__main__":
    main()
