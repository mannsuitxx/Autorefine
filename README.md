# AutoRefine: Sovereign On-Premise Agentic AI Workbench (MRPL)
### Smart India Hackathon 2026 · Problem Statement PS-26117
**Autonomous, Air-Gapped Integrity Management & Multimodal Engineering Workbench using Open-Weight LLMs**

---

## 🌟 Executive Summary
Refineries handle sensitive operational telemetry, piping schematics (P&IDs), and equipment turnaround reports governed under API-510 and OISD standards. Cloud-dependent AI solutions violate data sovereignty and risk catastrophic exfiltration.

The **AutoRefine Workbench** is a 100% on-premises, air-gapped system that:
1. **Auto-Selects Specialized Models**: Routes tasks dynamically to Qwen2.5 Reasoning, Qwen2.5 Coder, and Moondream Vision based on capability signatures.
2. **Executes Multi-Step ReAct Agency**: Implements an explicit state machine (Plan $\rightarrow$ Tool Call $\rightarrow$ Observe $\rightarrow$ Self-Correct $\rightarrow$ Deliver).
3. **Multimodal Turnaround Analysis**: Runs on-device OCR + API-510 remaining life calculation to generate signed OpenXML `.docx` Approval Notes.
4. **Sandboxed Code Execution**: Executes data analysis inside kernel network namespace sandboxes (`bwrap --unshare-net`) with zero socket egress.
5. **Verifiable Sovereignty**: Proves 0 bytes outbound internet traffic under Linux kernel firewall lockdown.

---

## 🚀 One-Command Launch

```bash
./run_workbench.sh
```

### Active Service Endpoints:
- **Sovereign Console (Primary UI):** [http://localhost:8000](http://localhost:8000)
- **FastAPI OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Acceptance Test Suite (D1 - D5)

Run the autonomous verification suite:
```bash
python3 scripts/full_verify.py
```

### Verified Acceptance Matrix:
- **D1 (Agentic .docx Deliverable):** PASS · Generates signed OpenXML `MRPL_Approval_Note_V-101_*.docx`
- **D2 (Sandboxed Coding & Self-Correction):** PASS · Computes 24hr Delta P & exports `E104_Heat_Exchanger_Audit_Summary.xlsx`
- **D3 (Multimodal Inspection Understanding):** PASS · Extracts Equipment Tag `V-101`, corrosion rate `0.429 mm/yr`, and remaining life `1.63 yrs`
- **D4 (Model Auto-Selection):** PASS · Dynamically selects Qwen2.5, Qwen2.5-Coder, and Moondream with logged rationales
- **D5 (Air-Gap Zero-Egress Proof):** PASS · Kernel-level `bwrap --unshare-net` blocks raw network egress with `[Errno 101]`

---

## 📂 Repository Structure

```text
SIH 2026/
├── backend/
│   └── main.py                 # FastAPI REST API (/chat, /task, /models, /kb, /audit/network)
├── agent/
│   ├── loop.py                 # Autonomous ReAct state machine
│   ├── router.py               # Capability-driven multi-model router
│   └── tools/
│       ├── doc_gen.py          # python-docx, openpyxl, python-pptx deliverable generator
│       ├── rag.py              # Offline vector RAG over API-510 & OISD SOPs
│       ├── sandbox.py          # Bubblewrap kernel network-isolated sandbox
│       └── vision_ocr.py       # Tesseract OCR & multimodal inspection analyzer
├── data/
│   └── sample_docs/            # Datasets: P&IDs, Inspection Sheets, Operating Logs, SOPs
├── frontend/
│   └── app.py                  # Streamlit mission control dashboard
├── outputs/                    # Generated .docx, .xlsx, .csv deliverables
├── scripts/
│   └── full_verify.py          # Canonical acceptance test suite (D1 - D5)
├── prototype.py                # Standalone single-file prototype server
├── run_workbench.sh            # One-command full-stack launcher
├── STATE.md                    # Verification loop tracking
├── ISSUES.md                   # Zero open items bug tracker
├── DECISIONS.md                # Architectural design rationale
├── DEMO.md                     # 3-minute presentation script
└── EVIDENCE.md                 # Raw test execution logs
```
