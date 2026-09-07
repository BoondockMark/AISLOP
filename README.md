# AISLOP

**Automated Inspection, Scanning, Listening & Observation Platform**

> Artificially Intelligent Software, Lovingly Orphaned Promptly.

AISLOP is a snarking app built with confidence, autocomplete, and absolutely no
dangerous burden of human comprehension. It is proof that software can look
finished long before anybody understands what it does.

## Full disclosure

I do **not** understand this code. I did **not** write a single line of it.
Every function in AISLOP was produced by ChatGPT's Codex; my role was to ask for
things, accept the results, and maintain an unwavering belief that green checks
are a substitute for knowledge.

I also have **no plans to maintain AISLOP after its initial release**. In policy
terms, that means version 1.0.0 is the only planned release and receives no bug,
compatibility, or security fixes. See the [maintenance and release policy](MAINTENANCE.md)
for the deliberately short lifecycle.

Use this project at your own risk. If it works, Codex deserves the credit. If it
breaks, the repository has achieved its intended state.

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open
protocol that lets an AI application connect to external tools and data through
a standard client/server interface. In less responsible terms: it is a USB-C
port for language models, except every device plugged into it can read your
files and has opinions.

AISLOP is intended to run as an **MCP server**. An MCP-compatible host—such as a
desktop AI application, editor, or agent—acts as the client. The host starts or
contacts AISLOP, discovers the tools AISLOP advertises, and allows the model to
invoke those tools on the user's behalf. This is much more convenient than
giving an unpredictable machine a shell directly, while preserving much of the
same excitement.

## Project status

AISLOP now has a Python package and MCP server implementation. It supports
CPython 3.12 and 3.13 and the official MCP Python SDK 1.13.x. The source checkout
can be installed with `uv sync`; no claim is made that a public package has been
published yet.

## Set up the server

### 1. Acquire the source

```sh
git clone <repository-url>
cd AISLOP
```

Replace `<repository-url>` with the clone URL for this repository.

### 2. Install the version 1.0 server

The [version 1.0 specification](docs/specification.md) defines an `aislop`
executable running on CPython 3.12 or 3.13. Install the checkout into a locked
virtual environment:

```sh
uv sync
uv run aislop --version
```

Stdio needs no credentials; HTTP requires the bearer token described below.
Run AISLOP as an unprivileged user and grant that account only the filesystem
access required for the configured roots.

### 3. Verify the server before connecting an AI

Once a package is released, confirm that the executable is the intended version:

```sh
aislop --version
```

Do not expect normal output when the server is launched by a host: stdout carries
MCP messages and diagnostics go to stderr.

## Connect from an external AI application

Version 1.0 supports local stdio and authenticated Streamable HTTP. Stdio is the
recommended default.

The model does not connect to AISLOP by itself. You configure AISLOP in an
**MCP-compatible host** (an AI desktop app, editor, or agent); that host becomes
the MCP client and exposes the discovered AISLOP tools to the model.

### Local connection over stdio

Use stdio when the AI host and AISLOP run on the same machine. In the host's MCP
settings, add an entry like this after installation and replace the sample root:

```json
{
  "mcpServers": {
    "aislop": {
      "command": "/absolute/path/to/aislop",
      "args": ["--allow-root", "/absolute/path/to/workspace"]
    }
  }
}
```

The top-level key and exact schema vary by host, so consult the host's MCP
documentation. Prefer an absolute executable path: GUI applications often do
not inherit the same `PATH` as a terminal. Restart or reload the host after
saving the configuration.

AISLOP requires one or more `--allow-root` arguments. It can only read targets
that resolve beneath those roots. For HTTP, run `aislop --transport http
--allow-root /absolute/root --auth-token <strong-secret>`, then connect to
`http://127.0.0.1:8000/mcp` with that bearer token. The unauthenticated
`/healthz` endpoint supports health probes.

### Confirm the connection

After restarting the host:

1. open its MCP/server panel and confirm that `aislop` is connected;
2. inspect the tools reported by the server rather than assuming their names;
3. review the host and server logs if discovery fails; and
4. verify the executable path, allowed-root arguments, working directory, and OS
   filesystem permissions before retrying.

If discovery fails, run `aislop --help` and verify the configured command and
arguments from a terminal before reconnecting the MCP client.

