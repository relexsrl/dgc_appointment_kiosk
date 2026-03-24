import re


def sanitize_hex_color(value, default="#1A237E"):
    """Return value only if it's a valid hex color, else default."""
    if value and re.match(r'^#[0-9a-fA-F]{3,8}$', value):
        return value
    return default
