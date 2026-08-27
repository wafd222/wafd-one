# WAFD ONE 10.0.0 RC238

## iPhone Saudi mobile input normalization fix

- Fixes valid Saudi mobile numbers being rejected when iOS inserts invisible direction or isolation characters.
- Extracts and validates the digits before normalizing `05xxxxxxxx` to `+9665xxxxxxxx`.
- Keeps support for Arabic/Persian numerals and local, `966`, `+966` and `00966` formats.
- Replaces the mixed-direction validation text with a short, readable Arabic message.
- Preserves all RC237 employee navigation fixes, roles, permissions and operational workflows.
