# Graph Report - patelvraj1922-ai-verbose-tribble  (2026-09-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 700 nodes · 1493 edges · 39 communities (36 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `44f19491`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- os
- verify_l17.py
- run_eval.py
- doc_gen.py
- main.jsx
- SovereignStateGraphEngine
- verify_l16.py
- prototype.py
- TamperEvidentLedger
- VisionOCRTool
- main.py
- hybrid_retriever.py
- LocalRAGEngine
- AirgapComplianceGuard
- post
- HardwareDetector
- SovereignAuditLogger
- DocumentComparisonTool
- BaseModel
- stt_engine.py
- verify_ledger.py
- AirgapAttestationEngine
- SovereignKnowledgePackEngine
- PhysicsGuardrail
- SchemaFieldExtractor
- GroundedClaimVerifier
- .get_role_model
- .parse_pdf
- download_deliverable
- .installed_models
- check_compliance
- compare_documents
- generate_presentation
- get_hardware_profile
- ocr_handwriting_endpoint
- hitl_decision
- inspect_file
- security_headers
- run_workbench.sh

## God Nodes (most connected - your core abstractions)
1. `SovereignStateGraphEngine` - 22 edges
2. `LocalRAGEngine` - 20 edges
3. `AgentState` - 19 edges
4. `VisionOCRTool` - 19 edges
5. `DocumentGeneratorTool` - 18 edges
6. `CapabilityRouter` - 17 edges
7. `SovereignAgentLoop` - 16 edges
8. `HybridGraphRetriever` - 16 edges
9. `EngineeringCalculationEngine` - 15 edges
10. `LocalLLMClient` - 15 edges

## Surprising Connections (you probably didn't know these)
- `CapabilityRouter` --uses--> `HardwareDetector`  [INFERRED]
  agent/router.py → hardware/detect.py
- `run_egress_probe()` --uses--> `CodeSandboxTool`  [INFERRED]
  backend/main.py → agent/tools/sandbox.py
- `SovereignEvaluationHarness` --uses--> `PlantDocumentClassifier`  [INFERRED]
  eval/run_eval.py → ml/classifier.py
- `HybridGraphRetriever` --uses--> `LocalRAGEngine`  [INFERRED]
  kb/hybrid_retriever.py → agent/tools/rag.py
- `run_l20_verification()` --uses--> `AirgapComplianceGuard`  [INFERRED]
  scripts/verify_l20_registry.py → security/egress_denylist.py

## Import Cycles
- None detected.

## Communities (39 total, 3 thin omitted)

### Community 0 - "os"
Cohesion: 0.05
Nodes (75): ===============================================================================…, Autonomous ReAct State Machine with Real Open-Weight Model Inference, Load-…, SovereignAgentLoop, ===============================================================================…, CapabilityRouter, ===============================================================================…, Hardware-Adaptive Capability Router. Routes industrial queries across 5…, EngineeringCalculationEngine (+67 more)

### Community 1 - "verify_l17.py"
Cohesion: 0.05
Nodes (52): LinearRegression, math, matplotlib_pyplot, PlantDocumentClassifier, Any, ml/classifier.py ================ Classical ML Document Type and Defect…, Trains TF-IDF + Classifier models with train/test split and computes metrics., Classifies an input text into document type and defect criticality with… (+44 more)

### Community 2 - "run_eval.py"
Cohesion: 0.06
Nodes (42): ConstrainedDecoder, Any, BaseModel, eval/constrained_decoder.py =========================== Constrained Structured…, Interfaces with local Ollama runtime to pass `format: schema` for strict…, Sends generation request with JSON schema constraint to Ollama. Validates…, Simulates unconstrained generation without JSON schema to measure baseline…, Any (+34 more)

### Community 3 - "doc_gen.py"
Cohesion: 0.07
Nodes (24): DocumentGeneratorTool, Any, SIH 2026 Sovereign Document Generator. Produces strictly derived DOCX memos,…, Generates dual CSV and styled XLSX audit spreadsheets., Prevent same-second runs or copied files from overwriting artifacts., Generates formal DOCX with provenance, step-by-step formula breakdowns, and…, PresentationGeneratorTool, Any (+16 more)

### Community 4 - "main.jsx"
Cohesion: 0.06
Nodes (29): dependencies, gsap, react, react-dom, vite, @vitejs/plugin-react, name, private (+21 more)

### Community 5 - "SovereignStateGraphEngine"
Cohesion: 0.10
Nodes (15): AgentState, Any, SovereignStateGraphEngine, Any, Any, Resumes from earlier checkpoint state with counterfactual parameter…, Executes a run using LangGraph with SQLite checkpointing., Re-executes past run with identical inputs and frozen seed. (+7 more)

### Community 6 - "verify_l16.py"
Cohesion: 0.09
Nodes (21): BilingualNoteEngine, Any, edge/bilingual_engine.py ======================== Bilingual Translation &…, Generates bilingual technical deliverables for Mangalore Refinery operations.…, Generates byte-consistent bilingual approval note. Protects technical…, Path, HybridGraphRetriever, Any (+13 more)

