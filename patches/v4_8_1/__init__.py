"""Compatibility patch: validate the canonical administration Desk Page."""

from wafd_one.setup import ensure_administration_page, rebuild_workspace_from_source

def execute():
    ensure_administration_page()
    rebuild_workspace_from_source()
