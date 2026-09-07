# Security architecture and release gate

## Scope and assets

AISLOP is a read-only MCP server. Its assets are workspace contents and names,
the HTTP bearer token, observation cursors, tool inputs/results, and service
availability. It does not execute commands, write workspace files, make outbound
network requests, load plugins, provide prompts/resources, or persist telemetry.

Sensitive inputs are `--allow-root`, tool paths, search expressions and globs,
file contents/results, cursor values, MCP request bodies, HTTP metadata, and
`AISLOP_AUTH_TOKEN`/`--auth-token`. Paths and returned content may themselves be
secrets. Treat every tool argument and every file as attacker-controlled.

## Trust boundaries and data flow

1. An MCP host and model cross the protocol boundary into the server. Pydantic
   validates arguments before dispatch; arguments never become shell commands.
2. The server process crosses the OS filesystem boundary. Canonical target
   membership must be beneath an explicitly configured absolute root. Directory
   walks do not follow symlinks. The OS account remains the final permission
   boundary.
3. Streamable HTTP crosses a network boundary. It is off by default, binds to
   loopback by default, and requires a bearer token. TLS and trusted-client
   identity belong at a correctly configured reverse proxy. Forwarded identity
   headers are deliberately not trusted for authentication or rate limiting.
4. Dependency packages cross a software-supply-chain boundary. Only PyPI's
   reviewed `mcp` distribution and its locked transitive graph are permitted;
   install indexes and build runners are trusted release infrastructure.

The server has no outbound networking, so tool arguments cannot trigger SSRF.
It has no subprocess, shell, template execution, or write primitive, so command
injection arguments are data only. Adding any such capability invalidates this
analysis and requires a new review.

## Secure deployment defaults and approvals

- Run stdio unless remote access is necessary. HTTP defaults to `127.0.0.1`, a
  1 MiB body, 35-second request deadline, and 60 authenticated requests per
  source address per minute. Tool operations have a separate 30-second deadline.
- HTTP tokens must be at least 32 printable, non-whitespace ASCII characters.
  Prefer `AISLOP_AUTH_TOKEN`; a CLI token is visible to local process inspection.
  Never put it in source, host configuration committed to source, URLs, or logs.
- Grant only the narrowest read-only roots and run as a dedicated unprivileged OS
  account without write permission, unrelated home-directory access, cloud
  instance credentials, or unnecessary network access. Never allow `/` or a home
  directory merely for convenience.
- The tools are read-only and therefore request no server-side approval. The host
  is expected to show the exact tool name and arguments and obtain user approval
  before each call when its policy requires approval. AISLOP never interprets a
  model assertion as approval. Root expansion, network exposure, or a future
  write/execute/network tool must require explicit administrator configuration
  and interactive host approval.

## Enforced controls and limits

Canonical-path authorization rejects `..`, absolute-path escapes, and symlink
escapes. Walks do not follow directory or file symlinks. Filesystem access is
read-only. TOCTOU changes by another local process remain possible; do not share
writable roots with an untrusted local user when stable observations matter.

Tool paths are limited to 4,096 characters; queries to 4,096; globs to 1,024;
cursors to 128. Inspection returns at most 1 MiB or 1,000 entries. Scans traverse
at most 10,000 paths/100 MiB, skip individual files over 10 MiB, return at most
1,000 matches, and truncate each returned line to 4,096 characters. Observations
snapshot at most 10,000 paths, return at most 1,000 changes, and retain at most
256 opaque, process-local cursors. MCP bodies default to 1 MiB. These ceilings
prevent unconstrained input, output, memory, and traversal work.

HTTP compares bearer values in constant time, ignores proxy identity headers,
rate-limits only authenticated traffic, sends generic authentication errors,
and sets `Cache-Control: no-store` and `X-Content-Type-Options: nosniff` on policy
responses. Health responses disclose only availability. Put an additional body,
connection, and distributed rate limit at the reverse proxy for exposed service.

## Credentials, logging, retention, and redaction

The bearer token flows from environment/CLI to process memory and is compared
only with the Authorization header. It is never returned, persisted, or logged
by AISLOP. Reverse proxies and hosts **must** redact `Authorization`, tokens,
cursors, request/response bodies, file content, search text, and sensitive path
components. Log only event type, status, duration, and a generated correlation
identifier. Disable access-log headers and body capture.

AISLOP persists no data. Results live in the client/host according to that
product's retention policy. Snapshot metadata (paths, sizes, timestamps and
modes) and opaque cursors remain in process memory until consumed, evicted after
256 entries, or process exit. The bearer token remains in memory until exit.
Crash dumps, swap, host transcripts, proxy logs, and OS audit logs are outside
AISLOP and must be protected or disabled as appropriate.

Errors intended for clients use stable codes. Operators must not add raw request
bodies, Authorization headers, file content, or environment dumps to diagnostics.

## Residual threats

An authorized client can read all text beneath an allowed root, infer metadata,
consume bounded resources repeatedly, and exfiltrate what it reads through the
host. Authentication is not authorization between multiple clients. HTTP has no
built-in TLS. A malicious writable workspace can race path checks and reads.
Regex syntax is restricted toward RE2 compatibility, but Python's regex engine
still executes accepted expressions under the tool deadline. Deploy OS sandboxing
and proxy limits when these residual risks are material.

## Dependency provenance and release gate

`requirements.lock` is the committed production lock input. The sole direct
runtime package is `mcp[cli]` from the Python Package Index; its transitive graph
is resolved only from the configured trusted index during controlled lockfile
regeneration. Maintainers must inspect unexpected new maintainers, packages,
native code, install hooks, licenses, and dependency diffs before accepting a
lock update. Git dependencies, direct URLs, editable installs, and unreviewed
indexes are prohibited. GitHub Actions are pinned to reviewed major releases and
publishing uses GitHub/PyPI trusted publishing rather than a stored API token.

Every release is blocked on the CI `test` and `quality` jobs. The quality gate
validates the reviewed production pin, checks the installed graph, audits known
vulnerabilities, scans secrets, type-checks/lints, and validates built metadata.
A maintainer must additionally confirm this threat model still matches the
feature set and record review of the dependency diff in the release pull request.
Any unexplained audit finding, provenance change, secret, failed negative test,
or undocumented capability blocks release; an accepted vulnerability requires a
time-bounded, documented exception approved by a maintainer.
