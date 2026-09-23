# L9 — USER-SUPPLIED REPORT INGESTION (DE-HARDCODE LOOP)
### Master prompt for Antigravity · SIH 2026 · PS-26117 · Sovereign On-Premise Agentic AI Workbench

---

## HOW TO USE
Paste **Section A** once (governor). Then paste **Section B** as the task. Do not paste anything else until Antigravity reports `L9 CLOSED`.

---

## SECTION A — LOOP GOVERNOR (paste first)

```
You are the sole engineer on the Sovereign On-Premise Agentic AI Workbench (SIH 2026, PS-26117, MRPL/ONGC).
This is a hackathon semi-final build. It will be examined by domain judges who will try to break it.
A defect you did not find is a defect they will find. Small mistakes are not acceptable.

OPERATING CONTRACT — applies to every task in this session, without reminder.

HARD INVARIANTS (breaking one = the loop FAILED, no matter how good the code looks):
  I1. ZERO EGRESS. No cloud SDK, no runtime pip install, no remote font, no CDN. Everything is 127.0.0.1 or local disk.
  I2. ZERO FABRICATION. If a tool cannot run, raise loudly. Never substitute a hard-coded "correct" value to make a demo pass.
  I3. EXECUTION IS TRUTH. Nothing is done because you wrote it. It is done when you ran it and pasted the real stdout.
  I4. NO REGRESSION. `python3 scripts/full_verify.py` must still PASS D1-D5 after every single loop.
  I5. NO SCOPE ESCAPE. You may not close a loop by narrowing the DONE-TEST, marking an item "future work",
      declaring it "out of scope", or claiming the environment prevents it. If blocked, name the exact blocker
      and the exact line of code causing it.

LOOP PROTOCOL — per task:
  STEP 1 READ    List every file you will touch and why. Quote the exact current lines you intend to delete. No code yet.
  STEP 2 PLAN    Smallest change satisfying the DONE-TEST. State explicitly what you are NOT doing.
  STEP 3 BUILD   Implement.
  STEP 4 RUN     Execute the DONE-TEST commands. Paste raw terminal output verbatim. No summarising, no paraphrasing.
  STEP 5 JUDGE   Compare output to the DONE-TEST criterion by criterion. Write PASS or FAIL per criterion.
                 You may NOT write PASS on partial output. You may NOT write PASS on output you did not paste.
  STEP 6 ITERATE If any criterion is FAIL: state root cause in one sentence, return to STEP 2.
                 Continue until every criterion is PASS. Do not stop, do not ask me whether to continue,
                 do not hand back a partially working state. If you hit 8 iterations on the same criterion,
                 stop and report the precise blocker honestly — but only after 8 real attempts.
  STEP 7 ADVERSARY Before declaring the task closed, attack your own work. Try to make it produce a wrong
                 answer. List every attack you tried and its result.
  STEP 8 RECORD  Append outcome to STATE.md. Append every bug found plus its fix to ISSUES.md, status CLOSED.
                 Zero OPEN items permitted.

Acknowledge in one line. Then wait.
```

---

## SECTION B — THE TASK (paste second)

