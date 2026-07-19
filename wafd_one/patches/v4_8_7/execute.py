"""Final administration Page and workspace consistency repair."""

from wafd_one.setup import ensure_administration_page, rebuild_workspace_from_source

def execute():
    ensure_administration_page()
    rebuild_workspace_from_source()