### Community 7 - "prototype.py"
Cohesion: 0.10
Nodes (14): datetime, http_server, CapabilityRouter, DeliverableGenerator, main(), MultimodalInspectionAnalyzer, OfflineRAGEngine, Any (+6 more)

### Community 8 - "TamperEvidentLedger"
Cohesion: 0.15
Nodes (12): Any, Creates the genesis block if the ledger is empty., Appends a cryptographically signed, hash-chained record containing ONLY content…, Computes the Merkle root of all record hashes belonging to a given…, Returns all records in the ledger., Returns up to `limit` most recent records., Initializes or loads the Ed25519 keypair, enforcing 0600 on private key., Produces deterministic canonical JSON representation. (+4 more)

### Community 9 - "VisionOCRTool"
Cohesion: 0.13
Nodes (13): FileIngestionTool, Any, Sniffs file content magic bytes to detect true file format regardless of…, Main entry point: Ingests any user document and returns normalized structured…, SIH 2026 Unified Sovereign File Ingestion Engine. Dispatches by real content…, Any, True Multimodal OCR & Handwriting Entity Parser. Extracts raw text via…, Transcribes handwritten or low-confidence documents using local multimodal… (+5 more)

### Community 10 - "main.py"
Cohesion: 0.15
Nodes (20): audit_network(), get_ablation_results(), get_audit_logs(), get_knowledge_graph(), get_ledger_records(), get_model_registry(), get_verify_suite(), health_check() (+12 more)

### Community 11 - "hybrid_retriever.py"
Cohesion: 0.14
Nodes (11): DiGraph, EquipmentKnowledgeGraphBuilder, Serializes graph to disk with node and edge attributes., Loads graph from disk if present, else builds from default., ===============================================================================…, Builds deterministic refinery asset integrity knowledge graph with strict…, ===============================================================================…, networkx (+3 more)

### Community 12 - "LocalRAGEngine"
Cohesion: 0.17
Nodes (8): ComplianceCheckingTool, Any, Runs rigorous standard compliance check against extracted document data.…, LocalRAGEngine, Any, Performs local keyword-matching search. Returns empty list if no matches found., Structured query interface returning matches and count., Offline local knowledge base engine indexing refinery SOPs & standards.…

### Community 13 - "AirgapComplianceGuard"
Cohesion: 0.18
Nodes (12): Deliberately triggers an egress check against a forbidden cloud API host to…, test_cloud_denylist_probe(), PermissionError, AirgapComplianceGuard, guarded_connect(), guarded_create_connection(), guarded_send(), guarded_urlopen() (+4 more)

### Community 14 - "post"
Cohesion: 0.13
Nodes (15): api_verify_ledger(), export_knowledge_pack(), generate_attestation(), generate_fleet_risk(), get_visualization_data(), Accepts .pdf, .png, .jpg, .jpeg, .csv, .xlsx, .docx, .txt. Sanitizes filename,…, Executes scripts/full_verify.py and returns live real-time pass/fail results., Demonstrates tamper evidence by mutating 1 byte, running the verifier,… (+7 more)

