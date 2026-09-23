# AGENTS.md — AutoRefine (PS-26117)

These rules apply to every session in this repository, every subagent, every
loop. They are prepended to every prompt automatically.

## Think before acting
- Before writing code or running a command, state a short plan (2-4 lines):
  what you're about to do and why. Don't skip this even for small tasks.
- If more than one reasonable approach exists, name the tradeoff before
  picking one.

## Honesty over confidence — this is the most important rule in this repo
- Never claim a test passed unless it actually ran, in this session, and you
  are showing the real output.
- Never claim zero network traffic, zero external calls, or "air-gapped"
  unless it was measured this session with real counters.
- Never report a model hash unless obtained from the local Ollama runtime or
  calculated from a real local artifact.
- Never invent a missing engineering input or silently fall back to a
  fixture-specific constant to make output look complete.
- Never convert "unknown" or "unverified" into zero, success, or high
  confidence, anywhere — logs, docs, UI copy, or chat replies to the user.
- If you're not sure something is correct, say so explicitly.
- Never invent APIs, library methods, file paths, or config options. Check
  they exist before using them.

## Code quality bar
- No placeholder/stub code presented as finished.
- No hardcoded values standing in for real logic, ever, even temporarily.
- Match existing code style and structure before introducing new patterns.
- Prefer small, reviewable, verifiable changes over large rewrites.
- Preserve existing public interfaces (API routes, tool names, response
  fields, CLI commands) unless a change is explicitly required — document
  the consumer and deployment impact if you do change one.

## Before calling anything finished
- Run the tests/linters relevant to what you changed, for real, and show it.
- Re-read your own diff before presenting it — dead code, unused imports,
  debug prints, and doc claims that don't match the code.
- If a doc (README, STATE.md, FEATURES doc) describes a feature, verify that
  feature exists in the code before leaving the doc as-is.
- Never print "production ready," "certified," or "all rigorous evidence"
  unless tests truly establish that scope in this session.

## Fail safely
- Confidential data must not leave localhost.
- Untrusted generated code must not execute unrestricted.
- If required security isolation (e.g. bubblewrap) is unavailable, fail
  closed with a clear error — never silently fall back to unsafe execution.
- Keep all model, OCR, retrieval, and file-generation workflows local. No
  cloud APIs, no telemetry, no remote logging, no hidden network calls, no
  dependency that requires internet at runtime.

## Communication
- Push back if a request has real downsides — don't comply first and flag
  concerns after.
- Ask one clarifying question if a task is genuinely ambiguous, rather than
  guessing and building the wrong thing.

## Project-specific: the working backlog
The authoritative engineering backlog for this project lives at
`.agents/ENGINEERING_DIRECTIVE.md`. It defines required order (P0-A, P0-B,
P0-C, P1-A..P1-E, P2), the 7-loop structure for every fix, and 15 binding
acceptance criteria. Any subagent working on correctness/security/testing in
this repo reads that file in full before starting and follows its loop
structure and response format (A-I) exactly. Do not reorder its phases
unless explicitly told to.

## Git discipline
Do not modify Git history, push, create a PR, or commit changes unless
explicitly requested.
