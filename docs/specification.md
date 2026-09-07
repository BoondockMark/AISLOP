# AISLOP product and protocol specification

**Version:** 1.0 (approved interface; implementation pending)
**Protocol:** Model Context Protocol (MCP)
**Transport:** local stdio only

## Product scope

AISLOP 1.0 is a local, read-only workspace-observation server for an
MCP-compatible AI host. It lets a user inspect a file or directory, search text,
and poll for filesystem changes without giving the model a general-purpose
shell. Its initial use cases are:

1. understand the structure and metadata of a local project;
2. read a bounded text file for review or summarization;
3. find literal or regular-expression matches in text files; and
4. observe which paths changed during a user-supervised development session.

AISLOP is not a malware scanner, accessibility service, audio recorder, network
monitor, or autonomous agent. Results are observations, not security findings.

## Protocol conventions

The host starts one AISLOP process and communicates with it using MCP over
standard input/output. Standard output is reserved for protocol frames;
diagnostics go to standard error. Paths may be absolute or relative to the
process working directory. After lexical normalization and symlink resolution,
every target must remain beneath one of the roots configured at startup.

All schemas below use JSON Schema draft 2020-12. Every successful tool result has
one JSON object in an MCP structured-content result and an equivalent JSON text
content block. Invalid arguments use MCP error `-32602`; an unavailable method
uses `-32601`; other tool failures return `isError: true` with this object:

```json
{
  "$id": "aislop.error",
  "type": "object",
  "required": ["code", "message", "retryable"],
  "properties": {
    "code": {"enum": ["OUTSIDE_ROOT", "NOT_FOUND", "NOT_READABLE", "NOT_TEXT", "LIMIT_EXCEEDED", "INVALID_PATTERN", "CURSOR_EXPIRED", "TIMEOUT", "CANCELLED", "IO_ERROR"]},
    "message": {"type": "string"},
    "retryable": {"type": "boolean"},
    "path": {"type": "string"}
  },
  "additionalProperties": false
}
```

Tool calls have a hard 30-second deadline. AISLOP also honors MCP cancellation;
both deadline expiry and cancellation stop traversal promptly and return
`TIMEOUT` or `CANCELLED`. Partial results are never returned on error. File
contents and matches are UTF-8; binary or invalid UTF-8 input returns `NOT_TEXT`.
Directory traversal never follows symlinked directories.

## Version 1.0 tools

Version 1.0 exposes exactly the following three tools.

### `inspect_path`

**Purpose:** Return metadata for a file or directory and, when requested, a
bounded text-file excerpt or a bounded directory listing.

**Input schema:**

```json
{
  "type": "object",
  "required": ["path"],
  "properties": {
    "path": {"type": "string", "minLength": 1},
    "include_content": {"type": "boolean", "default": false},
    "max_bytes": {"type": "integer", "minimum": 1, "maximum": 1048576, "default": 65536},
    "max_entries": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 200}
  },
  "additionalProperties": false
}
```

**Output schema:**

```json
{
  "type": "object",
  "required": ["path", "kind", "size", "modified_at", "truncated"],
  "properties": {
    "path": {"type": "string"},
    "kind": {"enum": ["file", "directory", "symlink", "other"]},
    "size": {"type": "integer", "minimum": 0},
    "modified_at": {"type": "string", "format": "date-time"},
    "content": {"type": "string"},
    "entries": {"type": "array", "items": {"type": "string"}},
    "truncated": {"type": "boolean"}
  },
  "additionalProperties": false
}
```

- **Errors:** `OUTSIDE_ROOT`, `NOT_FOUND`, `NOT_READABLE`, `NOT_TEXT`,
  `LIMIT_EXCEEDED`, `TIMEOUT`, `CANCELLED`, `IO_ERROR`, plus `-32602`.
- **Side effects:** None; filesystem access is read-only.
- **Required permissions:** OS read and directory-search permission for the
  target, and membership in a configured root.
- **Timeout behavior:** The common 30-second deadline applies; reaching
  `max_bytes` or `max_entries` succeeds with `truncated: true`.
- **User approval:** Not required by AISLOP. The host may impose approval.

### `scan_text`

**Purpose:** Search regular files under a file or directory for a literal string
or RE2-compatible regular expression, returning bounded, line-oriented matches.

**Input schema:**

```json
{
  "type": "object",
  "required": ["path", "query"],
  "properties": {
    "path": {"type": "string", "minLength": 1},
    "query": {"type": "string", "minLength": 1, "maxLength": 4096},
    "mode": {"enum": ["literal", "regex"], "default": "literal"},
    "case_sensitive": {"type": "boolean", "default": true},
    "glob": {"type": "string", "default": "**/*"},
    "max_results": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100}
  },
  "additionalProperties": false
}
```

**Output schema:**

```json
{
  "type": "object",
  "required": ["matches", "files_scanned", "truncated"],
  "properties": {
    "matches": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "line", "column", "text"],
        "properties": {
          "path": {"type": "string"},
          "line": {"type": "integer", "minimum": 1},
          "column": {"type": "integer", "minimum": 1},
          "text": {"type": "string"}
        },
        "additionalProperties": false
      }
    },
    "files_scanned": {"type": "integer", "minimum": 0},
    "truncated": {"type": "boolean"}
  },
  "additionalProperties": false
}
```

