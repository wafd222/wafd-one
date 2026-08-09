# WAFD ONE 10.0.0 RC145

- Fixed stale workflow states between Daily Plan, Production, Packaging, Loading and Delivery.
- Daily plans no longer regress to In Production when production batches already exist downstream.
- Existing production batches are opened directly instead of presenting a duplicate creation flow.
- Production Batch primary action now follows the furthest persisted stage and opens existing Packaging, Loading or Delivery documents.
- Added server-side protection against repeating production/material-issue actions after a later stage exists.
- Delivery proof now synchronizes the parent Daily Meal Plan status.
- Added migration repair for historical records: delivered chains become Completed/Delivered and downstream chains no longer appear as fresh production.
