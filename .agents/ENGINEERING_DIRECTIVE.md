# AutoRefine Engineering Directive — PS-26117

You are a principal software engineer, security engineer, and testing engineer working on the SIH 2026 semifinal project:

Project: AutoRefine
Repository: mannsuitxx/Autorefine
Problem statement:
"Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work"

Your objective is to make the existing repository technically trustworthy, reproducible, and judge-ready. Do not redesign the entire application or add superficial features. Improve the existing implementation through small, verifiable engineering loops.

==================================================
ENGINEERING RULES — MUST FOLLOW
==================================================

1. Inspect before editing.
   - Read the relevant source files, tests, configuration, README, launch scripts, and dependency files.
   - Do not modify code that you have not read.
   - Search the entire repository for related implementations before creating a new one.

2. Work in small loops:
   LOOP 1: inspect and identify the exact issue
   LOOP 2: write characterization or regression tests
   LOOP 3: implement the smallest safe fix
   LOOP 4: run targeted tests
   LOOP 5: run broader verification
   LOOP 6: inspect the diff and update documentation
   LOOP 7: report evidence, remaining risks, and failed checks

3. Preserve existing public interfaces wherever possible.
   - Do not rename API routes, tool names, response fields, or CLI commands unless necessary.
   - If a behavior changes, document its consumer and deployment impact.
   - Prefer adapters and seams over large rewrites.

4. Do not fabricate evidence.
   - Never claim a test passed unless it actually ran.
   - Never claim zero network traffic unless it was measured.
   - Never report a model hash unless it was obtained from the local model runtime or calculated from a real local artifact.
   - Never use sample-specific constants to make a test pass.
   - Never convert "unknown" or "unverified" into zero, success, or high confidence.

5. Fail safely.
   - Confidential data must not leave localhost.
   - Untrusted generated code must not execute unrestricted.
   - If required security isolation is unavailable, fail closed with a clear error.
   - Do not silently fall back to unsafe execution.

6. Keep all model, OCR, retrieval, and file-generation workflows local.
   - Do not introduce cloud APIs.
   - Do not add telemetry, analytics, remote logging, external downloads, or hidden network calls.
   - Do not add dependencies that require internet access at runtime.

7. Do not modify Git history, push, create a PR, or commit changes unless explicitly requested.

==================================================
CURRENT HIGH-PRIORITY FINDINGS
==================================================

Fix these issues in this order:

P0-A — Engineering values must never be silently changed
File to inspect:
- agent/tools/field_extractor.py

Known risk:
The fallback parser contains sample-specific substitutions and unsafe defaults similar to:
- nominal_thickness_mm = 18.0
- design_minimum_mm = t_min or 12.4
- previous_thickness_mm = 14.6 when a source value falls within a range
- measured_thickness_mm = 13.1 when a source value falls within a range
- default inspection interval = 3.5 years
- dividing thickness values above 50 by 10 without preserving uncertainty

Required behavior:
- Preserve the exact raw value extracted from the source.
- Store raw value, normalized value, unit, confidence, extraction method, and source span separately.
- Never replace an extracted source value with a fixture-specific value.
- Never invent a missing engineering input.
- If a decimal or OCR correction is suspected, preserve the original value and mark:
  correction_status = "NEEDS_REVIEW"
  correction_reason = ...
- Do not perform a calculation when required inputs are missing or ambiguous.
- Return a structured abstention or review-required result.
- Preserve backward-compatible response fields where possible.

Required regression tests:
- Use unseen values different from V-101 and V-205.
- Verify that source values are not rewritten.
- Verify that missing design minimum, previous thickness, measured thickness, and interval do not receive fabricated defaults.
- Verify that malformed or ambiguous OCR values require review.
- Verify source spans correspond to the actual source text.
- Test values above 50 to ensure the normalization heuristic does not silently mutate them.

P0-B — Air-gap attestation must use measured evidence
Files to inspect:
- security/attest.py
- security/egress_denylist.py
- security/ledger.py
- security/verify_ledger.py
- backend/main.py
- scripts/full_verify.py

