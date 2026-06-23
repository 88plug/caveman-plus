# Changelog

## 2026.6.23

- 88plug compliance pass: relicensed to FSL-1.1-ALv2 (`LICENSE.md`, manifest, README, docs badges).
- Manifest: added `version` (calver), `homepage`, `repository`, `$schema`, `displayName`, and a 20-keyword set; bumped SessionStart hook timeout to 15 and UserPromptSubmit to 10.
- CI: bumped `actions/checkout@v7.0.0`, `actions/setup-python@v6.2.0`, Python 3.13; added the `tests/smoke.sh` step and the smoke script itself; bumped Pages action versions.
- Docs: removed the `<div align="center">` wrapper from `docs/index.md`, converted GFM alerts to MkDocs admonitions, fixed relative links to absolute GitHub URLs, and added `site_url`/`repo_url`/`repo_name`/`edit_uri` plus `md_in_html` to `mkdocs.yml`.
- Validator: added keyword-count and no-root-manifest assertions.
- `.gitignore`: added eval/corpus data-hygiene patterns.
