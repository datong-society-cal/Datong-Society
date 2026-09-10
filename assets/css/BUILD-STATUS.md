# CSS build status — Datong-Society

**`assets/css/main.css` is the source of truth. It is maintained directly by hand;
it is NOT generated from `assets/sass/`.**

Verified 2026-09-09. Evidence:

1. **No build pipeline exists in the project.**
   No `package.json`, `gulpfile`, `Gemfile`, vite/webpack/sass config anywhere in
   the project tree; the `sass` CLI is not installed; the README documents no
   build step.

2. **The Sass tree is the stock HTML5 UP "Dimension" template source**, plus only
   the two-plate `#bg` block (`layout/_bg.scss`, the `.bg-far` plate). It contains
   **none** of the site's custom CSS:

   | marker            | in main.css | in assets/sass |
   |-------------------|------------:|---------------:|
   | `event-card`      |           7 |              0 |
   | `events-filter`   |           4 |              0 |
   | `recruit-modal`   |           4 |              0 |
   | `article-logo`    |          21 |              0 |
   | `cloud-divider`   |           2 |              0 |
   | `member-grid`     |           1 |              0 |
   | `qr-grid`         |           1 |              0 |
   | `lb-overlay`      |           3 |              0 |
   | `Cinzel` fonts    |           3 |              0 |
   | `Noto+Serif+SC`   |           1 |              0 |

3. **The one shared block has already diverged** (main.css was hand-edited after
   the last build): `body.is-article-visible` plate blur is
   `blur(0.1rem)` / `calc(0.1rem + var(--bg-mid) * 0.28rem)` in `main.css`, but
   `blur(0.2rem)` / `calc(0.2rem + var(--bg-mid) * 0.55rem)` in `_bg.scss`.
   `main.css` also swapped the template's Source Sans Pro stack for
   Cinzel / Noto Serif SC (inline `@import` at line ~1783).

**Consequence:** running `sass main.scss` today would output the template
stylesheet with the old two-plate values and would **drop every custom section**
(events, lightbox, recruit modal, persistent logo, dividers, members, QR, fonts),
breaking the site. Rebuilding from Sass is therefore **not** a viable option
unless the entire custom stylesheet is first ported into the Sass tree — a
separate, deliberate migration task.

**Rule of thumb:** edit `assets/css/main.css` directly. If you later decide to
adopt the Sass tree, port all custom sections into it first, then re-verify the
rendered hero against `Temp/after/hero1440.png`.
