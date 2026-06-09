"""Modular CSS system for the Clone Automation Dashboard."""

from styles.base import inject_css
from styles.layout import get_css as layout_css
from styles.tokens import get_css as tokens_css
from styles.typography import get_css as typography_css

__all__ = ["apply_global_styles"]


def apply_global_styles() -> None:
    """Inject all shared style modules."""
    inject_css(
        tokens_css(),
        typography_css(),
        layout_css(),
    )
