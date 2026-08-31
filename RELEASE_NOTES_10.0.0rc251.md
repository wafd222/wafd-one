# WAFD ONE 10.0.0 RC251

## Quotation migration controller fix

- Adds the missing `wafd_quotation_item.py` controller required by Frappe v16 while synchronizing the `WAFD Quotation Item` child DocType.
- Prevents the `ModuleNotFoundError` that stopped site migration at the quotation item metadata.
- Adds a release validation check that fails packaging if the child DocType module or controller class is missing.
- Re-syncs the quotation item, quotation parent and quotation print format in dependency order.
- Retains the complete RC250 quotation feature set, independent signature/stamp visibility controls and existing operational workflows.

## Upgrade

Deploy RC251 and run site migration again. The failed RC250 migration did not complete the quotation model sync; RC251 safely resumes it.
