"""Design tokens as CSS custom properties."""


def get_css() -> str:
    return """
    :root {
        --cad-color-primary: #131516;
        --cad-color-accent: #e87511;
        --cad-color-surface: #ffffff;
        --cad-color-muted: #6b7280;
        --cad-font-sans: "Source Sans Pro", -apple-system, BlinkMacSystemFont,
            "Segoe UI", Roboto, sans-serif;
        --cad-space-xs: 0.5rem;
        --cad-space-sm: 0.75rem;
        --cad-space-md: 1rem;
        --cad-space-lg: 1.5rem;
        --cad-space-xl: 2rem;
        --cad-radius-sm: 0.375rem;
        --cad-shadow-sm: 0 1px 2px rgba(19, 21, 22, 0.06);
    }
    """
