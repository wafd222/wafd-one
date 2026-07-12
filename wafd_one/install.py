"""Installation helpers for WAFD ONE.

The first stable cloud release intentionally performs no ERPNext-specific setup.
This keeps the app installable on a clean Frappe Framework v16 site.
"""


def after_install():
    """Reserved for safe, Frappe-only initialization in a future release."""
    return None