```
TASK L9: Make the workbench accept ANY report file the user supplies, and make every downstream number
derive from THAT file. Right now the three demo flows are hard-coded fixtures wearing a costume.

=== PART 1: FIND AND DELETE THE FIXTURES (do this first, before building anything) ===

These are the known hard-coded points. Delete or replace every one. Then hunt for the ones I have not listed.

  H-01  agent/tools/vision_ocr.py, in extract_inspection_findings():
        The block guarded by `if "Shell Course 3" in raw_text or "CRITICAL" in raw_text.upper():`
        assigns t_prev = 14.6, t_meas = 13.1, t_req = 12.4, dt_years = 3.5 as PYTHON LITERALS.
        These are never read from the image. The corrosion rate 0.429 and remaining life 1.63 that
        the whole demo rests on are therefore computed from constants, not from OCR.
        This is the single most damaging defect in the project. A judge who uploads a different
        inspection sheet gets 0.429 mm/yr back regardless of what the sheet says.
        REPLACE with: real numeric extraction of previous thickness, measured thickness, design minimum,
        and the interval between inspections, parsed from the OCR text of the supplied file.

  H-02  agent/tools/vision_ocr.py: `if "STABILIZER" in raw_text.upper():` forces equipment_tag = "C-101"
        and equipment_name = "Naphtha Stabilizer Column". Delete. Parse the tag from the document.

  H-03  agent/tools/vision_ocr.py: the regexes assume one exact label vocabulary
        (EQUIPMENT:, UNIT:, DATE:, LEAD INSPECTOR:, NDT:). A real refinery sheet may say
        "Equipment Tag No.", "Asset ID", "Plant", "Inspected By", "Method". Build a label-synonym
        map and a table-aware fallback so a differently formatted sheet still parses.

  H-04  agent/loop.py, multimodal branch: when attached_files is empty it silently falls back to
        data/sample_docs/inspection_reports/CDU_V101_Inspection_Turnaround_Report.png.
        A demo that quietly analyses a file the judge did not upload is worse than a demo that errors.
        DELETE the fallback. No file = explicit error.

  H-05  agent/loop.py, coding branch: coder_prompt hard-codes the string
        'data/sample_docs/engineering_logs/E104_Heat_Exchanger_Operating_Log.csv' into the LLM prompt.
        The user's uploaded CSV is ignored entirely. Inject the actual uploaded path.

  H-06  agent/loop.py, coding branch fallback_script: contains the absolute developer path
        '/home/beldarvishesh/Documents/SIH 2026/...' — this breaks on any other machine, including
        the judging laptop. It also hard-codes column names Shell_Inlet_Press_bar / Shell_Outlet_Press_bar /
        Tube_Inlet_Press_bar / Tube_Outlet_Press_bar AND default values 4.2 / 3.8 / 5.6 / 5.2 via
        row.get(col, default). Those defaults mean a CSV with different headers silently produces
        a plausible fake answer instead of failing. Remove the absolute path. Remove every default.
        A missing column must raise.

  H-07  agent/loop.py: threshold 0.350 bar is a literal. Move to config, and let the uploaded file or
        the SOP knowledge base supply the governing limit where available.

  H-08  agent/tools/doc_gen.py, generate_docx_approval_note(): every field has a fixture default —
        "V-101", "Reflux Drum", "Crude Distillation Unit (CDU-I)", "UTM & MPT", cr=0.429, rl=1.63,
        t_meas=13.1, t_req=12.4, "Shell Course 3 (Liquid-Vapor Interface)", and a fabricated sign-off
        by "Er. R. K. Sharma (Emp ID: 41088)".
        If findings are missing, the document quietly prints the V-101 demo values under the user's
        filename. REMOVE every `or <literal>` default. Missing data must render as
        "NOT FOUND IN SOURCE DOCUMENT" or abort generation — never a borrowed number.

  H-09  agent/tools/doc_gen.py: the string
        ">>> STATUS: APPROVED FOR INTERNAL WELD OVERLAY RESTORATION" and
        ">>> Action: Execute 316L stainless steel cladding prior to unit startup"
        are printed for every document regardless of the findings. The AI is auto-approving an
        industrial repair it did not assess. Replace with a recommendation derived from the actual
        computed remaining life against the actual retrieved clause, and mark it
        "RECOMMENDED — PENDING HUMAN AUTHORISATION".

  H-10  agent/tools/rag.py, search(): when self.documents is empty it returns a hand-written
        API-510 clause dict with score 0.95. That is a fabricated citation presented as a retrieval
        result. Delete it. Empty corpus must return [] and the caller must handle it honestly.

  H-11  scripts/full_verify.py and the console demo buttons assume the two bundled sample files.
        They must be re-pointed at whatever the user uploaded.

  THEN: grep the entire repository for every occurrence of
        0.429  1.63  13.1  12.4  14.6  18.0  3.5  4.2  3.8  5.6  5.2  0.350
        V-101  C-101  E104  E-104  "Reflux Drum"  "Shell Course 3"  "R. K. Sharma"  41088
        "/home/beldarvishesh"
  Every hit outside data/sample_docs/ and outside a clearly-named test fixture is a defect.
  Paste the grep output before and after. The "after" must be empty outside those two locations.

=== PART 2: BUILD REAL INGESTION ===

  B-01  POST /api/upload — accept .pdf, .png, .jpg, .jpeg, .csv, .xlsx, .docx, .txt.
        Sanitise the filename, reject path traversal, cap size, store under data/uploads/<session_id>/,
        return {file_id, server_path, detected_type, size_bytes, sha256}.
        Reject unsupported types with a clear message. Never write outside data/uploads/.

  B-02  agent/tools/file_ingest.py — one entry point: ingest(path) -> normalised document object.
        Dispatch by real content sniffing, not by extension alone:
          native-text PDF   -> pdfplumber text + tables
          scanned PDF       -> pdf2image + Tesseract per page
          image             -> Tesseract, plus the vision model for diagrams
          csv / xlsx        -> structured table with real headers, no assumed schema
          docx / txt        -> text
        Return: {source_path, sha256, detected_type, extraction_path_used, page_count,
                 text, tables[], ocr_confidence, warnings[]}.
        extraction_path_used must be logged so the judge can see WHICH path ran.

  B-03  Field extraction must be schema-driven, not regex-per-label-guess.
        Create config/extraction_schema.yaml declaring each field the system needs
        (equipment_tag, plant_unit, inspection_date, inspector, ndt_method, nominal_thickness,
        previous_thickness, measured_thickness, design_minimum, inspection_interval_years, units),
        each with: synonyms list, value pattern, unit handling, and required/optional.
        Extraction order: (1) direct label match, (2) synonym match, (3) table cell lookup,
        (4) LLM extraction over the OCR text constrained to the schema and validated against it.
        Every extracted field carries {value, unit, confidence, source_span, method_used}.
        A field that cannot be found is null with a warning — it is NEVER defaulted.

  B-04  Unit safety. If the sheet is in inches or mils, convert and record the conversion.
        A silent mm/inch mix-up on a wall thickness is a wrong engineering answer, not a formatting bug.

  B-05  Calculation layer reads ONLY from the extracted field object.
        corrosion_rate = (previous_thickness - measured_thickness) / interval_years
        remaining_life = (measured_thickness - design_minimum) / corrosion_rate
        Guard: interval_years <= 0, corrosion_rate <= 0, missing inputs -> raise with a named reason.
        Emit a Given / Formula / Substitution / Result / Check trace so a human can re-derive it by hand.

  B-06  For CSV/XLSX: detect columns by header semantics, show the user the detected mapping,
        and fail loudly on ambiguity. Never guess a column silently, never default a missing value.

  B-07  Provenance on every deliverable. The generated .docx and .xlsx must state the source filename,
        its SHA-256, the extraction path used, per-field confidence, and any field marked
        NOT FOUND IN SOURCE DOCUMENT. The judge must be able to see exactly where each number came from.

  B-08  UI: replace the three hard-wired demo buttons with an upload control plus a preview panel showing
        the parsed fields and their confidence BEFORE the agent proceeds. Keep the sample files as an
        explicitly labelled "Load demo file" option — clearly marked as a sample, never a silent fallback.

=== DONE-TEST — every criterion must PASS, with pasted real output ===

  T1  Upload a DIFFERENT inspection sheet with different values (make one: tag V-205, previous 20.0 mm,
      measured 16.5 mm, minimum 14.0 mm, interval 4 years).
      Expected corrosion rate 0.875 mm/yr, remaining life 2.86 yrs.
      The system must produce those numbers. If 0.429 / 1.63 appear anywhere, PART 1 is not finished.

  T2  Upload the original V-101 sheet. It must still produce 0.429 / 1.63 — but now DERIVED.
      Prove derivation: paste the source_span for each of the four input thicknesses, showing the
      exact OCR text each number was read from.

  T3  Differential test: run T1 and T2 back to back, diff the two outputs.
      Every engineering figure must differ. Identical figures = fixture still present.

  T4  Upload a sheet using different labels ("Asset ID", "Inspected By", "Method", "Thk (mm)").
      Synonym mapping resolves it. Paste the field-mapping table.

  T5  Upload a CSV with different column names and different row count. The pressure-drop analysis
      must use the real columns. Then upload a CSV missing a required column — it must FAIL LOUDLY
      with the missing column named, and must NOT emit a number.

  T6  Upload a born-digital PDF and a scanned PDF. Both work. extraction_path_used correctly reports
      NATIVE_TEXT and SCANNED_OCR respectively.

  T7  Upload a corrupt / empty / zero-byte file, a 0-page PDF, and a file with a spoofed extension
      (.png that is actually text). Each fails cleanly with a specific message. No crash, no fabrication.

  T8  Upload a sheet with a deliberately missing design minimum. The .docx renders
      "NOT FOUND IN SOURCE DOCUMENT" for that field and does NOT compute remaining life.

  T9  Submit with no file at all. Clean 400. Grep the trajectory: the demo PNG path appears nowhere.

  T10 Run on a clean checkout in a different directory with a different username.
      Zero absolute developer paths. It works.

  T11 grep for the fixture constants listed in PART 1. Empty outside data/sample_docs/ and tests.
      Paste the grep command and its output.

  T12 python3 scripts/full_verify.py — D1-D5 still PASS. Then extend it with D6 "user-supplied file
      drives all outputs" implemented as the T1/T2/T3 differential test, and D7 "missing field is
      never defaulted". Both PASS.

=== EXIT CONDITION ===

You may write "L9 CLOSED" only when all twelve criteria are PASS with pasted evidence, ISSUES.md has
zero OPEN items, and STATE.md records the loop. Until then you keep iterating. Do not ask me for
permission to continue. Do not return a partially working build. Do not soften a DONE-TEST criterion
to reach the exit.

Begin at STEP 1.
```

---

## WHY THIS ORDER MATTERS
Part 1 before Part 2 is deliberate. If you build the upload path while the fixtures are still in place, the system will *appear* to work on uploaded files while still printing 0.429 mm/yr underneath — and you will not notice until a judge uploads their own sheet on stage.
