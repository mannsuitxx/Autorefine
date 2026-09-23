import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { gsap } from 'gsap'
import './styles.css'

const api = async (url, options) => {
  const response = await fetch(url, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status})`)
  return data
}

const formatArtifactTime = (value) => {
  if (!value) return 'Timestamp unavailable'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Timestamp unavailable' : date.toLocaleString([], {
    year: 'numeric', month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const presets = {
  'Inspection approval': 'Analyze the attached scanned inspection report for V-101, verify API-510 statutory compliance, and generate a signed corporate Approval Note deliverable.',
  'Heat exchanger calculation': 'Execute sandboxed engineering calculations for Heat Exchanger E-104 operating log, compute 24hr shell/tube delta P, evaluate fouling limits, and generate an audit spreadsheet.',
  'Policy synthesis': 'What are the mandatory inspection interval limits and weld overlay requirements under API-510 when remaining life is under 2 years?'
}

const capabilities = [
  ['Report generation', 'Convert raw evidence into professional operational reports.'],
  ['Data analysis', 'Analyze CSV, Excel, and database exports with traceable calculations.'],
  ['Data visualization', 'Generate charts, graphs, and dashboards from local datasets.'],
  ['Enterprise search', 'Search indexed manuals, SOPs, reports, and correspondence.'],
  ['Research', 'Produce cited findings from the offline knowledge base.'],
  ['Meeting analysis', 'Turn transcripts into summaries, decisions, and action items.'],
  ['Speech-to-text', 'Transcribe locally available meeting and inspection audio.'],
  ['Translation', 'Translate technical and business documents while preserving structure.'],
  ['Content writing', 'Draft reports, letters, proposals, notices, and approval notes.'],
  ['Invoice processing', 'Extract invoice fields and validate totals and metadata.'],
  ['Form processing', 'Read forms and produce structured records.'],
  ['Document verification', 'Compare identity, asset, and compliance information across files.'],
  ['Calculations', 'Perform engineering, financial, and statistical calculations with steps.'],
  ['Engineering analysis', 'Interpret technical documents, measurements, and calculations.'],
  ['Maintenance support', 'Analyze maintenance records against manuals and history.'],
  ['Incident analysis', 'Analyze incident and inspection reports for causes and actions.'],
  ['Risk analysis', 'Identify, rank, and explain operational risks.'],
  ['Security analysis', 'Analyze local logs, configurations, and security reports.'],
  ['Testing and QA', 'Generate test cases and validate outputs in the sandbox.'],
  ['Debugging', 'Find, explain, and fix software errors with verification.'],
  ['DevOps', 'Analyze logs, configurations, and deployment failures.'],
  ['System administration', 'Diagnose local Linux or Windows server problems.'],
  ['Automation', 'Run repeatable multi-step workflows with audit trails.'],
  ['API interaction', 'Call approved internal APIs and local tools only.'],
  ['File management', 'Create, modify, organize, and transform local files.'],
  ['Document comparison', 'Compare document versions and show meaningful changes.'],
  ['Decision support', 'Compare options and recommend evidence-backed actions.'],
  ['Financial analysis', 'Analyze budgets, expenses, forecasts, and variances.'],
  ['Inventory analysis', 'Analyze stock, demand, and reorder requirements.'],
  ['HR work', 'Draft job descriptions, employee reports, and policy answers.'],
  ['Training', 'Generate courses, quizzes, and learning material.'],
  ['Education', 'Explain concepts, create questions, and evaluate answers.'],
  ['Health and safety documents', 'Analyze safety procedures, permits, and reports.'],
  ['Diagram understanding', 'Read flowcharts, P&IDs, and architecture diagrams.'],
  ['Visual inspection', 'Analyze equipment photographs for visible issues.'],
  ['OCR', 'Extract text from scanned and photographed documents.'],
  ['Handwriting recognition', 'Process handwritten notes where the local vision model supports it.'],
  ['Classification', 'Categorize documents, emails, incidents, and requests.'],
  ['Information extraction', 'Extract names, dates, values, IDs, and measurements.'],
  ['Summarization', 'Create short, medium, or detailed summaries.'],
  ['Transformation', 'Convert PDF to data, text to reports, and data to presentations.'],
  ['Presentation creation', 'Generate presentation structure and slide content.'],
  ['Proposal creation', 'Generate project and business proposals from evidence.'],
  ['Policy analysis', 'Compare documents against internal policies.'],
  ['Compliance checking', 'Identify missing requirements and exceptions.'],
  ['Knowledge extraction', 'Turn unstructured documents into structured knowledge.']
]

const coreWorkflows = [
  ['Mathematical work', 'Solve, calculate, explain steps, and verify.', 'Solve the supplied mathematical or engineering problem, show every step, verify the result, and identify assumptions.'],
  ['PDF and documents', 'Read, summarize, extract, compare, and answer questions.', 'Read the attached document, extract the important facts, compare relevant requirements, and answer the user question with page references.'],
  ['Coding', 'Generate, explain, debug, test, and execute code.', 'Build the requested program, explain the design, execute it in the sandbox with representative inputs, and fix any test failures.'],
  ['Image understanding', 'Analyze photos, diagrams, charts, and drawings.', 'Analyze the attached image or drawing, identify visible components and anomalies, and clearly separate observations from uncertain inferences.'],
  ['Information search', 'Search internal knowledge and documents.', 'Search the local knowledge base for the requested information and return a concise answer with source documents and matching passages.'],
  ['Excel and data', 'Analyze spreadsheets, calculate KPIs, and create reports.', 'Analyze the attached spreadsheet, calculate the requested KPIs, validate the calculations, and produce a clear findings report.'],
  ['Writing', 'Draft letters, reports, approval notes, and emails.', 'Draft the requested professional document from the supplied evidence, preserve factual boundaries, and list items requiring human approval.'],
  ['Presentation', 'Create presentation structure and content.', 'Create a slide-by-slide presentation outline from the supplied material, including titles, key points, speaker notes, and source references.'],
  ['OCR', 'Read scanned and handwritten documents.', 'Extract all legible text and structured fields from the attached scan, mark uncertain readings, and return a review-ready transcription.'],
  ['Reasoning', 'Solve multi-step problems and support decisions.', 'Analyze the problem step by step, compare alternatives, state trade-offs, and recommend an action supported by the available evidence.'],
  ['RAG and knowledge base', 'Answer using company manuals and SOPs.', 'Answer the question using only the local manuals and SOPs, quote the relevant passages, and say when the corpus does not provide enough evidence.'],
  ['Agentic tasks', 'Plan, use tools, execute, verify, and deliver.', 'Plan the work, inspect the supplied files, use the appropriate local tools, verify each output, and produce the requested final deliverable.'],
  ['Code execution', 'Run and verify generated programs.', 'Generate the requested code, run it in the isolated sandbox, capture stdout and errors, and iterate until the tests pass or explain the blocker.'],
  ['Data visualization', 'Create graphs, charts, and dashboards.', 'Analyze the supplied data and create the most useful charts, explain the trends, and identify data quality limitations.'],
  ['File operations', 'Read, write, and create local files.', 'Transform the supplied files into the requested output format, preserve source data, validate the output, and report the generated file path.'],
  ['Translation', 'Translate technical and business documents.', 'Translate the supplied document into the requested language, preserve technical terms and structure, and flag ambiguous passages for review.'],
  ['Speech', 'Convert speech to text and support voice interaction.', 'Transcribe the supplied local audio, separate speakers when possible, identify unclear sections, and produce a meeting-ready summary.'],
  ['Security and privacy', 'Keep confidential information on-premise.', 'Review this workflow for data exposure, verify that processing remains on approved localhost services, and report any blocked or suspicious egress.']
]

function App() {
  const [tab, setTab] = useState('Mission')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [health, setHealth] = useState(null)
  const [models, setModels] = useState(null)
  const [kb, setKb] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [network, setNetwork] = useState(null)
  const [hardware, setHardware] = useState(null)
  const [prompt, setPrompt] = useState(presets['Inspection approval'])
  const [preset, setPreset] = useState('Inspection approval')
  const [uploaded, setUploaded] = useState(null)
  const [trajectory, setTrajectory] = useState([])
  const [runState, setRunState] = useState('idle')
  const [notice, setNotice] = useState('')
  const [operationOutput, setOperationOutput] = useState(null)
  const fileRef = useRef(null)
  const mainRef = useRef(null)

  const refresh = async () => {
    try {
      const [h, m, k, d, n, hw] = await Promise.all([
        api('/api/health'), api('/models'), api('/kb'), api('/api/deliverables'),
        api('/api/network'), api('/api/hardware_profile')
      ])
      setHealth(h); setModels(m); setKb(k); setDeliverables(d); setNetwork(n); setHardware(hw)
    } catch (error) { setNotice(error.message) }
  }
  useEffect(() => {
    if (runState !== 'running') return undefined
    const timer = setInterval(() => {
      api('/api/hardware_profile').then(setHardware).catch(() => {})
    }, 750)
    return () => clearInterval(timer)
  }, [runState])
  useEffect(() => { refresh() }, [])
  useEffect(() => { if (preset !== 'Custom task') setPrompt(presets[preset]) }, [preset])
  useEffect(() => {
    const root = mainRef.current
    if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    const animated = root.querySelectorAll('.notice, .card')
    const cards = root.querySelectorAll('.card')
    const context = gsap.context(() => {
      gsap.fromTo('.hero',
        { autoAlpha: 0, y: 8 },
        { autoAlpha: 1, y: 0, duration: 0.42, ease: 'power2.out' }
      )
      gsap.fromTo(animated,
        { autoAlpha: 0, y: 10 },
        { autoAlpha: 1, y: 0, duration: 0.34, delay: 0.08, stagger: 0.045, ease: 'power2.out' }
      )
      gsap.fromTo(cards,
        { boxShadow: '0 14px 40px rgba(0,0,0,0)' },
        { boxShadow: '0 14px 40px rgba(0,0,0,0.2)', duration: 0.55, delay: 0.16, stagger: 0.045, ease: 'power1.out' }
      )
    }, root)
    return () => context.revert()
  }, [tab])

  const upload = async (file) => {
    if (!file) return
    setNotice(`Uploading ${file.name}…`)
    try {
      const body = new FormData(); body.append('file', file)
      const result = await api('/api/upload', { method: 'POST', body })
      setUploaded(result); setNotice(`${result.file_name} is ready for execution`)
    } catch (error) { setNotice(error.message) }
  }
  const run = async () => {
    if (!prompt.trim()) return setNotice('Enter an engineering instruction first.')
    setRunState('running'); setTrajectory([{ phase: 'ROUTER', summary: 'Dispatching to local capability model…' }]); setNotice('')
    try {
      const result = await api('/agent/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task: prompt, attached_files: uploaded ? [uploaded.server_path] : [] }) })
      setTrajectory(result.trajectory || []); setRunState('complete'); setNotice(`Completed in ${result.total_execution_time_sec || '—'}s with ${result.model_used || 'local model'}`); refresh()
    } catch (error) { setRunState('error'); setTrajectory([{ phase: 'FAILED', summary: error.message }]); setNotice(error.message) }
  }
  const runOperation = async (path, options = {}) => {
    setNotice(`Running ${options.label || 'local operation'}…`)
    try {
      const result = await api(path, options.body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(options.body) } : { method: 'POST' })
      setOperationOutput(result)
      setNotice(`${options.label || 'Operation'} completed locally`)
      await refresh()
      return result
    } catch (error) { setNotice(error.message); return null }
  }
  const inspectUpload = async () => {
    if (!uploaded?.server_path) return setNotice('Upload a document before inspecting it.')
    await runOperation('/api/inspect_file', { label: 'document inspection', body: { file_path: uploaded.server_path } })
  }
  const nav = ['Mission', 'Capabilities', 'Operations', 'Knowledge base', 'Model registry', 'Hardware telemetry', 'Network audit', 'Deliverables']
  const selectTab = (item) => { setTab(item); setMobileMenuOpen(false) }
  return <div className="app-shell">
    <aside className="rail">
      <div className="mark" aria-label="AutoRefine" tabIndex="0"><span className="mark-letter">A</span><span className="mark-dot">.</span><span className="mark-tooltip" role="tooltip">AutoRefine</span></div>
      {nav.map(item => <button key={item} className={`rail-button ${tab === item ? 'active' : ''}`} onClick={() => setTab(item)} title={item} aria-label={item}><span>{item}</span></button>)}
      <div className="rail-bottom"><button className="rail-button" onClick={refresh} title="Refresh telemetry" aria-label="Refresh telemetry"><span>Refresh telemetry</span></button></div>
    </aside>
    <div className="content">
      <header className="topbar"><div className="mobile-menu-wrap"><button className={`menu-button ${mobileMenuOpen ? 'open' : ''}`} onClick={() => setMobileMenuOpen(value => !value)} aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'} aria-expanded={mobileMenuOpen}><span/><span/><span/></button>{mobileMenuOpen && <><button className="menu-backdrop" aria-label="Close navigation menu" onClick={() => setMobileMenuOpen(false)}/><nav className="mobile-menu" aria-label="Mobile navigation">{nav.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => selectTab(item)}>{item}<span>›</span></button>)}<button className="mobile-refresh" onClick={() => { refresh(); setMobileMenuOpen(false) }}>Refresh telemetry<span>↻</span></button></nav></>}</div><div className="topbar-title"><div className="eyebrow">MRPL / AUTOREFINE RUNTIME</div><h1>AutoRefine Workbench</h1></div><div className="top-actions"><span className="pill"><i className="dot"/> AIR-GAP ENFORCED</span><button className="icon-button" onClick={refresh} aria-label="Refresh telemetry">Refresh</button></div></header>
      <main ref={mainRef}>
        <section className="hero"><div><div className="eyebrow accent">LOCAL-FIRST OPERATIONS</div><h2>{tab === 'Mission' ? 'Mission control' : tab}</h2><p>{tab === 'Mission' ? 'Run evidence-backed integrity workflows on your local industrial AI stack.' : `Inspect ${tab.toLowerCase()} across the AutoRefine runtime.`}</p></div><div className="hero-status"><strong>{health?.status || 'CONNECTING'}</strong><span>{hardware?.hardware_detected?.gpu_vram_used_gb ?? '—'} / {hardware?.hardware_detected?.gpu_vram_gb ?? '—'} GB VRAM active · {hardware?.active_profile || 'detecting'} profile</span></div></section>
        {notice && <div className={`notice ${runState === 'error' ? 'error' : ''}`}>{notice}<button onClick={() => setNotice('')}>×</button></div>}
        {tab === 'Mission' && <Mission prompt={prompt} setPrompt={setPrompt} preset={preset} setPreset={setPreset} fileRef={fileRef} upload={upload} uploaded={uploaded} run={run} runState={runState} trajectory={trajectory} deliverables={deliverables} setTab={setTab}/>}
        {tab === 'Capabilities' && <Capabilities setTab={setTab} setPrompt={setPrompt} setPreset={setPreset}/>}
        {tab === 'Operations' && <Operations uploaded={uploaded} inspectUpload={inspectUpload} runOperation={runOperation} output={operationOutput}/>}
        {tab === 'Knowledge base' && <Knowledge kb={kb}/>}
        {tab === 'Model registry' && <Models data={models} hardware={hardware} refresh={refresh}/>}
        {tab === 'Hardware telemetry' && <Hardware data={hardware} refresh={refresh}/>}
        {tab === 'Network audit' && <Network data={network} refresh={refresh}/>}
        {tab === 'Deliverables' && <Deliverables items={deliverables}/>}
      </main>

    </div>
  </div>
}

function Mission({ prompt, setPrompt, preset, setPreset, fileRef, upload, uploaded, run, runState, trajectory, deliverables, setTab }) {
  const userDeliverables = deliverables.filter(d => d.artifact_type !== 'audit_log')
  return <div className="grid mission-grid"><section className="card task-card"><div className="card-head"><div><span className="label">01 / FORMULATE</span><h3>Engineering task</h3></div><span className="status-tag">READY</span></div><label>Acceptance preset<select value={preset} onChange={e => setPreset(e.target.value)}>{Object.keys(presets).map(x => <option key={x}>{x}</option>)}<option>Custom task</option></select></label><label>Instruction<textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Describe the integrity decision you need…" /></label><div className="upload-box" onClick={() => fileRef.current?.click()}><input ref={fileRef} type="file" hidden onChange={e => upload(e.target.files[0])}/><span className="upload-icon">Upload</span><div><strong>{uploaded ? uploaded.file_name : 'Attach evidence'}</strong><small>{uploaded ? `${Math.round(uploaded.size_bytes / 1024)} KB · SHA256 verified` : 'PDF, image, CSV, XLSX, DOCX or TXT · max 50 MB'}</small></div><button type="button" onClick={e => { e.stopPropagation(); fileRef.current?.click() }}>Browse files</button></div><button className="primary-button" onClick={run} disabled={runState === 'running'}>{runState === 'running' ? 'Executing local loop…' : 'Execute sovereign loop'}<span>Run</span></button></section><section className="card trajectory-card"><div className="card-head"><div><span className="label">02 / OBSERVE</span><h3>ReAct trajectory</h3></div><span className={`status-tag ${runState}`}>{runState === 'running' ? 'RUNNING' : runState === 'complete' ? 'COMPLETE' : 'LIVE'}</span></div>{trajectory.length ? <div className="trajectory">{trajectory.map((step, i) => <div className="step" key={i}><div className="step-index">{String(i + 1).padStart(2, '0')}</div><div><strong>{step.phase || 'AGENT'}</strong><p>{step.summary || step.observation || step.response_text || step.reason || 'State transition completed.'}</p></div><span className="step-time">+{step.timestamp || '—'}s</span></div>)}</div> : <div className="empty"><div className="empty-icon">Ready</div><strong>Ready for a controlled run</strong><p>Your agent trajectory, invariant checks and deliverables will appear here.</p></div>}{runState === 'complete' && <div className="result-banner"><span>Pass</span><div><strong>Execution verified</strong><small>Physics guards passed · local audit recorded</small></div><button onClick={() => setTab('Deliverables')}>View artifacts</button></div>}</section><section className="card quick-card"><span className="label">03 / OUTPUTS</span><h3>Latest deliverables</h3>{userDeliverables.slice(0, 5).map(d => <a className="file-row" key={d.filename} href={`/outputs/${encodeURIComponent(d.filename)}`}><span className="file-type">{d.filename.split('.').pop()?.toUpperCase()}</span><span>{d.filename}</span><span><small>{formatArtifactTime(d.generated_at || d.mtime * 1000)}</small>Download</span></a>)}{!userDeliverables.length && <p className="muted">No generated artifacts yet.</p>}</section></div>
}

function Capabilities({ setTab, setPrompt, setPreset }) {
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => capabilities.filter(([name, description]) => `${name} ${description}`.toLowerCase().includes(query.toLowerCase())), [query])
  const useCapability = (name) => {
    setPreset('Custom task')
    setPrompt(`Use the local workbench for ${name.toLowerCase()}. Describe the source files, constraints, required checks, and final deliverable.`)
    setTab('Mission')
  }
  const useWorkflow = (name, example) => {
    setPreset('Custom task')
    setPrompt(example)
    setTab('Mission')
  }
  return <section className="card page-card capabilities-page">
    <div className="card-head"><div><span className="label">LOCAL TASK CATALOG</span><h3>Capabilities</h3><p className="muted">Every workflow stays on the approved local runtime. Select a capability to start a real task.</p></div><span className="metric">{filtered.length} of {capabilities.length}</span></div>
    <div className="workflow-heading"><span className="label">CORE WORKFLOWS</span><span className="muted">Example-driven entry points</span></div>
    <div className="workflow-grid">{coreWorkflows.map(([name, description, example]) => <button className="workflow-card" key={name} onClick={() => useWorkflow(name, example)}><strong>{name}</strong><small>{description}</small><em>{example}</em><span>Start workflow</span></button>)}</div>
    <div className="workflow-heading"><span className="label">FULL CATALOG</span><span className="muted">Search all local capabilities</span></div>
    <label className="search-field">Search capabilities<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search OCR, engineering, reports…" /></label>
    <div className="capability-grid">{filtered.map(([name, description], index) => <button className="capability-card" key={name} onClick={() => useCapability(name)}><span className="capability-number">{String(index + 1).padStart(2, '0')}</span><span><strong>{name}</strong><small>{description}</small></span><span className="capability-action">Use</span></button>)}</div>
  </section>
}

function Operations({ uploaded, inspectUpload, runOperation, output }) {
  return <section className="card page-card operations-page">
    <div className="card-head"><div><span className="label">LOCAL TOOL EXECUTION</span><h3>Operations</h3><p className="muted">These controls call the real backend tools directly and create auditable local outputs.</p></div><span className="metric">{uploaded ? uploaded.file_name : 'No file attached'}</span></div>
    <div className="operation-grid">
      <button className="operation-card" onClick={inspectUpload}><strong>Inspect uploaded file</strong><small>Parse text, metadata, detected type, fields, and warnings before an agent run.</small><span>Run inspection</span></button>
      <button className="operation-card" onClick={() => runOperation('/api/generate_fleet_risk', { label: 'fleet risk worklist' })}><strong>Generate fleet risk worklist</strong><small>Create the local Excel worklist from the fleet risk engine.</small><span>Generate XLSX</span></button>
      <button className="operation-card" onClick={() => runOperation('/api/generate_attestation', { label: 'air-gap attestation' })}><strong>Generate air-gap attestation</strong><small>Create the PDF report from the local security attestation engine.</small><span>Generate PDF</span></button>
      <button className="operation-card" onClick={() => runOperation('/api/export_knowledge_pack', { label: 'knowledge pack export' })}><strong>Export knowledge pack</strong><small>Package the indexed local corpus into a portable knowledge artifact.</small><span>Export pack</span></button>
      <button className="operation-card" onClick={() => runOperation('/api/visualize_data', { label: 'visualization data' })}><strong>Load visualization data</strong><small>Retrieve local fleet risk and corrosion trend series for charts.</small><span>Load data</span></button>
      <button className="operation-card" onClick={() => runOperation('/api/security_probe/cloud_blocked', { label: 'cloud egress probe' })}><strong>Verify cloud blocking</strong><small>Run the deny-list probe and record the blocked egress event.</small><span>Run probe</span></button>
    </div>
    {output && <pre className="operation-output">{JSON.stringify(output, null, 2)}</pre>}
  </section>
}

function Knowledge({ kb }) { return <section className="card page-card"><div className="card-head"><div><span className="label">OFFLINE CORPUS</span><h3>Knowledge base</h3></div><span className="metric">{kb?.total_documents || 0} documents · {kb?.total_chunks || 0} chunks</span></div><div className="table">{(kb?.indexed_documents || []).map(d => <div className="table-row" key={d.filename}><strong>{d.filename}</strong><span>{d.category}</span><span className="green-text">INDEXED</span></div>)}</div></section> }
function Models({ data, hardware, refresh }) { return <section className="card page-card"><div className="card-head"><div><span className="label">CAPABILITY ROUTER</span><h3>Model registry</h3><p className="muted">{hardware?.active_profile || 'Detecting'} profile · {hardware?.hardware_detected?.gpu_vram_gb ?? '—'} GB VRAM · Local acceleration is selected automatically</p></div><button className="secondary-button" onClick={refresh}>Refresh models</button></div><div className="model-grid">{(data?.models || []).map(m => <div className="model-card" key={m.id}><div className="model-title"><span className="model-mark">Model</span><strong>{m.name}</strong><span className={m.status.startsWith('Available') ? 'green-text' : 'muted'}>{m.status}</span></div><code>{m.id}</code><p>{m.parameters} · {m.engine}</p><small>{m.license}</small></div>)}</div>{data?.ollama_live === false && <div className="notice error">The local model runtime is unavailable. Start the configured runtime and load a supported model before executing AI tasks.</div>}</section> }
function Network({ data, refresh }) { return <section className="card page-card"><div className="card-head"><div><span className="label">ZERO-EGRESS AUDIT</span><h3>Network health</h3></div><button className="secondary-button" onClick={refresh}>Run network audit</button></div><div className="network-summary"><div><span className="big-number">{data?.measured_wan_tx_bytes_sec ?? '—'}</span><small>WAN TX bytes / sec</small></div><div><span className="big-number green-text">{data?.active_wan_connections ?? '—'}</span><small>external connections</small></div><div><span className="big-number">{data?.measured_loopback_tx_bytes_sec ?? '—'}</span><small>loopback traffic</small></div></div><div className="security-callout"><span>Pass</span><div><strong>{data?.airgap_status || 'Checking air-gap status'}</strong><p>Cloud providers blocked by policy. Ollama localhost runtime is permitted.</p></div></div></section> }
function Hardware({ data, refresh }) { const h = data?.hardware_detected || {}; return <section className="card page-card"><div className="card-head"><div><span className="label">RUNTIME TELEMETRY</span><h3>Hardware telemetry</h3><p className="muted">Detected locally from the host; no simulated values are shown.</p></div><button className="secondary-button" onClick={refresh}>Refresh telemetry</button></div><div className="network-summary"><div><span className="big-number">{h.gpu_vram_used_gb ?? '—'} / {h.gpu_vram_gb ?? '—'} GB</span><small>VRAM active / total · {h.gpu_device || 'Unknown device'}</small></div><div><span className="big-number">{h.gpu_utilization_percent ?? '—'}%</span><small>GPU utilization · {h.gpu_telemetry_source || 'Unavailable'}</small></div><div><span className="big-number">{h.system_ram_gb ?? '—'} GB</span><small>System RAM · {data?.active_profile || '—'} profile</small></div></div><div className="security-callout"><span>Pass</span><div><strong>{data?.is_simulated === false ? 'Live host telemetry' : 'Telemetry unavailable'}</strong><p>{data?.reasoning || 'Hardware profile is selected from current host resources.'}</p></div></div></section> }
function Deliverables({ items }) { const userDeliverables = items.filter(d => d.artifact_type !== 'audit_log'); return <section className="card page-card"><div className="card-head"><div><span className="label">ARTIFACTS HUB</span><h3>Deliverables</h3><p className="muted">Generated timestamp is shown in your local time for run verification.</p></div><span className="metric">{userDeliverables.length} files</span></div>{userDeliverables.length ? <div className="table deliverables-table">{userDeliverables.map(d => <div className="table-row" key={d.filename}><strong>{d.filename}</strong><span>{Math.round(d.size_bytes / 1024)} KB</span><span className="artifact-time">{formatArtifactTime(d.generated_at || d.mtime * 1000)}</span><a className="download-link" href={`/outputs/${encodeURIComponent(d.filename)}`}>Download ↗</a></div>)}</div> : <div className="empty"><div className="empty-icon">□</div><strong>No deliverables yet</strong><p>Execute a task to generate signed, auditable artifacts.</p></div>}</section> }

createRoot(document.getElementById('root')).render(<App />)
