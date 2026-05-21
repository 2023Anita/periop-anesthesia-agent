import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  HeartPulse,
  PlayCircle,
  Upload,
} from 'lucide-react';
import { LANGUAGES, TRANSLATIONS } from './i18n';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8010';
const DEFAULT_LANGUAGE = 'en';
const LANGUAGE_STORAGE_KEY = 'periop-agent-language';
const MODALITY_OPTIONS = ['clinical_note', 'ecg', 'lab', 'imaging', 'medication', 'airway', 'other'];

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
  const [manualText, setManualText] = useState('');
  const [modality, setModality] = useState('clinical_note');
  const [safetyText, setSafetyText] = useState('这个患者能不能手术？');
  const [safetyResult, setSafetyResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [operation, setOperation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  useEffect(() => {
    loadCases().catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (activeCase) {
      loadDocuments(activeCase.id).catch((err) => setError(err.message));
      loadReport(activeCase.id);
    }
  }, [activeCase]);

  const highRiskCount = useMemo(() => {
    return report?.risk_flags?.filter((flag) => ['high', 'critical'].includes(flag.severity)).length || 0;
  }, [report]);

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
      setMessage(t.reviewSaved);
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
            <Stat icon={<CheckCircle2 size={18} />} label={t.statusStat} value={report?.review_status || 'draft'} />
          </div>
        </header>

        <div className="notice">
          <AlertTriangle size={18} />
          {t.notice}
        </div>

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

        <ReportView
          report={report}
          setReport={setReport}
          onConfirm={confirmReport}
          onExport={exportReport}
          busy={busy}
          t={t}
        />
      </section>
    </main>
  );
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

function ReportView({ report, setReport, onConfirm, onExport, busy, t }) {
  if (!report) {
    return (
      <section className="panel empty-report">
        <Activity size={28} />
        <h3>{t.emptyReportTitle}</h3>
        <p>{t.emptyReportBody}</p>
      </section>
    );
  }

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
            <SummaryItem label={t.age} value={report.patient_context.age} t={t} />
            <SummaryItem label={t.sex} value={report.patient_context.sex} t={t} />
            <SummaryItem label={t.bodySize} value={report.patient_context.height_weight_bmi} t={t} />
            <SummaryItem label={t.plannedSurgery} value={report.patient_context.planned_surgery} t={t} />
            <SummaryItem label={t.urgency} value={report.patient_context.urgency} t={t} />
          </div>
          <TagRow label={t.history} items={report.patient_context.history} t={t} />
          <TagRow label={t.medications} items={report.patient_context.medications} t={t} />
          <TagRow label={t.allergyAnesthesia} items={[...report.patient_context.allergies, ...report.patient_context.anesthesia_history]} t={t} />
        </ReportBlock>

        <ReportBlock title={t.riskStratification}>
          <p>{report.asa_suggestion}</p>
          <p>{report.rcri_summary}</p>
          <p>{report.stop_bang_summary}</p>
          <p>{report.ponv_summary}</p>
        </ReportBlock>

        <ReportBlock title={t.riskFlags}>
          {report.risk_flags.map((flag, index) => (
            <div key={`${flag.name}-${index}`} className={`risk ${flag.severity}`}>
              <strong>{flag.name}</strong>
              <span>{flag.severity}</span>
              <p>{flag.rationale}</p>
            </div>
          ))}
        </ReportBlock>

        <ReportBlock title={t.ecgFindings}>
          {report.ecg_findings.length === 0 && <p>{t.noEcg}</p>}
          {report.ecg_findings.map((ecg, index) => (
            <div key={`${ecg.source}-${index}`} className="ecg-box">
              <strong>{ecg.source}</strong>
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
          {!report.lab_findings?.length && <p>{t.noLabs}</p>}
          <div className="lab-table">
            {report.lab_findings?.map((lab, index) => (
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
          <ul>{report.missing_information.map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title={t.followUp}>
          <ul>{report.suggested_follow_up_questions.map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title={t.checksMonitoring}>
          <ul>{[...report.suggested_additional_checks, ...report.perioperative_monitoring_focus].map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title={t.evidence}>
          {!report.source_findings?.length && <p>{t.noEvidence}</p>}
          {report.source_findings?.slice(0, 12).map((finding, index) => (
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
