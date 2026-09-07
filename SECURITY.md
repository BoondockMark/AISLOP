# Security policy

## Supported versions

| Version | Security fixes |
| --- | --- |
| Latest 1.x release | Yes |
| Older releases and unreleased source snapshots | No |

Upgrade to the latest release before reporting a defect. Security fixes may be
released without preserving insecure behavior.

## Reporting a vulnerability

Do **not** open a public issue. Use GitHub's **Security** tab and select
**Report a vulnerability** to submit a private advisory. Include the affected
version, configuration and transport, impact, reproduction steps, and any
suggested mitigation. Do not include real credentials or private workspace data.

Maintainers aim to acknowledge a report within 3 business days, provide an
initial assessment within 10 business days, and coordinate disclosure after a
fix is available. If the Security tab is unavailable, contact the repository
owner privately through the contact method on their GitHub profile. Please allow
90 days before disclosure, unless a shorter timeline is mutually agreed or
active exploitation requires an accelerated response.

The threat model, deployment requirements, and release security gate are in
[`docs/security.md`](docs/security.md).
