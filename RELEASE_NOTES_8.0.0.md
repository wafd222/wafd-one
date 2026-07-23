# WAFD ONE v8.0.0

Production-readiness upgrade for catering contracts and projects.

## Contract operations
- Reorganized the contract form into clear operational sections.
- Added contract type, duration, first and last meal, guest segmentation and service model.
- Added VAT, discount, advance payment, contractual balance and payment terms calculations.
- Added delivery location, contact, delivery window and hotel instructions.
- Added project management, responsible kitchen and operational priority.
- Added undertaking, annex and customer file attachments.

## Project integration
- Synchronizes the new contractual, delivery, management and financial fields to the linked project.
- Adds a contract and operation snapshot to the project form.
- Adds delivery and contact details required by production and distribution teams.

## Services
- Added Suhoor service type.
- Added delivery lead time and packaging type for every service row.

## Migration
- Includes an idempotent v8.0.0 migration patch that reloads the affected DocTypes and safely initializes defaults for existing contracts.
