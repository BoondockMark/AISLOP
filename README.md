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

AISLOP 1.0.0 is complete and packaged as [`aislop-sdr` on PyPI](https://pypi.org/project/aislop-sdr/1.0.0/). The canonical source repository is [BoondockMark/AISLOP on GitHub](https://github.com/BoondockMark/AISLOP). Version 1.0.0 is the only planned release and is unmaintained; see the [maintenance and release policy](MAINTENANCE.md).

The supported matrix is deliberately narrow:

| Runtime | Platforms | Architecture / notes |
| --- | --- | --- |
| CPython 3.12 or 3.13 | Windows 11 | 64-bit |
| CPython 3.12 or 3.13 | macOS 13 or newer | 64-bit Intel or Apple silicon |
| CPython 3.12 or 3.13 | glibc-based Linux, kernel 5.15 or newer | 64-bit |

PyPy, other Python versions, 32-bit systems, mobile platforms, WSL, BSD, and musl-based Linux are unsupported. CI tests both supported Python versions on Windows, macOS, and Linux. AISLOP uses the official MCP Python SDK (`mcp>=1.13.1,<2`); its wheel is platform-independent.

Release history is recorded in the [changelog](CHANGELOG.md), and the protected candidate,
acceptance, publication, and rollback procedure is in the [release checklist](RELEASING.md).

## Set up the server

### 1. Install the published package

Install into a dedicated virtual environment as an unprivileged user:

```sh
python -m pip install aislop-sdr==1.0.0
```

That is the exact release installation command and obtains the `aislop-sdr` distribution from [PyPI](https://pypi.org/project/aislop-sdr/1.0.0/). The installed command remains `aislop`. To work from canonical source instead, clone `https://github.com/BoondockMark/AISLOP.git`; source development uses `uv sync --all-groups`, not the release install above.

### 2. Verify the executable

```console
$ aislop --version
aislop 1.0.0
```

The packaged command's complete help is:

```console
$ aislop --help
usage: aislop [-h] [--version] --allow-root ALLOW_ROOT
              [--transport {stdio,http}] [--host HOST] [--port PORT]
              [--auth-token AUTH_TOKEN]
              [--max-request-bytes MAX_REQUEST_BYTES]
              [--request-timeout REQUEST_TIMEOUT] [--rate-limit RATE_LIMIT]

Run the AISLOP MCP server.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --allow-root ALLOW_ROOT
                        absolute readable workspace root (repeatable)
  --transport {stdio,http}
  --host HOST           HTTP bind host (default: loopback)
  --port PORT           HTTP port (default: 8000)
  --auth-token AUTH_TOKEN
                        HTTP bearer token (or AISLOP_AUTH_TOKEN)
  --max-request-bytes MAX_REQUEST_BYTES
  --request-timeout REQUEST_TIMEOUT
  --rate-limit RATE_LIMIT
                        requests per client per minute
```

At least one absolute, existing `--allow-root` is required; repeat it to grant more roots. CLI values take precedence over built-in defaults. The sole environment variable is `AISLOP_AUTH_TOKEN`, and explicit `--auth-token` takes precedence over it. No configuration files are read. Defaults are stdio, `127.0.0.1:8000`, a 1,048,576-byte HTTP request limit, a 35-second HTTP timeout, and 60 requests per client per minute.

Stdio needs no AISLOP credential. HTTP requires an ASCII bearer token of at least 32 printable, non-whitespace characters. A token authorizes all three tools against every allowed root in that server process: there are no narrower per-tool or per-root scopes and no multi-user identities. Prefer the environment variable because CLI arguments may appear in process listings. OS permissions still apply.

AISLOP supports exactly MCP over local stdio and MCP Streamable HTTP. It does not support legacy HTTP+SSE, WebSocket, or TLS termination. Put a trusted TLS reverse proxy in front of HTTP before traffic crosses a network.

## Connect from an external AI application

The model does not connect directly. An MCP-compatible AI application (the host) starts or contacts AISLOP, discovers its tools, and presents calls for model use. The official interoperability target and test client is the official MCP Python SDK. Host products differ in the name of their top-level server collection; the minimal conventional configurations below contain all AISLOP-specific values.

### Local stdio (recommended)

Create the example root with `mkdir -p /tmp/aislop-workspace`, then add this server to a host on macOS or Linux:

```json
{
  "mcpServers": {
    "aislop": {
      "command": "aislop",
      "args": ["--allow-root", "/tmp/aislop-workspace"]
    }
  }
}
```

On Windows, the equivalent supported-host entry is:

```json
{
  "mcpServers": {
    "aislop": {
      "command": "aislop.exe",
      "args": ["--allow-root", "C:\\Users\\Public\\aislop-workspace"]
    }
  }
}
```

GUI hosts may not inherit the terminal's `PATH`. If so, replace only `command` with the absolute result of `python -c "import shutil; print(shutil.which('aislop'))"`. Standard output is reserved for MCP frames and diagnostics go to standard error.

### Streamable HTTP

Start the server on its default loopback address. The literal token is a tested development value, not a secret to reuse:

```sh
AISLOP_AUTH_TOKEN=aislop-local-demo-token-0123456789abcdef aislop --transport http --allow-root /tmp/aislop-workspace
```

Configure an HTTP-capable host with:

```json
{
  "mcpServers": {
    "aislop": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer aislop-local-demo-token-0123456789abcdef"
      }
    }
  }
}
```

Keep a real token in the host's secret or environment facility rather than committing it. The MCP endpoint is `/mcp`. Both unauthenticated readiness endpoints (`/health` and `/healthz`) disclose only `{"status":"ok"}`. Verify one with:

```sh
curl --fail --silent http://127.0.0.1:8000/healthz
```

Restart or reload the host after saving either transport. Confirm that `aislop` is connected and advertises exactly the three tools below. If discovery fails, run `aislop --help`, then check the executable path, absolute allowed roots, working directory, token/header, endpoint, and OS permissions.

### Upgrade and uninstall

There is no automatic updater. Review the canonical release, upgrade with an explicit version, and verify it:

```sh
python -m pip install --upgrade aislop-sdr==1.0.0
aislop --version
```

Version 1.0.0 is the only planned release, so this currently reinstalls or confirms it. To uninstall, stop the server, remove its host entry, and run:

```sh
python -m pip uninstall --yes aislop-sdr
```

Uninstallation does not edit host settings, virtual environments, logs, shell history, or data retained by the host. AISLOP creates no persistent configuration or index.

## Use AISLOP through the AI

Version 1.0 exposes three read-only tools: `inspect_path` reads bounded metadata, content, or directory entries; `scan_text` performs a bounded literal or RE2-compatible regex search; and `observe_changes` polls metadata changes using a process-local cursor. It exposes no MCP resources, resource templates, or prompts. Complete schemas, limits, and errors are in the [specification](docs/specification.md).

Create deterministic example data:

```sh
mkdir -p /tmp/aislop-workspace
printf 'hello protocol\n' > /tmp/aislop-workspace/sample.txt
```

Successful discovery from the packaged artifact returns these real tool names and required schema fields (optional fields are omitted here only for readability):

```json
{
  "tools": [
    {"name": "inspect_path", "inputSchema": {"required": ["path"]}},
    {"name": "scan_text", "inputSchema": {"required": ["path", "query"]}},
    {"name": "observe_changes", "inputSchema": {"required": ["path"]}}
  ],
  "resources": [],
  "resourceTemplates": [],
  "prompts": []
}
```

A valid real `tools/call` request using the documented `scan_text` schema is:

```json
{
  "name": "scan_text",
  "arguments": {
    "path": "/tmp/aislop-workspace",
    "query": "protocol",
    "mode": "literal",
    "case_sensitive": true,
    "glob": "**/*",
    "max_results": 100
  }
}
```

It succeeds with:

```json
{
  "matches": [
    {
      "path": "/tmp/aislop-workspace/sample.txt",
      "line": 1,
      "column": 7,
      "text": "hello protocol",
      "text_truncated": false
    }
  ],
  "files_scanned": 1,
  "truncated": false
}
```

In an AI host, the same request can be natural language:

```text
Use scan_text to find the case-sensitive literal "protocol" under
/tmp/aislop-workspace. Return at most 100 matches.
```

Review the selected tool and arguments; the host may offer per-call approval, although AISLOP does not require it. All operations are read-only, but returned data leaves the server and may go to the host's model provider. Grant the smallest possible roots, start with non-sensitive data, and independently check results.

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