## Use AISLOP through the AI

The version 1.0 interface exposes three read-only tools:

- `inspect_path` returns bounded file content, a directory listing, or metadata;
- `scan_text` performs a bounded literal or RE2-compatible regex search; and
- `observe_changes` polls metadata changes since a process-local cursor.

It exposes no MCP resources, resource templates, or prompts. Complete schemas,
limits, errors, permissions, and security boundaries are in the
[specification](docs/specification.md). Once the initial package exists, use it
as follows:

1. install AISLOP from the release's documented source;
2. add its documented server configuration to an MCP-compatible host;
3. restart the host and confirm it discovers exactly the three tools above;
4. make a specific request naming the allowed target and desired result;
5. review the selected tool and its arguments (AISLOP does not require approval,
   although the host may); and
6. verify the result and supervise every action instead of confusing protocol
   support with good judgment.

A future tool call might be requested in natural language like this:

```text
Use inspect_path to read README.md beneath the configured workspace root. Return
a short summary and tell me if the result was truncated.
```

All version 1.0 operations are read-only, but returned file data leaves AISLOP's
process and may be sent by the host to its model provider. Configure the smallest
possible roots, begin with non-sensitive data, and independently check results.

## Best practices in AI SLOP coding

AISLOP aspires to the following standards of machine-assisted craftsmanship:

### 1. Superficial competence

The code should look clean, pass the obvious unit tests, and satisfy the demo.
Architectural consequences are deferred to a future maintainer who, as noted
above, does not exist. This produces the ideal combination of professional
presentation and load-bearing mystery.

Further reading: [What Is AI Slop in Code?](https://dev.to/heavykenny/what-is-ai-slop-in-code-235a)
and [What Is AI Slop? Detect and Prevent Low-Quality AI Code](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code).

### 2. Complexity inflation and over-abstraction

No operation is so simple that it cannot benefit from a wrapper, a manager, a
factory, and an `AbstractThingStrategyProvider`. Extra layers ensure that a
three-line behavior requires twelve files and the quiet acceptance of several
design patterns.

Further reading: [AI Slop in Code](https://www.managed-code.com/blog-post/ai-slop-in-code)
and [What Is AI Slop?](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code).

### 3. Pattern drift and duplication

Why reuse an existing abstraction when we can generate a nearly identical one
with a slightly different name? Duplicate utilities preserve each prompt's
unique artistic vision while turning bug fixes into a repository-wide scavenger
hunt.

Further reading: [What Is AI Slop?](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code)
and [AI Slop in Code](https://www.managed-code.com/blog-post/ai-slop-in-code).

### 4. Hollow testing

Tests should confirm that the implementation is implemented exactly as
implemented. Edge cases, user behavior, and inconvenient reality would only
make the suite less green. A mock of a mock is still confidence if the badge
says “passing.”

Further reading: [What Is AI Slop?](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code).

### 5. Ceremonial and redundant comments

Every self-evident line deserves a comment restating it in English. Comments
explaining *why* a decision was made are discouraged because that would require
someone to know why the decision was made.

Further reading: [AI Slop in Code](https://www.managed-code.com/blog-post/ai-slop-in-code).

### 6. Ghost references and unused imports

Unused imports are not clutter; they are aspirations. References to objects
that do not exist provide a flexible roadmap for features nobody requested.
Redundant declarations, meanwhile, give the code a reassuring sense of volume.

Further reading: [A discussion of AI slop and vibe coding](https://www.reddit.com/r/vibecoding/comments/1ny8v7q/anyone_care_to_explain_ai_slop/)
and [AI Slop: The Future of Software Engineering](https://davidkcaudill.medium.com/ai-slop-the-future-of-software-engineering-0eb0d2570a7a).

## Support

There is none.

Outside contributions are not accepted, so the project does not maintain
contribution or community conduct policies. Issues and pull requests may be
closed without review. For troubleshooting, paste the error into the next
available language model and continue the proud AISLOP tradition. Security
reports are handled as described in the [security policy](SECURITY.md).

## License

AISLOP is available under the [MIT License](LICENSE). Dependency and bundling
information is recorded in [third-party notices](THIRD_PARTY_NOTICES.md).
