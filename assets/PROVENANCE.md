# Canonical logo

Translational Sensory & Circadian Neuroscience Unit (MPS/TUM/TUMCREATE)

`tscn-logo.png` is the unmodified canonical asset downloaded from:
https://github.com/tscnlab/Templates/blob/main/logo/logo_with_text-01.png

SHA-256: `ad721549a8fd502f376ead0afa3426265bca46491607bfea3043db5e7dbb6ee3`

The same bytes are used in HTML and PDFs. The build verifies the digest and
downloads from the canonical URL only if the vendored copy is absent. A change
upstream fails verification until a maintainer reviews and updates the digest.
The logo and institutional marks remain subject to their owners' rights.

## Favicon

`favicon.png` is the unmodified 363 × 363 PNG supplied by the user on
25 September 2026. It uses the unit's circular mark for browser tabs.

SHA-256: `655bcfebe4c9844e7ee746e8636cafa2c3f0c63b09aa8fed60589c63bdcd8006`

## Social preview

`social-preview.png` is a 1200 × 630 rendering of
`templates/social-preview.html`, using the unmodified canonical logo, the
heading “Join the unit” and `join.tscnlab.org`. The layout uses the site's
colours and serif heading style. Regenerate it with
`python scripts/render_social_preview.py` after installing the browser QA
dependencies. The rendered PNG is committed so a normal Quarto build does not
need a browser or depend on the build machine's font selection.
