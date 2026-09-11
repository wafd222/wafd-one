## Summary

Improve Delivery Supervisor and Driver workflows with map-first navigation and multi-day scheduling.

- always shows a Google Maps action beside the destination name in the driver trip card
- falls back to a safe Google Maps name search when no saved destination link exists
- adds supervisor destination management with search, edit, map update, and safe removal from choices
- adds full planned-trip editing before driver acceptance
- allows mistaken planned trips to be cancelled and completed test records to be hidden without deleting delivery proof or audit history
- adds one-entry scheduling for multiple days and multiple meals with independent default times and quantities
- prevents duplicate recurring trips and supports schedules up to 90 days
- preserves RC273 secure read-only beneficiary tracking links

## Upgrade

Run migrate, clear cache, and restart after installing RC274.

