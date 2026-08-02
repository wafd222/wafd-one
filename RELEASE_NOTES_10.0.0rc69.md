# WAFD ONE 10.0.0 RC69

- Reapplies the approved invoice header layout: contact information upper-left, company identity centered, logo upper-right.
- Adds an explicit server-side **Submit Payment & Finish** action.
- Submits the payment, refreshes invoice totals/status, closes the project financially, and returns to the operations dashboard.
- Makes the final workflow step atomic and repeat-safe instead of depending on a client-side submit event.
