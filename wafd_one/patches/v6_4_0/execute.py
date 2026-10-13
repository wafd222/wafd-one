"""Finalize the safe undertaking template and verified hotel catalogue."""
from wafd_one.setup import ensure_hotel_undertaking_print_format, ensure_madinah_hotels_400


def execute():
    ensure_hotel_undertaking_print_format()
    ensure_madinah_hotels_400()
