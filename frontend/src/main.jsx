import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertTriangle,
  GitBranch,
  CheckCircle2,
  ClipboardList,
  Cpu,
  Download,
  FileText,
  FlaskConical,
  HeartPulse,
  PlayCircle,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import { LANGUAGES, TRANSLATIONS } from './i18n';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8010';
const DEFAULT_LANGUAGE = 'en';
const LANGUAGE_STORAGE_KEY = 'periop-agent-language';
const MODALITY_OPTIONS = ['clinical_note', 'ecg', 'lab', 'imaging', 'medication', 'airway', 'other'];
const EVENT_TYPES = ['hypotension', 'hypertension', 'hypoxemia', 'arrhythmia', 'bleeding', 'airway', 'medication', 'other'];
const EVENT_SEVERITIES = ['low', 'medium', 'high', 'critical'];
const COPY = {
  ecgAdapter: 'ECG adapter',
  ecgAdapterReady: 'Rule-based text ECG adapter is available',
  ecgAdapterDetail: 'Uploads are parsed as structured findings for clinician review; this is not an autonomous ECG diagnosis.',
  intraopTitle: 'Intraoperative events',
  eventType: 'Event type',
  eventSeverity: 'Severity',
  eventDescription: 'Event description',
  eventAction: 'Clinician action summary',
  eventPlaceholder: 'Record hypotension, hypoxemia, arrhythmia, bleeding, airway issues, or other intra-op events...',
  actionPlaceholder: 'Summarize what the clinical team documented. Do not enter medication dose instructions.',
  addEvent: 'Add event',
  noEvents: 'No intraoperative events recorded for this case.',
  addingEvent: 'Adding intraoperative event...',
  eventAdded: 'Intraoperative event added.',
  postopTitle: 'Postoperative surveillance draft',
  postopFocus: 'Surveillance focus',
  postopChecks: 'Suggested checks',
  escalationTriggers: 'Escalation triggers',
  noPostopPlan: 'Generate a report first to build the postoperative surveillance draft.',
  outputSafety: 'Output safety boundary',
  outputSafetyText: 'This draft must not contain surgery clearance, individualized dosing, emergency commands, or patient-facing instructions.',
  bandTitle: 'Band collaboration trace',
  bandConfigured: 'Band configured',
  bandLocal: 'Local trace',
  bandBody: 'Shows how specialized agents share context and hand off work through the Band-ready collaboration layer.',
  bandGenerate: 'Generate trace',
  bandExport: 'Export transcript',
  bandGenerating: 'Generating Band collaboration trace...',
  bandGenerated: 'Band collaboration trace generated.',
  bandRequirementMet: '3+ agent requirement met',
  bandRequirementPending: 'Needs Band credentials for live collaboration',
  statusDraft: 'Draft',
  statusAssessed: 'Assessed',
  statusConfirmed: 'Clinician confirmed',
  statusEventLogged: 'Intra-op event logged',
};

async function requestJSON(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  const contentType = res.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    throw new Error(payload?.detail || payload || `Request failed with status ${res.status}`);
  }
  return payload;
}

function getInitialLanguage() {
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return TRANSLATIONS[stored] ? stored : DEFAULT_LANGUAGE;
}

