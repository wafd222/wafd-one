# WAFD ONE 10.0.0 RC62

- Rebuilds contract reset/permanent deletion around the complete operational workflow.
- Discovers legacy stock movements through project, production batch, and operational-document references.
- Automatically includes same-contract Issue, Waste, and Transfer movements even when their project field is empty.
- Reverses the full stock dependency chain newest-first before older receipts.
- Blocks only genuinely external, reserved, or unsafe adjustment dependencies.
- Preserves transactional rollback: no partial deletion when any step fails.
- Retains RC61 specialized warehouse and cold-room routing.
