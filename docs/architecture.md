# Website architecture and maintainer guide

The production site is static HTML, CSS, JavaScript, and images served by OCF.
Python is a build/check tool only. No Node server, database, CMS, package manager,
or application process is required to operate the website.

## Sources and output

- `content/pages/*.html`: English content fragments, including the historical gallery.
- `content/events.json`: recent and future events, with stable IDs, timezone-aware
  start/end timestamps, bilingual titles/descriptions/locations, and a poster path.
- `content/resources.json`: curated bilingual resource names and HTTPS links.
- `content/site.json`: release date, classification timestamp, and optional analytics.
- `content/zh.json`: shared translations and explicitly identified Chinese blocks.
- `templates/hero.html`, `templates/footer.html`: shared identity and footer.
- `assets/css/main.css`: shared tokens, layout, and components. Historical CSS
  is archived in `docs/archive/`; it is neither imported nor deployed.
- `scripts/build_site.py`: generates seven pages in each language. Edit sources,
  not the fourteen generated root HTML files.

Navigation links point to real HTML pages and work without JavaScript. The small
`main.js` maps bookmarked home hash URLs (`#resources`, `#events`, etc.) to the
new pages. `effects.js` provides optional gallery filtering and an accessible
image viewer. Language switching preserves the equivalent page.

## Add an event

Add a record to `content/events.json`, following the existing example. Use a
stable ID, an ISO timestamp including the UTC offset, and both `en` and `zh`
content. Put an optimized poster in `images/events/<event-id>/`, then add it to
Git before packaging. Poster images are lazy loaded.

The first upcoming event is featured on Home. If none is upcoming, the most
recent event is shown as a recap. Events are classified against `as_of` in
`content/site.json`, not the build machine clock: the same Git commit always
produces the same artifact. Advance `as_of` and `updated` when preparing a release.
This is a static site; status does not change on the server between releases.
Older gallery entries remain in `content/pages/events.html`.

## Add a resource or page

Resources need only `id`, `url`, and bilingual `title`; no client-side JSON fetch
or runtime dependency is introduced. Keep the list curated and check links each term.

A new page needs a fragment, an entry in `PAGES` in `build_site.py` and the
translation mapping, and an explicitly allowed filename in `site_contract.py`.
Deployment-contract changes must be installed with the administrator key before
release, as described in `deployment.md`. Do not broaden the artifact whitelist
to arbitrary HTML, scripts, or server-side files.

## Build, preview, validate

```sh
python scripts/build_site.py
python -m http.server 8766 --bind 127.0.0.1
python scripts/check_site.py
```

`check_site.py` builds, checks content and bilingual navigation, runs deployment
boundary tests, checks JavaScript syntax, and validates the public artifact.
Linux CI additionally runs the receiver integration tests that require rsync.
CSS/JS and QR links receive content-hash query versions automatically.
Generated files are committed so local preview and GitHub diffs stay inspectable.

## Analytics

Analytics is disabled (`provider: "none"`). The build supports opt-in GoatCounter:
set `provider` to `goatcounter` and provide the account's HTTPS `/count` endpoint
after the society has selected a service and created its account. No credentials
belong in these public settings. The hosted integration sends visit information
to GoatCounter. Document the enabled service for visitors and maintainers.

GoatCounter can be self-hosted or used as a hosted service. Umami and Plausible CE
are alternatives, but require a separately maintained analytics application and
database. Keep analytics independent of the static OCF website so analytics
failure does not take down content, navigation, or participation links.

## Release and handover

Use a pull request and review the generated page diffs. Validation must pass
before merging. The existing OCF workflow deploys and verifies hashes, assets,
and the version marker, and retains releases for rollback. Check the deployed
version and representative pages after release. Hand over the GitHub repository,
OCF recovery access, and any separately owned analytics account together.
