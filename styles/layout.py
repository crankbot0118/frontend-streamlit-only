"""Layout styles for page structure and header placement."""

PAGE_HEADER_CLASS = "cad-page-header"


def get_css() -> str:
    return f"""
    .{PAGE_HEADER_CLASS} {{
        width: 100%;
        padding: var(--cad-space-lg) 0 var(--cad-space-md);
        margin-bottom: var(--cad-space-lg);
        border-bottom: 1px solid rgba(19, 21, 22, 0.08);
    }}

    .cad-main-content {{
        padding-top: var(--cad-space-sm);
    }}
    """
