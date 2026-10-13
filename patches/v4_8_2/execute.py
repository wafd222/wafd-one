"""Compatibility patch for the historical v4.8.2 path.

Keep a real callable in this module. Importing ``execute`` from the package with
``from . import execute`` is unsafe here because this module itself is named
``execute`` and Python may resolve the package attribute to the module object.
"""

from wafd_one.setup import ensure_administration_page, rebuild_workspace_from_source


def execute():
    ensure_administration_page()
    rebuild_workspace_from_source()
