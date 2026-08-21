# WAFD ONE 10.0.0 RC203

## iOS lock-screen media suppression for undertakings

- Undertaking preview is now rendered as self-contained HTML, never as an inline PDF iframe.
- Issuing a PDF refreshes the HTML preview instead of opening/loading PDF media.
- Save and Share fetch PDF bytes as a Blob and never call window.open.
- Save uses a direct Blob download without a new tab.
- Share uses the native iOS Share Sheet when available.
- Clears any browser media-session metadata and pauses/removes accidental audio/video elements.
- No DocType/schema changes; migrate is not required.
