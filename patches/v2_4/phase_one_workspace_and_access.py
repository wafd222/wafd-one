from wafd_one.setup import apply_setup


def execute():
    """Finalize Phase 1 after DocTypes have been synchronized."""
    apply_setup(force_rebuild=True, assign_manager_access=True)
