# WAFD ONE 10.0.0 RC258

## Quotation preview and English output

- Restored the quotation-preview back button above the mobile application header.
- Added a saved quotation language selector and an Arabic/English switch inside preview.
- Added complete editable English introduction, quotation terms, payment terms and closing text.
- Generates, prints and shares the PDF in the selected quotation language.
- Preserves the attached-menu page, signature, stamp and corrected meal-count heading in both languages.

## Direct driver launch

- Opens the installed WAFD ONE app directly on the role home page.
- Retains the role-aware legacy `/wafd-mobile` launcher for existing shortcuts.
- Redirects legacy home and Desk launch URLs to the canonical Frappe v16 role-home route.

## Deployment

Deploy the application and run the site migration. Confirm the installed version is `10.0.0rc258`, clear the site cache and reload the application. If an iPhone home-screen shortcut continues to use its old cached URL, remove that shortcut once and add it again after opening the updated site.
