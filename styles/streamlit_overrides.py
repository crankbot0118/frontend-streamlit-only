"""Streamlit framework overrides — reset default spacing so custom layout controls the top edge."""


def get_css() -> str:
    return """
    /* Streamlit reserves ~5rem top padding on the main block for its toolbar */
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0;
        padding-bottom: 2rem;
    }

    /* Remove extra gap above the first element in the main area */
    [data-testid="stAppViewContainer"] .main .block-container > div:first-child {
        margin-top: 0;
        padding-top: 0;
    }

    /* Keep the built-in toolbar but stop it from stealing vertical space from content */
    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        right: 0;
    }
    """
