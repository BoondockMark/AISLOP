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

## Installation

### Today: acquire the source-shaped placeholder

```sh
git clone <repository-url>
cd AISLOP
```

Replace `<repository-url>` with the clone URL for this repository. That installs
nothing, but it does provide a local copy of the disclaimer, which is currently
the complete AISLOP experience.

### Initial release: install the actual software

No installation command is published yet. Do **not** guess a package name and
run it through `npm`, `pip`, `uv`, `cargo`, or a curl-to-shell pipeline. Wait for
a tagged release, then follow the release notes and verify that the documented
package and executable actually exist.

## Connecting an MCP client

There is currently no AISLOP server process, URL, or supported MCP transport to
connect to. A real connection guide must specify all of the following:

1. the AISLOP executable or server URL;
2. whether the server uses standard input/output or a network transport;
3. any required arguments and environment variables; and
4. the exact MCP client configuration.

Until the initial release supplies those details, do not paste a fictional
`aislop` command into your MCP client's configuration. The client will fail to
start it, which is technically predictable behavior but not yet a feature.

## Usage

At present, usage consists of reading this README and imagining a successful
tool call. There are no tools to invoke, prompts to run, resources to browse, or
credentials to configure.

When an initial release exists, the expected workflow will be:

1. install AISLOP from the release's documented source;
2. add its documented server configuration to an MCP-compatible host;
3. restart the host and confirm that it discovers AISLOP's advertised tools;
4. ask the host to invoke a tool and review what the model proposes; and
5. supervise every action instead of confusing protocol support with good
   judgment.

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
