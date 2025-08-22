# Changelog

## [Unreleased]

- Ensure Outlinks, Downloads and Site Search are never the first action in a visit.
- Set `urlref` for outlink/download hits to the page that contained the link.
- Convert relative download paths to full URLs using the page's base URL.
- Add debug script `matomo-load-baked/debug_build_requests.py` to print constructed Matomo requests.
- Add `choose_action_pages` helper and unit tests.
