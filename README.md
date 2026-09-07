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

### 2. Install a released server

No installation command is published yet. Do **not** guess a package name and
run it through `npm`, `pip`, `uv`, `cargo`, or a curl-to-shell pipeline. Wait for
a tagged release, then follow the release notes and verify that the documented
package and executable actually exist. A usable release must document:

- the installation command and supported runtime version;
- the executable name and its `--help` and `--version` commands;
- required credentials and other environment variables; and
- whether it supports local **stdio**, remote **Streamable HTTP**, or both.

Keep credentials out of this repository. Put them in the host's secret or
environment-variable facility, grant the smallest permissions possible, and do
not include secret values in screenshots, prompts, or bug reports.

### 3. Verify the server before connecting an AI

Run the release's documented health check first. At minimum, confirm that the
executable starts without an AI client and that its version is the one you
intended to install. The concrete command will replace this placeholder after a
server is released:

```sh
<aislop-executable> --version
```

For a stdio server, do not expect normal application output in the terminal:
stdout carries MCP protocol messages. Diagnostic logs must go to stderr. For a
remote server, use the release's documented health endpoint and TLS URL.

## Connect from an external AI application

There is currently no AISLOP server process, URL, or supported MCP transport to
connect to. A real connection guide must specify all of the following:

1. the AISLOP executable or server URL;
2. whether the server uses standard input/output or a network transport;
3. any required arguments and environment variables; and
4. the exact MCP client configuration.

The model does not connect to AISLOP by itself. You configure AISLOP in an
**MCP-compatible host** (an AI desktop app, editor, or agent); that host becomes
the MCP client and exposes the discovered AISLOP tools to the model.

Choose one connection pattern when a release becomes available.

### Local connection over stdio

Use stdio when the AI host and AISLOP run on the same machine. In the host's MCP
settings, add an entry shaped like this and replace every `<...>` value with
values from the AISLOP release notes:

```json
{
  "mcpServers": {
    "aislop": {
      "command": "<absolute-path-to-aislop-executable>",
      "args": ["<documented-server-argument>"],
      "env": {
        "<VARIABLE_FROM_RELEASE_NOTES>": "<load-with-your-hosts-secret-manager>"
      }
    }
  }
}
```

The top-level key and exact schema vary by host, so consult the host's MCP
documentation. Prefer an absolute executable path: GUI applications often do
not inherit the same `PATH` as a terminal. Restart or reload the host after
saving the configuration.

### Remote connection over Streamable HTTP

Use a network transport only if a future AISLOP release explicitly supports
it. Deploy the server behind HTTPS, require authentication, and restrict
inbound access. Then add the documented MCP endpoint to a host that supports
remote servers. A typical *shape* is:

```json
{
  "mcpServers": {
    "aislop": {
      "url": "https://<your-hostname>/<documented-mcp-path>",
      "headers": {
        "Authorization": "Bearer <load-from-a-secret-manager>"
      }
    }
  }
}
```

Do not expose a local stdio process directly to the internet, assume the sample
keys match your chosen host, or use an unencrypted `http://` endpoint outside a
trusted development machine. If the host cannot attach headers safely, use its
documented OAuth or secret-injection mechanism instead of storing a token in a
shared configuration file.

### Confirm the connection

After restarting the host:

1. open its MCP/server panel and confirm that `aislop` is connected;
2. inspect the tools reported by the server rather than assuming their names;
3. review the host and server logs if discovery fails; and
4. verify the executable path, arguments, environment, URL, TLS certificate,
   and authorization settings before retrying.

Until the initial release supplies real values, do not paste the placeholder
configurations above into an MCP client and expect them to work.

## Use AISLOP through the AI

At present, usage consists of reading this README and imagining a successful
tool call. There are no tools to invoke, prompts to run, resources to browse, or
credentials to configure.

When an initial release exists, the expected workflow will be:

1. install AISLOP from the release's documented source;
2. add its documented server configuration to an MCP-compatible host;
3. restart the host and confirm that it discovers AISLOP's advertised tools;
4. ask the AI to list the AISLOP tools it can access;
5. make a specific request, including the target and desired result;
6. review the selected tool, its arguments, and any approval prompt; and
7. verify the result and supervise every action instead of confusing protocol
   support with good judgment.

A future tool call might be requested in natural language like this:

```text
List the AISLOP tools available to you. Do not call one yet. Explain which tool
you would use for <task>, show me the proposed arguments, and wait for approval.
```

After reviewing the proposal, ask the AI to run it. Start with a read-only
operation, use a non-production target, and independently check the result.
Tool availability, names, inputs, and outputs come from server discovery and
the release documentation; the example above intentionally invents none of
them.

Exact commands and examples will be added only after the interface exists. This
is inconvenient, but still more useful than documentation for software Codex
has not hallucinated into being yet.

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
