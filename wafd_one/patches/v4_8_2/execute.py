"""Compatibility module for the historical patch path.

The implementation originally lived in the package ``__init__`` while
``patches.txt`` referenced ``wafd_one.patches.v4_8_2.execute``.  Keeping this
module makes that exact patch path importable on clean and partially upgraded
sites.
"""

from . import execute

__all__ = ["execute"]
