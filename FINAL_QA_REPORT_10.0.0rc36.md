# WAFD ONE 10.0.0rc36 — Document Suite QA

## Scope

This release replaces the partial invoice-only branding change with a complete, unified Document Studio suite.

## Rebuilt templates

1. Hotel undertaking
2. Contract
3. Quotation
4. Tax invoice
5. Project operation order
6. Production order
7. Meal preparation order
8. Loading and dispatch order
9. Delivery note and proof
10. Certificate of appreciation

## Confirmed corrections

- Official WAFD Al-Madinah logo is present in every rebuilt template.
- A4 portrait layout uses zero renderer margins and controlled internal coordinates.
- Invoice footer and totals remain inside the first page for ordinary invoices.
- Invoice table widths total 100%, preventing right-side clipping.
- Hotel undertaking is explicitly one-party and contains only WAFD company signature/stamp approval.
- The migration patch creates any missing core template before applying the design.
- Existing enabled templates in the ten supported categories are upgraded, not only the default invoice.

## Static validation

- 84 patch entries validated.
- Release version consistency validated.
- Python syntax validated.
- JSON metadata validated.
- JavaScript syntax validated.
- Distribution cache files removed.

## Runtime acceptance checks after migration

Open one real document from each category and generate Template PDF. Confirm the logo loads from the site assets, Arabic text uses the server font fallback, and long tables continue to a second page when applicable.
