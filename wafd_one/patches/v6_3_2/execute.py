"""Force-repair all stored Hotel Undertaking print formats."""

from wafd_one.setup import ensure_hotel_undertaking_print_format


def execute():
    ensure_hotel_undertaking_print_format()