### Community 15 - "HardwareDetector"
Cohesion: 0.23
Nodes (6): HardwareDetector, Any, Evaluates hardware metrics against registry profiles. Returns selected profile…, Returns total physical RAM in GB., Queries nvidia-smi or rocm-smi for dedicated GPU VRAM. Returns (vram_gb,…, Return live total/used VRAM and utilization without simulating values.

### Community 16 - "SovereignAuditLogger"
Cohesion: 0.22
Nodes (7): Any, Write an immutable, uniquely named audit snapshot for one agent run., SIH 2026 Sovereign Audit Logger (Immutable Append-Only Audit Trail). Records…, Appends an audit record to the immutable JSONL file., Retrieves the most recent audit records in reverse chronological order., Generates security and compliance summary counts., SovereignAuditLogger

### Community 17 - "DocumentComparisonTool"
Cohesion: 0.29
Nodes (5): DocumentComparisonTool, Any, Extracts structured fields from PDF, image, text, or JSON., Compares two document files field-by-field. Document A is considered Baseline…, Compares two extracted data dictionaries.

### Community 18 - "BaseModel"
Cohesion: 0.18
Nodes (11): chat_endpoint(), ChatRequest, execute_task(), BaseModel, query_graph_rag(), QueryGraphRequest, Performs 3-way RRF fused retrieval (Dense Vector + BM25 Lexical + Graph Multi-…, Applies refinery domain phonetic lexicon post-processing to raw field dictation. (+3 more)

### Community 19 - "stt_engine.py"
Cohesion: 0.20
Nodes (7): difflib, FieldVoiceIntakeEngine, Any, edge/stt_engine.py ================== Offline Voice Dictation Intake Engine for…, Computes standard Levenshtein-based Word Error Rate (WER) and domain-specific…, Simulates / wraps offline field voice intake (whisper.cpp engine) with domain…, Applies domain vocabulary biasing and extracts structured parameters from voice…

### Community 20 - "verify_ledger.py"
Cohesion: 0.24
Nodes (9): cryptography_exceptions, log_test(), main(), canonical_json(), main(), Any, ===============================================================================…, Forensically validates every record in the ledger. Returns: (is_valid,… (+1 more)

### Community 21 - "AirgapAttestationEngine"
Cohesion: 0.29
Nodes (5): AirgapAttestationEngine, Any, Renders the cryptographic attestation into a formal signed PDF report., Reads kernel network counters from /proc/net/dev if available., Collects airgap proof metrics and cryptographically signs the record.

### Community 22 - "SovereignKnowledgePackEngine"
Cohesion: 0.31
Nodes (5): Any, Path, Verifies Ed25519 digital signature and unpacks archive into target directory.…, Gathers SOP corpus, KG json, and RAG documents into a signed tarball archive.…, SovereignKnowledgePackEngine

### Community 23 - "PhysicsGuardrail"
Cohesion: 0.22
Nodes (5): PhysicsGuardrail, Any, Enforces physical laws: 1. 0 < measured_thickness <= nominal_thickness 2.…, Enforces thermodynamics & API-510 calculation constraints: 1. 0 <= CR <=…, Scans LLM output text for stated numerical figures and cross-checks them…

### Community 24 - "SchemaFieldExtractor"
Cohesion: 0.38
Nodes (4): Any, SIH 2026 Schema-Driven Field Extractor. Parses OCR text and table structures…, Extracts all schema-defined fields from OCR / document text., SchemaFieldExtractor

### Community 25 - "GroundedClaimVerifier"
Cohesion: 0.33
Nodes (4): GroundedClaimVerifier, Any, Splits narrative into discrete factual propositions., Evaluates entailment for each proposition against source spans and extracted…

### Community 26 - ".get_role_model"
Cohesion: 0.40
Nodes (3): Any, Re-evaluates hardware metrics and updates the active profile., Returns model specification for a given role under the active profile.

### Community 27 - ".parse_pdf"
Cohesion: 0.50
Nodes (3): Any, Parses a PDF file and returns structured text by page with metadata., Searches for specific terms across all pages of a PDF.

### Community 28 - "download_deliverable"
Cohesion: 0.40
Nodes (5): api_route, download_deliverable(), get_deliverable_content(), resolve_deliverable_path(), serve_console()

### Community 30 - "check_compliance"
Cohesion: 0.67
Nodes (3): check_compliance(), ComplianceCheckRequest, Checks extracted report data against API-510, OISD, and ASME standards with…

### Community 31 - "compare_documents"
Cohesion: 0.67
Nodes (3): compare_documents(), DocumentCompareRequest, Performs field-level comparison between two inspection/engineering documents.…

### Community 32 - "generate_presentation"
Cohesion: 0.67
Nodes (3): generate_presentation(), PresentationRequest, Generates a 6-10 slide executive presentation deck (.pptx) dynamically from…

### Community 33 - "get_hardware_profile"
Cohesion: 0.67
Nodes (3): get_hardware_profile(), HardwareDetectRequest, Returns detected RAM, detected VRAM, active profile (STANDARD vs…

### Community 34 - "ocr_handwriting_endpoint"
Cohesion: 0.67
Nodes (3): HandwritingOCRRequest, ocr_handwriting_endpoint(), Processes inspection sheet or field log using vision OCR and handwriting…

### Community 35 - "hitl_decision"
Cohesion: 0.67
Nodes (3): hitl_decision(), HitlDecisionRequest, Receives human engineer sign-off decision (Approve / Reject) and logs to…

### Community 36 - "inspect_file"
Cohesion: 0.67
Nodes (3): inspect_file(), InspectRequest, Ingests file and returns parsed schema fields and confidence scores before the…

## Knowledge Gaps
- **17 isolated node(s):** `capabilities`, `run_workbench.sh script`, `gsap`, `react`, `react-dom` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 271 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TamperEvidentLedger` connect `TamperEvidentLedger` to `os`, `main.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `HybridGraphRetriever` connect `verify_l16.py` to `hybrid_retriever.py`, `main.py`, `run_eval.py`, `LocalRAGEngine`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `LocalRAGEngine` connect `LocalRAGEngine` to `os`, `SovereignStateGraphEngine`, `verify_l16.py`, `main.py`, `hybrid_retriever.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `capabilities`, `run_workbench.sh script`, `gsap` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `os` be split into smaller, more focused modules?**
  _Cohesion score 0.05420353982300885 - nodes in this community are weakly interconnected._
- **Should `verify_l17.py` be split into smaller, more focused modules?**
  _Cohesion score 0.053763440860215055 - nodes in this community are weakly interconnected._
- **Should `run_eval.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._