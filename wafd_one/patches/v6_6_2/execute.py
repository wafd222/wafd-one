"""Recovery patch for Document Studio template naming.

Safe to run whether v6_6_0 completed, partially ran, or failed.
"""

from wafd_one.patches.v6_6_0.execute import execute as ensure_document_templates


def execute():
    ensure_document_templates()
