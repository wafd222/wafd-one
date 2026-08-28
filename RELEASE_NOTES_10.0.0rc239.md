# WAFD ONE 10.0.0 RC239

## Secure driver delivery workflow

- Adds a dedicated multilingual mobile **My Trips** page for each driver instead of the raw Frappe list.
- Restricts the driver page and APIs to trips assigned to the signed-in driver's WAFD Driver record.
- Adds driver actions to start the trip, record arrival and submit delivery proof.
- Requires a delivery photo, receiver name and receiver signature unless the entire delivery is rejected, and records who uploaded the photo and when.
- Adds secure private image upload without granting drivers or supervisors broad File creation access.
- Requires and audits the loading photo before dispatch or trip creation, including uploader and upload time.
- Lets the driver review the loading photo, seal, destination, vehicle and quantities before starting.
- Preserves the current ten-language selector and localizes the dedicated driver workflow using the selected language.
- Stores operational quick notes with an Arabic management rendering while retaining the exact original free text and its language.
- Keeps names, phone numbers, identifiers and user-entered values unchanged.
- Replaces the overlapping floating back button on the loading form with an inline navigation action.
- Preserves the RC238 iPhone Saudi mobile normalization fix and all earlier role/security controls.
