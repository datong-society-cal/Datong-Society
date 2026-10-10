# Architecture review — 2026-10-10

The production site is a small static site. Keep native JavaScript and Python
deployment tooling; a framework, package manager, or server application is not
needed for its present scope.

## Current ownership

- `index.html`: English edition, shared layout and original homepage content.
- `content/zh.json`: Chinese text and stable content-block translations.
- `scripts/build_chinese.py`: shared HTML-aware generator for both Chinese pages.
- `zh.html`: generated, checked-in Chinese edition. Regenerate after editing
  English text or translations; do not maintain it independently.
- `collaboration.html`: English collaboration source; `collaboration-zh.html` is generated.
- `assets/css/main.css`: hand-maintained stylesheet; legacy Sass is reference
  material and must not be compiled over this file.
- `assets/js/main.js`: section routing and focus handling.
- `assets/js/effects.js`: gallery filtering, image dialog, reading progress.
- `assets/js/language.js`: language links preserving the current section hash.
- `scripts/site_contract.py`: deployment file rules, references and budgets.
- `scripts/package_site.py`, `publish_ocf.py`, `ocf_receive.py`: packaging,
  publishing and server-side validation; keep these responsibilities separate.
- `docs/home-redesign.html`: design experiment, excluded from production.

## Recommended simplification order

1. Give both Chinese pages one generation workflow. Move translation content
   into an explicit data file; translate attributes and text deliberately.
   Current exact-text replacement is sensitive to English punctuation changes.
   Avoid replacing text inside comments, scripts or styles.
2. Remove duplicated Chinese paragraphs and repeated bilingual labels in the
   Chinese contact/collaboration sections. Retain concise English accents.
3. Group stylesheet sections and consolidate overrides. Remove unused
   `home-hero`, `home-emblem`, `home-intro`, `home-qr-valid` rules and superseded
   footer rules after checking both editions, mobile and article views.
4. Store repeated event date/location and contact information in one small data
   source if updates become frequent. Avoid a new build system solely for this.
5. Move legacy Sass to a clearly labeled reference/archive directory and remove
   hidden placeholder member content from public HTML after preserving it in
   documentation. Neither belongs in the active editing workflow.
6. Keep experimental previews and original QR uploads outside published assets.
   The current Chinese-named QR source duplicates `qr-activity-group.jpg` and is
   untracked; it was preserved, not deleted.

## Verification

`scripts/tests/test_language.py` checks both language selectors, homepage
generation consistency and contact wording. Existing deployment tests cover
archive safety and the artifact contract. Linux rsync integration tests run in
GitHub Actions, not on this Windows host.

## Implemented cleanup

Both Chinese pages now share generation and content data. Explicit blocks remove
duplicated contact and collaboration copy. The HTML parser skips code and comments,
translates accessible attributes, and keeps filter categories unchanged. Unused
home/footer rules and unreachable routing code were removed. Legacy Sass and
placeholder members were archived. Language storage without a reader was removed.

Event facts remain in English source HTML for now; adding a second template layer
solely for one featured event would increase maintenance. If recurring event
updates grow, introduce a small event data file with a dedicated generation check.
