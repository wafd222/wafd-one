# WAFD ONE 10.0.0 RC173

## Client Portal tracking integrity fix
- Resolve loading records through the Delivery Trip -> Loading Record link, so historical operations remain visible even when loading and trip timestamps fall on adjacent dates.
- Receipt is considered complete only from a Receiving Note with status `تم الاستلام / Received` or an explicit client acknowledgement.
- Never infer receipt time from arrival time and never use planned departure as the actual delivery start.
- Add actual arrival time, actual receipt time, receiver name/title, received quantity and delivery-to-receipt duration to the beneficiary portal.
- Keep project isolation and financial/inventory privacy unchanged.
- Duration renders in minutes or hours/minutes according to elapsed time.
