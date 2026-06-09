"""Typography styles for headings and body text."""

PAGE_TITLE_CLASS = "cad-page-title"


def get_css() -> str:
    return f"""
    .{PAGE_TITLE_CLASS} {{
        font-family: var(--cad-font-sans);
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.2;
        color: var(--cad-color-primary);
        margin: 0;
        padding: 0;
        letter-spacing: -0.02em;
    }}

    .cad-page-title-accent {{
        color: var(--cad-color-accent);
    }}
    """