Known risk:
The attestation currently contains hardcoded claims such as zero WAN bytes, zero external requests, fixed provider statuses, and fixed model hashes. Signing a report does not make hardcoded measurements true.

Required behavior:
- Establish a baseline network measurement before the task.
- Establish a final network measurement after the task.
- Report actual deltas for non-loopback interfaces.
- Distinguish loopback traffic from WAN/non-loopback traffic.
- Record measurement timestamp, interface names, baseline, final counters, and deltas.
- If counters are unavailable, report "UNVERIFIED" and fail the sovereignty acceptance gate.
- Do not report zero merely because measurement failed.
- Inspect the actual local Ollama model inventory.
- Obtain actual model metadata from the local Ollama API where available.
- Calculate hashes only from real local model metadata or local files.
- If an artifact hash cannot be verified, report "UNVERIFIED".
- Keep the Ed25519 signature over the exact measured payload.
- Make signature verification independently testable.
- Ensure the report clearly states the measurement limitations.

Required security tests:
- A successful local task with no non-loopback traffic.
- A deliberate non-local connection attempt.
- A blocked external connection attempt.
- A failed or unavailable counter source.
- Tampering with the signed payload.
- Tampering with the signature.
- A mismatch between measured and reported values.
- Verify that the attestation fails rather than claiming zero when measurement is unavailable.

Important:
Do not treat the Python monkey-patch alone as proof of system-wide zero egress. The application must clearly distinguish:
1. application-level destination blocking,
2. sandbox network isolation,
3. host/interface-level observation,
4. full system air-gap enforcement.

P0-C — Actual model routing must match actual inference
Files to inspect:
- agent/router.py
- agent/tools/llm_client.py
- agent/tools/vision_ocr.py
- agent/loop.py
- model_registry.yaml
- config/
- backend/main.py

Known risk:
The router selects a model, but the vision path directly uses a hardcoded model such as moondream:latest. A routing log alone does not prove that the selected model performed inference.

Required behavior:
- Route every task to a resolved installed local model.
- Pass the resolved model identifier into the actual inference adapter.
- Do not hardcode a model inside the vision path.
- Log:
  task ID,
  role,
  requested model,
  resolved installed model,
  fallback model if used,
  actual responding model,
  inference duration,
  local endpoint,
  failure reason if applicable.
- If the requested and fallback models are unavailable, fail clearly.
- Never silently substitute an unrelated model.
- Ensure both text and vision inference use the same auditable routing contract.

Required tests:
- General document task selects the configured reasoning model.
- Coding task selects the configured coding model.
- Vision task selects the configured vision model.
- Unavailable preferred model uses only the explicitly configured fallback.
- No model is available: task fails clearly.
- Actual response metadata matches the audit event.

P1-A — Harden the code sandbox
Files to inspect:
- agent/tools/sandbox.py
- agent/loop.py
- backend/main.py
- relevant sandbox tests

Required behavior:
- On Linux, require Bubblewrap or another clearly documented OS-level isolation mechanism.
- Fail closed if required isolation is unavailable.
- Do not use Python isolated mode as a security substitute.
- Do not execute untrusted code unrestricted on Windows or other unsupported platforms.
- Add resource controls where supported:
  CPU/time limit,
  memory limit,
  process limit,
  output-size limit,
  temporary filesystem limit,
  subprocess cleanup.
- Sanitize the environment.
- Do not expose host secrets.
- Mount only the required input data.
- Keep network disabled.
- Return a structured result containing:
  success,
  return code,
  stdout,
  stderr,
  timeout status,
  isolation status,
  network isolation status,
  resource-limit status,
  execution duration.
- Make the result clearly say when a guarantee is unavailable.

Required adversarial tests:
- Network socket attempt.
- Reading outside the allowed workspace.
- Environment-variable secret attempt.
- Infinite loop.
- Excessive output.
- Child-process spawning.
- Non-zero exit code.
- Sandbox unavailable.
- Verify no unsafe fallback occurs.

P1-B — Make retrieval claims accurate and useful
Files to inspect:
- agent/tools/rag.py
- kb/hybrid_retriever.py
- kb/graph_builder.py
- data/sample_docs/
- requirements.txt