function App() {
  const [language, setLanguage] = useState(getInitialLanguage);
  const t = TRANSLATIONS[language] || TRANSLATIONS[DEFAULT_LANGUAGE];
  const [cases, setCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [report, setReport] = useState(null);
  const [intraopEvents, setIntraopEvents] = useState([]);
  const [postopPlan, setPostopPlan] = useState(null);
  const [bandTrace, setBandTrace] = useState(null);
  const [manualText, setManualText] = useState('');
  const [modality, setModality] = useState('clinical_note');
  const [eventType, setEventType] = useState('hypoxemia');
  const [eventSeverity, setEventSeverity] = useState('medium');
  const [eventDescription, setEventDescription] = useState('');
  const [eventAction, setEventAction] = useState('');
  const [safetyText, setSafetyText] = useState('这个患者能不能手术？');
  const [safetyResult, setSafetyResult] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [operation, setOperation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  useEffect(() => {
    loadCases().catch((err) => setError(err.message));
    loadSystemStatus();
  }, []);

  useEffect(() => {
    if (activeCase) {
      loadDocuments(activeCase.id).catch((err) => setError(err.message));
      loadReport(activeCase.id);
      loadIntraopEvents(activeCase.id);
      loadPostopPlan(activeCase.id);
      loadBandTrace(activeCase.id);
    }
  }, [activeCase]);

  const highRiskCount = useMemo(() => {
    return report?.risk_flags?.filter((flag) => ['high', 'critical'].includes(flag.severity)).length || 0;
  }, [report]);

  const systemChecks = useMemo(() => {
    const reviewConfirmed = report?.review_status === 'clinician_confirmed';
    const safetyChecked = Boolean(safetyResult);
    const agentsSdkConfigured = Boolean(systemStatus?.agents_sdk_refinement_configured);
    const evalCaseCount = systemStatus?.eval_case_count;
    const safetyCategories = systemStatus?.safety_boundary_categories?.join(', ');
    const hasEcgDocument = documents.some((doc) => doc.modality === 'ecg');
    const hasEcgFinding = Boolean(report?.ecg_findings?.length);
    const bandConfigured = Boolean(systemStatus?.band_collaboration_configured);
    return [
      {
        key: 'band',
        icon: <GitBranch size={18} />,
        tone: bandTrace?.minimum_agent_requirement_met ? 'good' : 'watch',
        title: label(t, 'bandTitle'),
        status: bandConfigured ? label(t, 'bandConfigured') : label(t, 'bandLocal'),
        detail: bandTrace?.minimum_agent_requirement_met ? label(t, 'bandRequirementMet') : label(t, 'bandRequirementPending'),
      },
      {
        key: 'deterministic',
        icon: <Cpu size={18} />,
        tone: report ? 'good' : documents.length ? 'watch' : 'neutral',
        title: t.systemChecks.deterministic.title,
        status: report ? t.statusReady : documents.length ? t.statusQueued : t.statusWaiting,
        detail: report
          ? t.systemChecks.deterministic.reportReady
          : documents.length
            ? t.systemChecks.deterministic.readyToRun
            : t.systemChecks.deterministic.needDocuments,
      },
      {
        key: 'ecgAdapter',
        icon: <HeartPulse size={18} />,
        tone: hasEcgFinding ? 'good' : hasEcgDocument ? 'watch' : 'neutral',
        title: label(t, 'ecgAdapter'),
        status: hasEcgFinding ? t.statusReady : hasEcgDocument ? t.statusQueued : t.statusWaiting,
        detail: hasEcgFinding ? label(t, 'ecgAdapterReady') : label(t, 'ecgAdapterDetail'),
      },
      {
        key: 'agentsSdk',
        icon: <Activity size={18} />,
        tone: agentsSdkConfigured ? 'good' : 'neutral',
        title: t.systemChecks.agentsSdk.title,
        status: agentsSdkConfigured ? t.statusConfigured : t.statusOptional,
        detail: agentsSdkConfigured ? t.systemChecks.agentsSdk.configured : t.systemChecks.agentsSdk.optional,
      },
      {
        key: 'safety',
        icon: <ShieldCheck size={18} />,
        tone: safetyChecked ? (safetyResult.allowed ? 'good' : 'critical') : 'watch',
        title: t.systemChecks.safety.title,
        status: safetyChecked
          ? (safetyResult.allowed ? t.statusAllowed : t.statusBlocked)
          : t.statusStandby,
        detail: safetyChecked ? safetyResult.category : (safetyCategories || t.systemChecks.safety.detail),
      },
      {
        key: 'evals',
        icon: <FlaskConical size={18} />,
        tone: report || safetyChecked ? 'good' : 'neutral',
        title: t.systemChecks.evals.title,
        status: Number.isFinite(evalCaseCount)
          ? `${evalCaseCount} ${t.statusCaseCountSuffix}`
          : report || safetyChecked
            ? t.statusObserved
            : t.statusLocal,
        detail: t.systemChecks.evals.detail,
      },
      {
        key: 'review',
        icon: <CheckCircle2 size={18} />,
        tone: reviewConfirmed ? 'good' : 'watch',
        title: t.systemChecks.review.title,
        status: reviewConfirmed ? t.statusConfirmed : t.statusPending,
        detail: reviewConfirmed ? t.systemChecks.review.confirmed : t.systemChecks.review.pending,
      },
    ];
  }, [documents, report, safetyResult, systemStatus, t]);

  async function runOperation(label, task) {
    setBusy(true);
    setOperation(label);
    setMessage('');
    setError('');
    try {
      await task();
    } catch (err) {
      setError(err.message || t.genericError);
    } finally {
      setBusy(false);
      setOperation('');
    }
  }

  async function loadCases() {
    const data = await requestJSON('/api/cases');
    setCases(data);
    if (!activeCase && data.length) setActiveCase(data[0]);
  }

  async function loadSystemStatus() {
    try {
      setSystemStatus(await requestJSON('/api/system/status'));
    } catch {
      setSystemStatus(null);
    }
  }

  async function createCase() {
    await runOperation(t.creatingCase, async () => {
      const data = await requestJSON('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: `Pre-op assessment ${new Date().toLocaleString()}` }),
      });
      setActiveCase(data);
      await loadCases();
      setMessage(t.caseCreated);
    });
  }

  async function loadSampleCase() {
    await runOperation(t.loadingSample, async () => {
      const data = await requestJSON('/api/demo/sample-case', { method: 'POST' });
      setActiveCase(data.case);
      setDocuments(data.documents);
      setReport(data.report);
      await loadCases();
      setMessage(t.sampleLoaded);
    });
  }

  async function loadDocuments(caseId) {
    setDocuments(await requestJSON(`/api/cases/${caseId}/documents`));
  }

  async function loadReport(caseId) {
    try {
      setReport(await requestJSON(`/api/cases/${caseId}/report`));
    } catch {
      setReport(null);
    }
  }

  async function loadIntraopEvents(caseId) {
    try {
      setIntraopEvents(await requestJSON(`/api/cases/${caseId}/intraop-events`));
    } catch {
      setIntraopEvents([]);
    }
  }

  async function loadPostopPlan(caseId) {
    try {
      setPostopPlan(await requestJSON(`/api/cases/${caseId}/postop-plan`));
    } catch {
      setPostopPlan(null);
    }
  }

  async function loadBandTrace(caseId) {
    try {
      setBandTrace(await requestJSON(`/api/cases/${caseId}/band-collaboration`, { method: 'POST' }));
    } catch {
      setBandTrace(null);
    }
  }

  async function addManualText() {
    if (!activeCase || !manualText.trim()) return;
    await runOperation(t.addingText, async () => {
      await requestJSON(`/api/cases/${activeCase.id}/documents/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: `${modality}-manual.txt`,
          modality,
          text: manualText,
        }),
      });
      setManualText('');
      await loadDocuments(activeCase.id);
      setMessage(t.textAdded);
    });
  }

  async function uploadFile(event) {
    const file = event.target.files?.[0];
    if (!activeCase || !file) return;
    await runOperation(t.uploading, async () => {
      const form = new FormData();
      form.append('file', file);
      form.append('modality', modality);
      await requestJSON(`/api/cases/${activeCase.id}/documents`, {
        method: 'POST',
        body: form,
      });
      await loadDocuments(activeCase.id);
      setMessage(t.fileUploaded);
      event.target.value = '';
    });
  }

  async function runAssessment() {
    if (!activeCase) return;
    await runOperation(t.runningAssessment, async () => {
      const data = await requestJSON(`/api/cases/${activeCase.id}/analyze/preop`, { method: 'POST' });
      setReport(data);
      await loadPostopPlan(activeCase.id);
      await loadBandTrace(activeCase.id);
      await loadCases();
      setMessage(t.assessmentReady);
    });
  }

  async function confirmReport() {
    if (!activeCase || !report) return;
    await runOperation(t.savingReview, async () => {
      const data = await requestJSON(`/api/cases/${activeCase.id}/report/clinician-review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clinician_notes: report.clinician_notes || '',
          review_status: 'clinician_confirmed',
        }),
      });
      setReport(data);
      await loadCases();
      setMessage(t.reviewSaved);
    });
  }

  async function addIntraopEvent() {
    if (!activeCase || !eventDescription.trim()) return;
    await runOperation(label(t, 'addingEvent'), async () => {
      await requestJSON(`/api/cases/${activeCase.id}/intraop-events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: eventType,
          severity: eventSeverity,
          description: eventDescription,
          clinician_action_summary: eventAction,
        }),
      });
      setEventDescription('');
      setEventAction('');
      await loadIntraopEvents(activeCase.id);
      await loadPostopPlan(activeCase.id);
      await loadBandTrace(activeCase.id);
      await loadCases();
      setMessage(label(t, 'eventAdded'));
    });
  }

  async function generateBandTrace() {
    if (!activeCase || !report) return;
    await runOperation(label(t, 'bandGenerating'), async () => {
      setBandTrace(await requestJSON(`/api/cases/${activeCase.id}/band-collaboration`, { method: 'POST' }));
      setMessage(label(t, 'bandGenerated'));
    });
  }

  async function exportBandTrace() {
    if (!activeCase || !report) return;
    await runOperation(label(t, 'exporting'), async () => {
      const res = await fetch(`${API_BASE}/api/cases/${activeCase.id}/band-collaboration/export.md`);
      if (!res.ok) throw new Error(t.genericError);
      const markdown = await res.text();
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `band-collaboration-${activeCase.id}.md`;
      link.click();
      URL.revokeObjectURL(url);
      setMessage(t.exportDone);
    });
  }

  async function checkSafety() {
    if (!safetyText.trim()) return;
    await runOperation(t.checkingSafety, async () => {
      const data = await requestJSON('/api/safety/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: safetyText }),
      });
      setSafetyResult(data);
    });
  }

  async function exportReport() {
    if (!activeCase || !report) return;
    await runOperation(t.exporting, async () => {
      const res = await fetch(`${API_BASE}/api/cases/${activeCase.id}/report/export.md`);
      if (!res.ok) throw new Error(t.genericError);
      const markdown = await res.text();
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `periop-assessment-${activeCase.id}.md`;
      link.click();
      URL.revokeObjectURL(url);
      setMessage(t.exportDone);
    });
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <HeartPulse size={26} />
          <div>
            <h1>Periop Anesthesia Agent</h1>
            <p>{t.brandSubtitle}</p>
          </div>
        </div>
        <label className="language-select">
          <span>Language</span>
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            {LANGUAGES.map((item) => (
              <option key={item.code} value={item.code}>{item.label}</option>
            ))}
          </select>
        </label>
        <button className="primary" onClick={createCase} disabled={busy}>{t.newCase}</button>
        <button className="sample-button" onClick={loadSampleCase} disabled={busy}>
          <PlayCircle size={17} />
          {t.loadSample}
        </button>
        <div className="case-list">
          {cases.map((item) => (
            <button
              key={item.id}
              className={activeCase?.id === item.id ? 'case active' : 'case'}
              onClick={() => setActiveCase(item)}
            >
              <span>{item.title}</span>
              <small>{item.status}</small>
            </button>
          ))}
          {cases.length === 0 && <p className="sidebar-empty">{t.noCases}</p>}
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t.templateEyebrow}</p>
            <h2>{activeCase?.title || t.noCase}</h2>
          </div>
          <div className="status-strip">
            <Stat icon={<FileText size={18} />} label={t.documentsStat} value={documents.length} />
            <Stat icon={<AlertTriangle size={18} />} label={t.highRiskStat} value={highRiskCount} />
            <Stat icon={<CheckCircle2 size={18} />} label={t.statusStat} value={statusLabel(t, report?.review_status || activeCase?.status || 'draft')} />
          </div>
        </header>

        <div className="notice">
          <AlertTriangle size={18} />
          {t.notice}
        </div>

        <SystemValidationPanel checks={systemChecks} t={t} />

        {busy && <div className="busy-bar">{operation}</div>}
        {message && <div className="toast">{message}</div>}
        {error && <div className="error-banner">{error}</div>}

        <div className="grid">
          <section className="panel">
            <div className="panel-title">
              <Upload size={20} />
              <h3>{t.uploadTitle}</h3>
            </div>
            <label className="field">
              {t.modality}
              <select value={modality} onChange={(event) => setModality(event.target.value)}>
                {MODALITY_OPTIONS.map((item) => (
                  <option key={item} value={item}>{t.modalities[item]}</option>
                ))}
              </select>
            </label>
            <label className="file-drop">
              <input type="file" onChange={uploadFile} disabled={!activeCase || busy} />
              {t.fileDrop}
            </label>
            <textarea
              value={manualText}
              onChange={(event) => setManualText(event.target.value)}
              placeholder={t.manualPlaceholder}
            />
            <button className="secondary" onClick={addManualText} disabled={!activeCase || busy || !manualText.trim()}>
              {t.addDocument}
            </button>
          </section>

          <section className="panel">
            <div className="panel-title">
              <FileText size={20} />
              <h3>{t.previewTitle}</h3>
            </div>
            <div className="doc-list">
              {documents.length === 0 && <div className="empty-state">{t.emptyDocuments}</div>}
              {documents.map((doc) => (
                <article key={doc.id} className="doc-card">
                  <div>
                    <strong>{doc.filename}</strong>
                    <span>{doc.modality}</span>
                  </div>
                  <p>{doc.extracted_text || t.noExtractedText}</p>
                  {doc.extraction_notes?.map((note) => <small key={note}>{note}</small>)}
                </article>
              ))}
            </div>
            <button className="primary" onClick={runAssessment} disabled={!activeCase || busy || documents.length === 0}>
              {t.runAssessment}
            </button>
          </section>
        </div>

        <section className="panel safety-panel">
          <div className="panel-title">
            <AlertTriangle size={20} />
            <h3>{t.safetyTitle}</h3>
          </div>
          <div className="safety-check-row">
            <textarea
              value={safetyText}
              onChange={(event) => setSafetyText(event.target.value)}
              placeholder={t.safetyPlaceholder}
            />
            <button className="secondary" onClick={checkSafety} disabled={busy || !safetyText.trim()}>
              {t.checkBoundary}
            </button>
          </div>
          {safetyResult && (
            <div className={safetyResult.allowed ? 'safety-result allowed' : 'safety-result blocked'}>
              <strong>{safetyResult.allowed ? t.safetyAllowed : t.safetyBlocked}</strong>
              <span>{safetyResult.category}</span>
              <p>{safetyResult.reason}</p>
              <small>{safetyResult.safe_response}</small>
            </div>
          )}
        </section>

        <IntraopEventPanel
          events={intraopEvents}
          eventType={eventType}
          setEventType={setEventType}
          eventSeverity={eventSeverity}
          setEventSeverity={setEventSeverity}
          eventDescription={eventDescription}
          setEventDescription={setEventDescription}
          eventAction={eventAction}
          setEventAction={setEventAction}
          onAdd={addIntraopEvent}
          disabled={!activeCase || busy}
          t={t}
        />

        <BandCollaborationPanel
          trace={bandTrace}
          onGenerate={generateBandTrace}
          onExport={exportBandTrace}
          disabled={!activeCase || !report || busy}
          t={t}
        />

        <ReportView
          report={report}
          setReport={setReport}
          intraopEvents={intraopEvents}
          postopPlan={postopPlan}
          onConfirm={confirmReport}
          onExport={exportReport}
          busy={busy}
          t={t}
        />
      </section>
    </main>
  );
}

function label(t, key) {
  return t[key] || COPY[key] || key;
}

function statusLabel(t, status) {
  const labels = {
    draft: label(t, 'statusDraft'),
    assessed: label(t, 'statusAssessed'),
    clinician_confirmed: label(t, 'statusConfirmed'),
    intraop_event_logged: label(t, 'statusEventLogged'),
  };
  return labels[status] || status;
}

function Stat({ icon, label, value }) {
  return (
    <div className="stat">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SystemValidationPanel({ checks, t }) {
  return (
    <section className="system-panel">
      <div className="system-panel-copy">
        <p className="eyebrow">{t.systemPanelEyebrow}</p>
        <h3>{t.systemPanelTitle}</h3>
        <p>{t.systemPanelBody}</p>
      </div>
      <div className="system-check-grid">
        {checks.map((check) => (
          <article key={check.key} className={`system-check ${check.tone}`}>
            <div className="check-icon">{check.icon}</div>
            <div>
              <span>{check.title}</span>
              <strong>{check.status}</strong>
              <p>{check.detail}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function IntraopEventPanel({
  events,
  eventType,
  setEventType,
  eventSeverity,
  setEventSeverity,
  eventDescription,
  setEventDescription,
  eventAction,
  setEventAction,
  onAdd,
  disabled,
  t,
}) {
  return (
    <section className="panel intraop-panel">
      <div className="panel-title">
        <ClipboardList size={20} />
        <h3>{label(t, 'intraopTitle')}</h3>
      </div>
      <div className="event-form">
        <label className="field">
          {label(t, 'eventType')}
          <select value={eventType} onChange={(event) => setEventType(event.target.value)}>
            {EVENT_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label className="field">
          {label(t, 'eventSeverity')}
          <select value={eventSeverity} onChange={(event) => setEventSeverity(event.target.value)}>
            {EVENT_SEVERITIES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <textarea
          value={eventDescription}
          onChange={(event) => setEventDescription(event.target.value)}
          placeholder={label(t, 'eventPlaceholder')}
        />
        <textarea
          value={eventAction}
          onChange={(event) => setEventAction(event.target.value)}
          placeholder={label(t, 'actionPlaceholder')}
        />
        <button className="secondary" onClick={onAdd} disabled={disabled || !eventDescription.trim()}>
          {label(t, 'addEvent')}
        </button>
      </div>
      <div className="event-list">
        {!events.length && <div className="empty-state">{label(t, 'noEvents')}</div>}
        {events.map((event) => (
          <article key={event.id} className={`event-card ${event.severity}`}>
            <div>
              <strong>{event.event_type}</strong>
              <span>{event.severity}</span>
            </div>
            <p>{event.description}</p>
            {event.clinician_action_summary && <small>{event.clinician_action_summary}</small>}
          </article>
        ))}
      </div>
    </section>
  );
}

function BandCollaborationPanel({ trace, onGenerate, onExport, disabled, t }) {
  return (
    <section className="panel band-panel">
      <div className="panel-title">
        <GitBranch size={20} />
        <div>
          <h3>{label(t, 'bandTitle')}</h3>
          <p>{label(t, 'bandBody')}</p>
        </div>
      </div>
      <div className="band-actions">
        <button className="secondary" onClick={onGenerate} disabled={disabled}>
          {label(t, 'bandGenerate')}
        </button>
        <button className="secondary" onClick={onExport} disabled={disabled || !trace}>
          <Download size={17} />
          {label(t, 'bandExport')}
        </button>
      </div>
      {!trace && <div className="empty-state">{label(t, 'bandRequirementPending')}</div>}
      {trace && (
        <>
          <div className="band-summary">
            <span>{trace.band_configured ? label(t, 'bandConfigured') : label(t, 'bandLocal')}</span>
            <strong>{trace.minimum_agent_requirement_met ? label(t, 'bandRequirementMet') : label(t, 'bandRequirementPending')}</strong>
          </div>
          <div className="band-roles">
            {trace.agent_roles?.map((role) => (
              <article key={role.name}>
                <strong>{role.band_mention}</strong>
                <p>{role.responsibility}</p>
              </article>
            ))}
          </div>
          <div className="band-steps">
            {trace.collaboration_steps?.map((step) => (
              <article key={step.order}>
                <span>{step.order}</span>
                <div>
                  <strong>{step.from_agent} → {step.to_agent}</strong>
                  <p>{step.handoff}</p>
                  <small>{step.expected_output}</small>
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function ReportView({ report, setReport, intraopEvents, postopPlan, onConfirm, onExport, busy, t }) {
  if (!report) {
    return (
      <section className="panel empty-report">
        <Activity size={28} />
        <h3>{t.emptyReportTitle}</h3>
        <p>{t.emptyReportBody}</p>
      </section>
    );
  }
  const patientContext = report.patient_context || {};
  const riskFlags = report.risk_flags || [];
  const ecgFindings = report.ecg_findings || [];
  const labFindings = report.lab_findings || [];
  const missingInformation = report.missing_information || [];
  const followUpQuestions = report.suggested_follow_up_questions || [];
  const additionalChecks = report.suggested_additional_checks || [];
  const monitoringFocus = report.perioperative_monitoring_focus || [];
  const sourceFindings = report.source_findings || [];
  const postopDraft = postopPlan?.surveillance_focus?.length
    ? postopPlan.surveillance_focus
    : (report.postop_surveillance_plan || []);

  return (
    <section className="report">
      <div className="report-header">
        <div>
          <p className="eyebrow">{t.reportEyebrow}</p>
          <h3>{t.reportTitle}</h3>
        </div>
        <div className="report-actions">
          <button className="secondary icon-button" onClick={onExport} disabled={busy}>
            <Download size={17} />
            {t.exportMarkdown}
          </button>
          <button className="primary" onClick={onConfirm} disabled={busy}>{t.saveReview}</button>
        </div>
      </div>

      <div className="report-grid">
        <ReportBlock title={t.context}>
          <div className="summary-grid">
            <SummaryItem label={t.age} value={patientContext.age} t={t} />
            <SummaryItem label={t.sex} value={patientContext.sex} t={t} />
            <SummaryItem label={t.bodySize} value={patientContext.height_weight_bmi} t={t} />
            <SummaryItem label={t.plannedSurgery} value={patientContext.planned_surgery} t={t} />
            <SummaryItem label={t.urgency} value={patientContext.urgency} t={t} />
          </div>
          <TagRow label={t.history} items={patientContext.history} t={t} />
          <TagRow label={t.medications} items={patientContext.medications} t={t} />
          <TagRow label={t.allergyAnesthesia} items={[...(patientContext.allergies || []), ...(patientContext.anesthesia_history || [])]} t={t} />
        </ReportBlock>

        <ReportBlock title={t.riskStratification}>
          <p>{report.asa_suggestion}</p>
          <p>{report.rcri_summary}</p>
          <p>{report.stop_bang_summary}</p>
          <p>{report.ponv_summary}</p>
        </ReportBlock>

        <ReportBlock title={t.riskFlags}>
          {riskFlags.map((flag, index) => (
            <div key={`${flag.name}-${index}`} className={`risk ${flag.severity}`}>
              <strong>{flag.name}</strong>
              <span>{flag.severity}</span>
              <p>{flag.rationale}</p>
            </div>
          ))}
        </ReportBlock>

        <ReportBlock title={t.ecgFindings}>
          {ecgFindings.length === 0 && <p>{t.noEcg}</p>}
          {ecgFindings.map((ecg, index) => (
            <div key={`${ecg.source}-${index}`} className="ecg-box">
              <strong>{ecg.source}</strong>
              <small>{ecg.analyzer_name || 'rule_based_text_ecg_adapter'} · {ecg.adapter_version || '0.1.0'} · {ecg.confidence || 'medium'} confidence</small>
              <p>
                {t.rhythm}: {ecg.rhythm || t.notExtracted}; {t.heartRate}: {ecg.heart_rate || t.notExtracted};
                PR: {ecg.pr_interval || t.notExtracted}; QRS: {ecg.qrs_duration || t.notExtracted};
                QTc: {ecg.qtc || t.notExtracted}
              </p>
              <TagRow label={t.stt} items={ecg.st_t_changes} t={t} />
              <TagRow label={t.conduction} items={ecg.conduction_findings} t={t} />
              <TagRow label={t.arrhythmia} items={ecg.arrhythmia_findings} t={t} />
              {ecg.anesthesia_risk_notes.map((note) => <small key={note}>{note}</small>)}
              {ecg.missing_info.length > 0 && <small>{t.missing}: {ecg.missing_info.join('；')}</small>}
            </div>
          ))}
        </ReportBlock>

        <ReportBlock title={t.labs}>
          {!labFindings.length && <p>{t.noLabs}</p>}
          <div className="lab-table">
            {labFindings.map((lab, index) => (
              <div key={`${lab.name}-${index}`} className={`lab-row ${lab.interpretation}`}>
                <strong>{lab.name}</strong>
                <span>{lab.value}{lab.unit || ''}</span>
                <em>{lab.interpretation}</em>
                <small>{lab.anesthesia_relevance}</small>
              </div>
            ))}
          </div>
        </ReportBlock>

        <ReportBlock title={t.missingInfo}>
          <ul>{missingInformation.map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title={t.followUp}>
          <ul>{followUpQuestions.map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title={t.checksMonitoring}>
          <ul>{[...additionalChecks, ...monitoringFocus].map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title={label(t, 'intraopTitle')}>
          {!intraopEvents.length && <p>{label(t, 'noEvents')}</p>}
          {intraopEvents.map((event) => (
            <div key={event.id} className={`event-card compact ${event.severity}`}>
              <div>
                <strong>{event.event_type}</strong>
                <span>{event.severity}</span>
              </div>
              <p>{event.description}</p>
            </div>
          ))}
        </ReportBlock>

        <ReportBlock title={label(t, 'postopTitle')}>
          {!postopDraft.length && <p>{label(t, 'noPostopPlan')}</p>}
          <ul>{postopDraft.map((item) => <li key={item}>{item}</li>)}</ul>
          {postopPlan?.suggested_checks?.length > 0 && <TagRow label={label(t, 'postopChecks')} items={postopPlan.suggested_checks} t={t} />}
          {postopPlan?.escalation_triggers?.length > 0 && <TagRow label={label(t, 'escalationTriggers')} items={postopPlan.escalation_triggers} t={t} />}
        </ReportBlock>

        <ReportBlock title={t.evidence}>
          {!sourceFindings.length && <p>{t.noEvidence}</p>}
          {sourceFindings.slice(0, 12).map((finding, index) => (
            <div className="finding-row" key={`${finding.source}-${finding.fact}-${index}`}>
              <strong>{finding.fact}</strong>
              <small>{finding.source} · {finding.confidence}</small>
            </div>
          ))}
        </ReportBlock>
      </div>

      <label className="field clinician-notes">
        {t.clinicianNotes}
        <textarea
          value={report.clinician_notes || ''}
          onChange={(event) => setReport({ ...report, clinician_notes: event.target.value })}
          placeholder={t.clinicianPlaceholder}
        />
      </label>

      <div className="safety">{report.safety_notice}</div>
      <div className="safety">{label(t, 'outputSafetyText')}</div>
    </section>
  );
}

function ReportBlock({ title, children }) {
  return (
    <section className="report-block">
      <h4>{title}</h4>
      {children}
    </section>
  );
}

function SummaryItem({ label, value, t }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value || t.needsConfirmation}</strong>
    </div>
  );
}

function TagRow({ label, items, t }) {
  const values = items?.filter(Boolean) || [];
  return (
    <div className="tag-row">
      <span>{label}</span>
      <div>
        {values.length ? values.map((item) => <em key={item}>{item}</em>) : <small>{t.toSupplement}</small>}
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
