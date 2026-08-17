# WAFD ONE 10.0.0 RC189

- Fixed undertaking PDF 417 / ContentNotFoundError caused by broken image links.
- Embeds local logo, signature and stamp images into PDF HTML before wkhtmltopdf rendering.
- Missing optional images no longer abort the entire PDF.
- Re-applies saved/default signature and stamp to legacy undertakings and clears stale compiled undertaking templates.
- Keeps Preview and issued PDF on the same rendering path.
- Polished the global mobile Back button into the top navigation instead of a floating bottom control.
- Preserved direct Preview, Issue PDF, Share PDF and Save PDF actions.
