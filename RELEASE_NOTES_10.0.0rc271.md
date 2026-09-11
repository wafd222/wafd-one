# WAFD ONE 10.0.0 RC271

## Simple Delivery Supervisor

- Replaced the duplicated Delivery Supervisor cards with four practical actions: add delivery, current deliveries, delivery records, and locations/hotels.
- Added a searchable hotel/location picker and a quick form for adding hotels, mosques, Haram sites, Iftar sites, companies, and other destinations.
- Added flexible delivery planning independent of Loading Records. The supervisor chooses the destination, date, driver, optional vehicle, optional meal count, and notes.
- Added requested meal-time defaults: breakfast 04:00, lunch 10:00, dinner 17:00, and Iftar Saim 12:00. Every time remains editable.
- Added four common Madinah mosque destinations during migration.
- Delivery tasks now appear directly in the selected driver's trip screen.
- The driver accepts the delivery, opens the destination map, records arrival, and submits a required delivery photo.
- The driver's current GPS coordinates and the server delivery timestamp are required and stored with the proof; the driver must allow phone location access.
- Delivery records show the proof photo, actual time, and actual map location to the Delivery Supervisor and operations management.
- Simplified supervisor-plan proof: receiver name, signature, vehicle, and meal count are optional; the photo is mandatory.
- Preserved the existing controlled Loading Record delivery workflow for legacy/production trips.
- Added translated driver delivery labels and meal names for Arabic, English, Indonesian, Urdu, Hindi, Bengali, French, Hausa, Swahili, and Uzbek using the single language selected on Role Home.

## Upgrade

Run **Migrate Site**, **Clear Cache**, and **Build Assets**, then sign out and sign in again.
