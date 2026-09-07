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

I also have **no plans to maintain AISLOP after its initial release**. The first
release is therefore also the long-term-support release, the sunset release,
and—unless an AI takes pity on it—the final release.

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

**There is no installable software in this repository yet.** The repository
currently contains this README and no executable, package manifest, MCP server,
or published release. Consequently, nobody can honestly install, connect to, or
use AISLOP today.

This limitation is documented rather than disguised behind a plausible-looking
command that installs an unrelated package from the internet. Once Codex
produces an initial release, this section will be updated with the real package
name, executable, transport, and configuration—assuming that happens before
maintenance ends.

## Set up the server

> [!IMPORTANT]
> The commands in this section describe the setup contract for a future AISLOP
> release. They are deliberately marked as placeholders because the repository
> does not contain a server executable yet.

### 1. Acquire the source-shaped placeholder

```sh
git clone <repository-url>
cd AISLOP
```

Replace `<repository-url>` with the clone URL for this repository. That installs
nothing, but it does provide a local copy of the disclaimer, which is currently
the complete AISLOP experience.

### 2. Prepare for the version 1.0 server

The approved [version 1.0 specification](docs/specification.md) defines a local
`aislop` executable running on CPython 3.12 or 3.13 over **stdio only**. Windows
11, macOS 13+, and glibc-based Linux with kernel 5.15+ are supported. No package
is published yet, so there is still no valid installation command; do not guess
a package name. A tagged release must supply and document the package before
this setup can be completed.

AISLOP 1.0 needs no application credentials. Run it as an unprivileged user and
grant that account only the filesystem access required for the configured roots.

### 3. Verify the server before connecting an AI

Once a package is released, confirm that the executable is the intended version:

```sh
aislop --version
```

Do not expect normal output when the server is launched by a host: stdout carries
MCP messages and diagnostics go to stderr.

## Connect from an external AI application

Version 1.0 uses local stdio. The implementation is not yet published, so the
configuration below documents the approved contract rather than a currently
runnable server.

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

AISLOP requires one or more `--allow-root` arguments and no credentials. It can
only read targets that resolve beneath those roots. Streamable HTTP, remote
deployment, and authentication are explicitly deferred beyond version 1.0.

### Confirm the connection

After restarting the host:

1. open its MCP/server panel and confirm that `aislop` is connected;
2. inspect the tools reported by the server rather than assuming their names;
3. review the host and server logs if discovery fails; and
4. verify the executable path, allowed-root arguments, working directory, and OS
   filesystem permissions before retrying.

Until the initial release supplies real values, do not paste the placeholder
configurations above into an MCP client and expect them to work.

## Use AISLOP through the AI

The implementation is pending, but the version 1.0 interface is fixed. It exposes
three read-only tools:

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

Issues may be opened for archival purposes. Pull requests may be admired from a
respectful distance. For troubleshooting, paste the error into the next
available language model and continue the proud AISLOP tradition.

## License

No license has been selected yet. This is not legal advice; it is barely a
README.
