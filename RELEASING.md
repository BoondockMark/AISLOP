# Release checklist

> **Current policy:** 1.0.0 is the sole planned release and is unmaintained.
> This checklist is retained only to prevent an accidental future publication
> from misrepresenting the packaged RF application.

The distribution version has one source,
`src/aislop/__init__.py::__version__`; `rf_mcp` re-exports it and both console
scripts and wheel metadata must match. Tags are immutable `v<SemVer>` tags.
The RF API contract version (`1.0`) is separately defined in
`src/rf_mcp/api_contract.py`; changing either value requires an explicit
compatibility and documentation decision.

## Candidate preparation

- [ ] Obtain repository-owner approval to depart from the no-future-release
  policy and update `MAINTENANCE.md`, `SECURITY.md`, and the changelog first.
- [ ] Freeze `get_rf_api_contract`, generated MCP discovery, dashboard/JSON/live
  routes, persistence schema/migrations, receiver adapters, subprocess decoder
  capabilities, environment variables, and supported OS/Python matrix.
- [ ] Apply Semantic Versioning: patch for fixes without intentional stable-core
  changes; minor for additive tools/optional fields/enum values; major for
  removals, renames, new requirements, or other incompatible v1 changes. Give at
  least one minor release of deprecation notice before a next-major removal.
- [ ] Update the authoritative package version, API version if applicable,
  README install/host/verification instructions, specification, threat model,
  policies, and dated changelog. Use the registry's PEP 440 spelling for a
  prerelease artifact.
- [ ] Review every Python lock diff and every expected external program
  (`airspyhf_*`, `rtl_*`, ffmpeg, WSJT-X decoders, Fldigi/playback, SSTV), native
  driver assumption, network destination, and license. External tools are not
  pinned by the wheel, so record acceptance versions as release evidence.
- [ ] Verify migrations and recovery using a copy of a prior
  `RF_MCP_DATA_DIR`; never run candidate tests against irreplaceable station
  data. Test backup/restore of SQLite database/WAL and artifacts together.

## Automated gates

- [ ] From a clean checkout run `uv sync --all-groups` and `uv run pytest` on
  CPython 3.12 and 3.13 and every advertised OS.
- [ ] Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`,
  `uv run python scripts/validate_dependencies.py`, `uv pip check`, and
  `uv run pip-audit -r requirements.lock`.
- [ ] Run the secret scan and manually review auth/session, webhook, subprocess,
  receiver, storage/delete, dashboard/download, live-stream, and non-loopback
  negative cases against `docs/security.md`.
- [ ] Build from the clean tree with `uv build`; run Twine metadata validation,
  `scripts/validate_release_artifacts.py`, and `scripts/validate_version.py`.
  Confirm both console scripts, all RF modules, and packaged dashboard assets
  are present.

## Installed-artifact acceptance

For every supported OS/Python pair, install the exact wheel into a new virtual
environment from outside the checkout and run `tests/installed_wheel_e2e.py`.
Also execute the README's deterministic post-install sequence. Evidence must
show all of the following without physical SDR hardware:

- [ ] `rf-mcp --version` equals wheel/tag version;
- [ ] `/healthz` reports ready, correct version, and auth state;
- [ ] authenticated dashboard HTML/CSS/JavaScript assets are delivered and
  unauthenticated access is rejected when a token is configured;
- [ ] MCP initializes at `/mcp`, discovery includes the stable v1 core, and the
  API contract is correct;
- [ ] explicit fake-backend `list_devices` and `inspect_spectrum` calls return
  the deterministic non-hardware observation; and
- [ ] the job, result, plots, artifact metadata, and `SDR-MCP.sqlite3` persist in
  the isolated data root and recovery works after restart.

Separately perform owner-supervised hardware acceptance for each advertised
Airspy HF+ and RTL-SDR adapter, and capability/timeout/failure checks for each
advertised decoder. Hardware absence must remain an actionable capability error,
not silently switch to fake data.

## Publication and rollback

- [ ] Merge through protected `main`, tag the exact reviewed commit once, and
  require all CI/release-environment approvals.
- [ ] In the PyPI pending publisher, configure owner `BoondockMark`, repository
  `AISLOP`, workflow `release.yml`, and environment `release` exactly. Creating
  the `v1.0.0` tag runs the trusted-publishing job; its first successful upload
  creates the PyPI project and converts the pending publisher into a normal
  project publisher. Do not create the project manually under another account.
- [ ] Confirm the clean workflow emits matching sdist/wheel, SHA-256 checksums,
  CycloneDX SBOM, provenance attestations, registry version, GitHub release, and
  release notes. The GitHub release is published independently so its verified
  artifacts remain available if the registry job fails. Publish to PyPI via
  trusted publishing, never a stored PyPI token.
- [ ] Reinstall the registry artifact and repeat deterministic acceptance. Do
  not call a release supported unless `SECURITY.md` explicitly says so.

If compromised or broken, stop publication/deployment and revoke permissions,
tokens, sessions, and webhook secrets. Never move/reuse a tag or overwrite a
registry file. Yank/withdraw the artifact, preserve forensic catalog/artifact
copies, publish an advisory/changelog correction, and—only if maintenance policy
has been changed—fix forward under a new SemVer version through every gate.
