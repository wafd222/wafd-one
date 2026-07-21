from wafd_one.setup import ensure_madinah_central_and_nearby_hotels


def execute():
    # Re-run the idempotent catalogue installer after normalizing every
    # controlled Select value. Existing user records are never deleted.
    ensure_madinah_central_and_nearby_hotels()