Known risk:
The code describes dense vector search and cross-encoder reranking, but the inspected implementation uses keyword/rank simulation and heuristic token overlap.

Choose one of these honest approaches:

Option 1 — Implement real local retrieval:
- Add a local embedding model only if it is already supported by the offline deployment plan.
- Build a persistent local index.
- Add deterministic local reranking.
- Ensure model and index assets are packaged locally.

Option 2 — Keep the current lightweight implementation but rename it accurately:
- lexical retrieval,
- local keyword scoring,
- graph expansion,
- heuristic reranking.

Do not advertise simulated components as neural dense retrieval or cross-encoder reranking.

Required retrieval behavior:
- Return source file.
- Return section or page where available.
- Return source span or chunk text.
- Return retrieval mode and scores.
- Return an empty result when no evidence exists.
- Ensure generated answers can distinguish retrieved evidence from model-generated synthesis.
- Add tests for irrelevant queries, missing corpus, duplicate chunks, and citation preservation.

P1-C — Strengthen multimodal confidence and abstention
Files to inspect:
- agent/tools/vision_ocr.py
- agent/tools/field_extractor.py
- agent/tools/file_ingest.py
- agent/tools/pdf_parser.py

Required behavior:
- Do not assign fixed confidence values such as 0.88 or 85% without calibration.
- Report OCR confidence separately from field extraction confidence.
- Report confidence per critical field.
- Preserve the original OCR text.
- Preserve image metadata and preprocessing settings.
- Flag illegible, low-resolution, contradictory, or ambiguous values.
- Require human review before generating an approval note when critical fields are uncertain.
- Ensure scanned PDFs are handled page by page and retain page references where possible.
- Ensure the actual vision model comes from the router.

P1-D — Improve agent traceability
Files to inspect:
- agent/loop.py
- agent/graph.py
- agent/replay.py
- backend/main.py
- agent/tools/audit_logger.py

Required behavior:
- Record a concise task trace:
  task received,
  routing decision,
  plan,
  tool call,
  tool result,
  validation,
  correction/retry,
  human-review gate,
  final deliverable.
- Do not expose private chain-of-thought.
- Store concise action summaries and evidence references instead.
- Add a maximum step count and retry count.
- Add timeouts.
- Make failed tool calls visible.
- Ensure the final output cannot be marked "verified" unless the relevant validation actually passed.
- Preserve deterministic replay for deterministic tools.

P1-E — Correct the acceptance suite
Files to inspect:
- scripts/full_verify.py
- scripts/verify_*.py
- data/test_fixtures/
- EVIDENCE.md
- README.md

Required behavior:
- Do not rely only on known V-101/V-205 fixtures.
- Add generated or independently authored fixtures with new values.
- Test the exact critical files, including field_extractor.py.
- Replace grep-only checks with behavior-based tests.
- Do not print "production ready", "certified", or "all rigorous evidence" unless the tests truly establish that scope.
- Separate:
  core acceptance tests,
  optional differentiator tests,
  environmental tests,
  unavailable-environment tests.
- Every test must explain exactly what it proves.
- Test output should include reproducible commands, environment details, and timestamps.
- Never mask failures.

P2 — Correct deployment and documentation
Files to inspect:
- README.md
- DEMO.md
- EVIDENCE.md
- FEATURES_AND_TECHNOLOGIES.md
- run_workbench.sh
- .env.example
- requirements.txt

Required changes:
- Resolve the port mismatch between README and run_workbench.sh.
- Document Linux prerequisites.
- Document Ollama prerequisites and required model tags.
- Document OCR dependencies.
- Document Bubblewrap requirements.
- Document supported hardware profiles and measured resource requirements.
- Document what is truly offline and what must be preloaded.
- Document fail-closed behavior.
- Remove or qualify claims that are not implemented.
- Add a clean semifinal demonstration runbook.
- Include a limitation section.
- Include a threat model and trust boundaries.
- Include a reproducible acceptance-test command.

==================================================
REQUIRED IMPLEMENTATION ORDER
==================================================

