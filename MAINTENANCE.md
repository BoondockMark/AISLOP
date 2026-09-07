# Maintenance and release policy

## Project lifecycle

AISLOP is unmaintained after its initial release. Concretely:

- version 1.0.0 is the only planned release;
- no released version receives bug, compatibility, dependency, or security fixes;
- known vulnerabilities may remain publicly documented and unfixed; and
- users must evaluate, patch, fork, or replace the software themselves.

The repository owner may change this policy, but users must not rely on future
releases or response times unless a later, committed policy explicitly says so.

## Contributions

Outside contributions are not accepted. Issues and pull requests do not create
an obligation to review, merge, respond, or release. Because the repository is
not an open contribution community, it does not provide separate contribution
or code-of-conduct policies.

## Release authority

Only the repository owner may approve a release by creating its version tag.
Only the repository owner, or an automation identity explicitly authorized by
the owner through the protected `release` environment, may publish artifacts.
Passing CI is required but is not release approval.

Published package ownership remains with the repository owner. It will not be
transferred merely because the project is unmaintained. Any future transfer or
new maintainer must be announced in this repository and through the relevant
package registry; unsolicited requests for package ownership may be declined.
