# WAFD ONE 10.0.0rc51

- Fixed the acceptance opening-stock migration patch.
- Removed the invalid Dynamic Link reference to a non-existent DocType.
- Opening balances are now created using only existing WAFD Stock Balance and WAFD Stock Movement DocTypes.
- The patch remains idempotent and does not overwrite positive stock balances.