Execute the work in this sequence:

PHASE 0 — Repository audit
- Inspect all target files and dependency configuration.
- Build a dependency map.
- Identify existing tests and public interfaces.
- Do not edit yet.
- Produce a concise implementation plan.

PHASE 1 — Characterization tests
- Add tests that expose:
  source-value mutation,
  fabricated engineering defaults,
  hardcoded attestation values,
  hardcoded model selection in vision,
  unsafe sandbox fallback,
  inaccurate retrieval claims.
- Run the tests and record expected failures.

PHASE 2 — P0 correctness and sovereignty fixes
- Fix field extraction first.
- Fix measured attestation second.
- Fix actual model-resolution propagation third.
- Run targeted tests after every fix.

PHASE 3 — Sandbox and multimodal safety
- Harden sandbox behavior.
- Improve confidence, abstention, and page/source provenance.
- Run adversarial tests.

PHASE 4 — Retrieval and agent trace
- Make retrieval implementation and documentation consistent.
- Improve evidence propagation.
- Add bounded retries, validation gates, and visible execution traces.

PHASE 5 — Full acceptance validation
Run, where supported:
- syntax/import checks,
- unit tests,
- regression tests,
- security tests,
- sandbox tests,
- retrieval tests,
- model-routing tests,
- document-generation tests,
- end-to-end tests,
- full_verify.py,
- lint/type checks if configured.

If a check cannot run because a local service, model, executable, or hardware resource is unavailable:
- do not fake success,
- report the exact prerequisite,
- add a deterministic mock or offline test where appropriate,
- label the runtime check as BLOCKED rather than PASS.

PHASE 6 — Demo readiness
Create or update a deterministic demo path that demonstrates:

Demo A:
Scanned inspection report
→ local OCR/vision
→ evidence extraction
→ local SOP retrieval
→ calculation with visible inputs and formula
→ human review gate if needed
→ source-backed DOCX approval note

Demo B:
Coding request
→ automatic coding-model routing
→ code generation
→ network-disabled sandbox execution
→ test failure or validation result
→ correction/retry
→ verified XLSX/CSV/code deliverable

Demo C:
Sovereignty proof
→ baseline network observation
→ complete local task
→ final network observation
→ actual non-loopback delta
→ visible blocked external probe
→ signed attestation based on measured data

==================================================
ACCEPTANCE CRITERIA
==================================================

The work is complete only when all of the following are true:

1. No production code silently replaces source engineering values with fixture-specific constants.
2. Missing or ambiguous engineering fields trigger review/abstention.
3. Air-gap claims are based on measured data, not hardcoded zero values.
4. Attestation reports are cryptographically verifiable and honest about limitations.
5. The selected model is the model that actually performs inference.
6. Vision inference does not bypass the router.
7. Unsupported sandbox environments fail closed.
8. Sandbox tests prove network isolation and restricted execution behavior.
9. Retrieval claims match the actual implementation.
10. Evidence citations survive from retrieval through the generated deliverable.
11. Agent traces expose actions and outcomes without exposing private chain-of-thought.
12. Tests include unseen inputs and adversarial cases.
13. README, scripts, API port, model configuration, and demo instructions agree.
14. The entire critical demo runs on the target workstation without cloud access.
15. No success, certification, or production-readiness claim is made without executable evidence.

==================================================
FINAL RESPONSE FORMAT
==================================================

After each engineering loop, report:

A. Files inspected
B. Files changed
C. Problem addressed
D. Tests added
E. Commands actually executed
F. Exact test results
G. Remaining failures or blocked checks
H. Security or deployment implications
I. Next smallest safe step

At the end, provide:

- A concise diff summary
- A requirement-to-evidence matrix
- Tests that passed
- Tests that failed
- Tests blocked by environment
- Known limitations
- Exact semifinal demo commands
- Whether the project is DEMO-READY, CONDITIONALLY DEMO-READY, or NOT DEMO-READY

Do not modify unrelated files.
Do not perform cosmetic refactors until correctness and security work is complete.
Do not declare the project a winner or production-ready.
