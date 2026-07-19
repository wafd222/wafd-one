"""Final administration-console synchronization and navigation repair."""

from wafd_one.setup import ensure_administration_console, rebuild_workspace_from_source


def execute():
    ensure_administration_console()
    rebuild_workspace_from_source()
