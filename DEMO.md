# DEMO SCRIPT — 3-MINUTE JUDGES PRESENTATION
Project PS-26117 · "Sovereign On-Premise Agentic AI Workbench" (MRPL)

## Timeline & Presentation Plan

### ⏱️ Minute 0:00 - 0:45 · The Air-Gap & Zero-Egress Proof (D5)
- **Action**: Open terminal, run `curl -v --max-time 3 https://www.google.com`.
- **Speech**: *"Judges, industrial integrity data cannot leak to cloud APIs. Our sovereign workbench operates under an enforced kernel firewall (`iptables OUTPUT DROP`). Notice the request immediately times out with 0 egress bytes."*

### ⏱️ Minute 0:45 - 1:30 · Dynamic Capability-Driven Model Auto-Selection (D4)
- **Action**: Open UI at `http://localhost:8501` (or `http://localhost:8080`). Submit general, vision, and coding tasks.
- **Speech**: *"Our system doesn't rely on a single monolithic model. The Capability Router classifies each task against registered open-weight models (Qwen2.5 Reasoning on 8001, Qwen2.5-Coder on 8002, Moondream Vision on 8003) and displays the rationale live."*

### ⏱️ Minute 1:30 - 2:15 · Multimodal Report to Signed .docx Deliverable (D1 & D3)
- **Action**: Run Demo B on `CDU_V101_Inspection_Turnaround_Report.png`.
- **Speech**: *"The agent ingests a scanned turnaround inspection report, runs local OCR, calculates corrosion rate (0.429 mm/yr) and remaining life (1.63 yrs), queries offline API-510 regulatory standard clauses, and generates an authentic signed corporate Approval Note `.docx`."*

### ⏱️ Minute 2:15 - 3:00 · Sandboxed Code Execution & Self-Correction (D2)
- **Action**: Run Demo C on `E104_Heat_Exchanger_Operating_Log.csv`.
- **Speech**: *"The agent writes Python code and executes it in an unprivileged Bubblewrap kernel sandbox (`--unshare-net`). When an initial calculation limit is encountered, the agent reflects, iterates, and outputs a verified Excel/CSV audit sheet with zero network exposure."*
