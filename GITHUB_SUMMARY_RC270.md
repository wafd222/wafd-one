Translate material names without breaking stock history

- Added editable translated display-name fields to the WAFD Ingredient master for all supported employee languages.
- Seeded multilingual names for the operational cleaning and hygiene catalog, including Waste Bags and Sanitizer Test Strips.
- Kept the canonical Arabic ingredient document name unchanged so historical receipts, issues, balances, custody, and usage records remain linked to the same item.
- Returned `ingredient_label` from Cleaning Supervisor and Storekeeper APIs according to the selected global language.
- Applied translated labels to pending receipts, custody, recent usage, material pickers, inventory balances, and expiry alerts.
- Enabled Storekeeper material search by the translated name as well as the canonical name and item code.
- Ensured the Cleaning Supervisor page header follows the globally selected language.
