"""SE export adapter package.

Provides a factory function to instantiate the correct adapter based on
the ``se-export.type`` configuration key from project.yaml.

Usage::

    from scripts.lib.se_export import get_adapter

    adapter = get_adapter(config["se-export"])
    id_map = adapter.export_graph(graph)
"""

from .base import SEAdapter
from .github_issues_adapter import GitHubIssuesAdapter
from .markdown_adapter import MarkdownAdapter

__all__ = ["GitHubIssuesAdapter", "MarkdownAdapter", "SEAdapter", "get_adapter"]

_ADAPTER_MAP = {
    "markdown": MarkdownAdapter,
    "github_issues": GitHubIssuesAdapter,
}


def get_adapter(config: dict) -> SEAdapter:
    """Instantiate the SE export adapter specified by *config*.

    Args:
        config: The ``se-export`` section of project.yaml.  Must contain
                ``type`` (one of ``markdown`` | ``github_issues``).

    Returns:
        A concrete :class:`SEAdapter` instance ready to use.

    Raises:
        ValueError: If ``type`` is missing or not one of the known adapters.
    """
    adapter_type: str = config.get("type", "")

    if adapter_type not in _ADAPTER_MAP:
        known = ", ".join(sorted(_ADAPTER_MAP))
        raise ValueError(
            f"Unknown se-export adapter type: {adapter_type!r}. "
            f"Known types: {known}"
        )

    adapter_class = _ADAPTER_MAP[adapter_type]

    if adapter_type == "markdown":
        output_dir: str = config.get("output_dir", "docs/se")
        return adapter_class(output_dir=output_dir)

    # github_issues and future adapters receive the full config dict
    return adapter_class(config=config)