- **Errors:** `OUTSIDE_ROOT`, `NOT_FOUND`, `NOT_READABLE`, `INVALID_PATTERN`,
  `LIMIT_EXCEEDED`, `TIMEOUT`, `CANCELLED`, `IO_ERROR`, plus `-32602`. Binary
  files are skipped rather than reported as errors.
- **Side effects:** None; filesystem access is read-only.
- **Required permissions:** OS read and directory-search permission for every
  traversed path, and membership of the starting path in a configured root.
- **Timeout behavior:** The common deadline applies; reaching `max_results`
  succeeds with `truncated: true`. At most 10,000 files or 100 MiB are scanned;
  crossing either traversal cap returns `LIMIT_EXCEEDED`.
- **User approval:** Not required by AISLOP. The host may impose approval.

### `observe_changes`

**Purpose:** Compare current file metadata with a process-local snapshot and
return paths created, modified, or deleted since a cursor was issued.

**Input schema:**

```json
{
  "type": "object",
  "required": ["path"],
  "properties": {
    "path": {"type": "string", "minLength": 1},
    "cursor": {"type": "string"},
    "glob": {"type": "string", "default": "**/*"},
    "max_changes": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 200}
  },
  "additionalProperties": false
}
```

Omitting `cursor` establishes a baseline and therefore returns no changes.

**Output schema:**

```json
{
  "type": "object",
  "required": ["cursor", "changes", "truncated"],
  "properties": {
    "cursor": {"type": "string"},
    "changes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "type"],
        "properties": {
          "path": {"type": "string"},
          "type": {"enum": ["created", "modified", "deleted"]}
        },
        "additionalProperties": false
      }
    },
    "truncated": {"type": "boolean"}
  },
  "additionalProperties": false
}
```

- **Errors:** `OUTSIDE_ROOT`, `NOT_FOUND`, `NOT_READABLE`, `CURSOR_EXPIRED`,
  `LIMIT_EXCEEDED`, `TIMEOUT`, `CANCELLED`, `IO_ERROR`, plus `-32602`.
- **Side effects:** Stores an in-memory metadata snapshot and invalidates the
  supplied cursor after a successful comparison. It does not modify files.
- **Required permissions:** OS metadata-read and directory-search permission for
  traversed paths, and membership of the starting path in a configured root.
- **Timeout behavior:** The common deadline applies. At most 10,000 paths are
  observed; crossing that cap returns `LIMIT_EXCEEDED`. Reaching `max_changes`
  succeeds with `truncated: true` and a cursor representing the full new scan.
- **User approval:** Not required by AISLOP. The host may impose approval.

## Resources and prompts

Version 1.0 exposes **no MCP resources, resource templates, or prompts**. File
access is deliberately available only through the bounded tools above. MCP
discovery therefore returns empty resource and prompt lists.

## Platform, deployment, and security

- **Operating systems:** 64-bit Windows 11, macOS 13 or newer, and glibc-based
  Linux distributions with kernel 5.15 or newer.
- **Runtime:** CPython 3.12 or 3.13. Other Python implementations and versions
  are unsupported.
- **Deployment model:** One unprivileged local process per MCP host session,
  installed into a virtual environment and launched by the host. Containers,
  daemons, multi-user services, and remote deployment are unsupported.
- **Configuration:** The executable is `aislop`; repeated
  `--allow-root <absolute-path>` arguments define readable roots. At least one is
  required. No network listener is created.
- **Credentials:** None. AISLOP must not receive API keys, bearer tokens, cloud
  credentials, or elevated OS credentials. It inherits only the launching
  user's filesystem access and a minimal environment supplied by the host.
- **Trust boundaries:** The host and user are trusted to choose roots and review
  model requests. The model, tool arguments, files within roots, filenames, and
  file contents are untrusted. The OS process boundary and root/cap enforcement
  protect files outside configured roots. AISLOP provides no confidentiality
  boundary between the host/model and allowed files: returned content is sent to
  the host and may be forwarded to its model provider.
- **Approval policy:** These read-only tools do not require server-side approval.
  Users should configure host-side per-call approval when allowed roots contain
  private or regulated data.

## Deferred beyond 1.0

The following are explicitly out of scope: Streamable HTTP and every other
network transport; authentication and multi-user authorization; write, delete,
rename, command-execution, and version-control tools; live push notifications
and persistent watchers; persistent indexes or cursor state; MCP resources and
prompts; OCR, image, audio, microphone, camera, and network inspection; malware,
secret, dependency, semantic, or vulnerability scanning; archive traversal;
non-UTF-8 decoding; ignore-file semantics; remote filesystems and cloud storage;
plugins; telemetry; automatic updates; container/server deployment; and support
for mobile OSes, WSL, BSD, Python 3.11 or earlier, or Python 3.14 or later.

