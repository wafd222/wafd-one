"""RC141 migration-safety marker.

The actual fix is in ``wafd_one.setup`` and must be importable before schema
updates begin.  This patch intentionally does no database mutation.
"""

def execute():
    return
