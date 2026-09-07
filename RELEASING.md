# Release checklist

AISLOP uses Semantic Versioning. `src/aislop/__init__.py::__version__` is the single
authoritative version source; Hatch reads it into package metadata and the CLI imports it for
`aislop --version`. Release tags are exactly `v<version>`. Python registries normalize a SemVer
candidate such as `0.1.0-rc.1` to its equivalent PEP 440 spelling, `0.1.0rc1`; the release
validator checks that deterministic translation and the clean install must use the registry's
spelling.

## One-time hosting setup

- Set the canonical `origin` to `https://github.com/BoondockMark/AISLOP.git`.
- Protect `main`: require a pull request, the complete CI matrix and `quality` checks, no force
  pushes or deletion, resolved conversations, and administrator enforcement.
- Create protected GitHub environments named `prerelease` and `release`. Require an owner review
  for `release`, restrict it to tags matching `v[0-9]*`, and configure PyPI trusted publishing for
  this repository/workflow/environment. The prerelease environment must target a non-production
  registry (normally TestPyPI) and define the `repository-url` used by the publish step when that
  registry is selected.
- Enable immutable releases/tags and artifact attestations where the hosting plan supports them.

## Candidate (`0.1.0-rc.1` example)

- [ ] Freeze and approve `docs/specification.md`; record any intentional delta in `CHANGELOG.md`.
- [ ] Set `__version__` to `0.1.0-rc.1`, update the changelog, and merge through protected `main`.
- [ ] Run the complete test, formatting, lint, type, locked-dependency, vulnerability, secret,
  metadata, licensing, and version gates locally and in CI.
- [ ] Complete the threat-model and dependency/security review; resolve or explicitly accept every
  finding before approval.
- [ ] Verify README install/upgrade examples, CLI help, specification, security policy, maintenance
  policy, licenses, and changelog against the candidate.
- [ ] Produce a clean clone with no ignored/untracked inputs and tag that exact commit
  `v0.1.0-rc.1`; push the tag. Never reuse or move a release tag.
- [ ] Confirm the release workflow creates the sdist and universal wheel, SHA-256 checksums,
  CycloneDX SBOM, GitHub provenance attestations, prerelease registry publication, and a matching
  GitHub prerelease.
- [ ] In a clean supported OS/Python environment, install the exact registry artifact by version
  (not the workspace), verify `aislop --version`, complete MCP initialization/tool discovery, and
  successfully call `inspect_path` and `scan_text`. Save the workflow and test evidence.

## Stable acceptance

- [ ] Obtain release-owner acceptance of all candidate criteria on every supported OS/Python pair.
- [ ] Set the stable SemVer, remove the prerelease suffix, finalize the dated changelog, repeat all
  gates from a clean checkout, and approve the protected `release` environment.
- [ ] Confirm registry metadata, Git tag, GitHub release title/notes, artifact versions, checksums,
  SBOM, and provenance all name the identical stable version.
- [ ] Reinstall the exact stable registry artifact in a new clean environment and repeat MCP
  initialization, discovery, and representative calls.

## Rollback

- [ ] Stop the environment deployment and revoke publishing credentials/permissions if compromise
  is suspected. Do not delete, move, or overwrite tags or registry files.
- [ ] Mark the GitHub/registry release as withdrawn or yanked, document impact in the changelog and
  security advisory, and direct users to the last accepted version.
- [ ] Fix forward with a new SemVer patch (or a new prerelease identifier), rerun every gate and
  clean-install acceptance check, then publish through the same protected process.
