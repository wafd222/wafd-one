"""Force the v6.3.3 print-format repair and complete the 400-hotel catalogue."""
from wafd_one.setup import ensure_hotel_undertaking_print_format, ensure_madinah_hotels_400

def execute():
    ensure_hotel_undertaking_print_format()
    ensure_madinah_hotels_400()
