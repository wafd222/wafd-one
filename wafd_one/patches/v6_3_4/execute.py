"""Re-run the corrected undertaking and hotel catalogue installation."""
from wafd_one.setup import ensure_hotel_undertaking_print_format, ensure_madinah_hotels_400


def execute():
    ensure_hotel_undertaking_print_format()
    ensure_madinah_hotels_400()
