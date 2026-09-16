## WAFD ONE 10.0.0 RC247 — Root Delivery Handoff Repair

RC247 fixes the root cause of the driver's empty **My Trips** page. An approved
loading could be saved while delivery-trip creation failed later, leaving no
trip record for the driver portal to display. The release now reconciles every
approved loading with a delivery trip, repairs canonical driver/login links,
and creates missing trips idempotently under normal Frappe validations.

The same secured reconciliation path is used by migration, the manager action,
the manager field-delivery page, and every driver's My Trips page. Empty states
now explain whether loading is unapproved, assignment is incomplete, or a
specific validation blocked trip creation. Driver row-level isolation remains
enforced and one bad legacy record cannot hide other employees' trips.

Validation covers driver identity, portal retrieval, the approved-loading
handoff, patch paths, release structure, and the complete employee access
matrix.
