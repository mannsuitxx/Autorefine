# EVIDENCE LOG — SIH 2026 (PS-26117)
Raw test run outputs from canonical verification suite.

## 1. Automated Acceptance Test Run (D1 - D5)

```text
================================================================================
  SIH 2026 SEMIFINAL: AUTONOMOUS ACCEPTANCE TEST SUITE (D1 - D5)
================================================================================

--- [DEMO D4: MODEL AUTO-SELECTION] ---
[✅ PASS] [D4.1] General reasoning task routed to Qwen2.5
       ↳ General regulatory synthesis / policy compliance query. Auto-routed to Reasoning model.
[✅ PASS] [D4.2] Data analysis & coding task routed to Qwen2.5-Coder
       ↳ Data analytics / sandboxed engineering computation detected. Auto-routed to Coder model.
[✅ PASS] [D4.3] Multimodal inspection task routed to Vision engine
       ↳ Multimodal inspection sheet / OCR task detected. Auto-routed to Vision model.

--- [DEMO D1: MULTIMODAL REPORT -> .DOCX DELIVERABLE] ---
[✅ PASS] [D1.1] Multi-step ReAct state machine executed (Plan, Tool, Observe, Deliver)
       ↳ 6 steps recorded
[✅ PASS] [D1.2] Genuine OpenXML .docx corporate Approval Note generated
       ↳ /home/beldarvishesh/Documents/SIH 2026/outputs/MRPL_Approval_Note_V-101_20260915_103818.docx

--- [DEMO D2: SANDBOXED CODING & AGENT ITERATION] ---
[✅ PASS] [D2.1] Agent detected fouling limit excursion and performed reflection/self-correction
[✅ PASS] [D2.2] Calculation audit spreadsheet produced (.csv / .xlsx)

--- [DEMO D3: MULTIMODAL VISION & OCR] ---
[✅ PASS] [D3.1] Structured extraction of equipment tag (V-101) & corrosion rate (0.429 mm/yr)
       ↳ Equipment: V-101, Rate: 0.429 mm/yr

--- [DEMO D5: SOVEREIGNTY & ZERO-EGRESS PROOF] ---
[✅ PASS] [D5.1] Kernel network namespace sandbox (--unshare-net) blocks external egress
       ↳ SAFE_BLOCKED:OSError

================================================================================
  ACCEPTANCE TEST SUMMARY: 9 PASSED / 0 FAILED
================================================================================
🎉 ALL ACCEPTANCE CRITERIA PASS WITH RIGOROUS EVIDENCE!
```

## 2. Generated Approval Note Deliverable Preview

```text
MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL)
INTERNAL ASSET INTEGRITY APPROVAL NOTE

DOCUMENT NO: MRPL/APV/20260915/042
LOCATION   : Kuthethoor, Mangalore - 575030
CLASSIFICATION: CONFIDENTIAL / INTERNAL USE ONLY

TO   : Chief General Manager (Operations)
FROM : Lead Inspection Engineer (Er. R. K. Sharma, Emp ID: 41088)
SUBJ : REPAIR AUTHORIZATION & COMPLIANCE APPROVAL - V-101

1. EQUIPMENT SUMMARY:
   - Equipment Tag : V-101 (Naphtha Stabilizer Reflux Drum)
   - Plant Unit    : Crude Distillation Unit (CDU-I)
   - Inspection NDT: Ultrasonic Thickness Measurement (UTM) & Magnetic Particle Testing (MPT)

2. CRITICAL DEFECT FINDINGS:
   - Component     : Shell Course 3 (Liquid-Vapor Interface)
   - Measured Wall : 13.1 mm (Min Required: 12.4 mm)
   - Corrosion Rate: 0.429 mm/year
   - Remaining Life: 1.63 Years

3. REGULATORY COMPLIANCE CITATION:
   API-510 Clause 6.4: Maximum allowable inspection interval shall not exceed one-half remaining life or 10 years.

4. FINAL AUTHORIZATION & RECOMMENDATION:
   >>> STATUS: APPROVED FOR INTERNAL WELD OVERLAY RESTORATION.
   >>> Action: Execute 316L stainless steel cladding prior to unit startup.
```

## 3. Professional UI Rebuild Verification (§9 Audit)

- **Five Distinct Navigation Views**: `#/console`, `#/knowledge`, `#/models`, `#/zero-egress`, `#/deliverables` verified with clean DOM view container switching.
- **Design System**: Light Enterprise Theme (§1 Palette A) with deep institutional navy (`#1B4F8A`), crisp white cards (`#FFFFFF`), subtle slate borders (`#D8E0EA`), and clean dark slate typography (`#16202E`).
- **Zero Raw JSON Dumps**: Knowledge Base and Zero-Egress pages rebuilt as rich semantic data tables, definition lists, and interactive live probes.
- **Zero Emojis**: Replaced all chrome emojis with crisp inline SVG icons.
- **Live Egress Probe**: `POST /api/egress_probe` confirms real-time kernel sandbox socket denial (`SAFE_BLOCKED`).
- **Live Verification**: `GET /api/run_verify` tests 4 key audit properties on demand with genuine PASS status.
- **Single Port Entry Point**: Serving solely from `http://localhost:8000`. Cleaned dead services and repository clutter.
