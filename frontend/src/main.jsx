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
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8010';

async function requestJSON(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  const contentType = res.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    throw new Error(payload?.detail || payload || `Request failed with status ${res.status}`);
  }
  return payload;
}

function App() {
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
      setError(err.message || '操作失败，请检查后端服务是否正在运行。');
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
    await runOperation('正在创建病例...', async () => {
      const data = await requestJSON('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: `术前评估 ${new Date().toLocaleString()}` }),
      });
      setActiveCase(data);
      await loadCases();
      setMessage('新病例已创建。');
    });
  }

  async function loadSampleCase() {
    await runOperation('正在加载样例病例并生成报告...', async () => {
      const data = await requestJSON('/api/demo/sample-case', { method: 'POST' });
      setActiveCase(data.case);
      setDocuments(data.documents);
      setReport(data.report);
      await loadCases();
      setMessage('Synthetic sample case loaded. The draft report is ready for review.');
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
    await runOperation('正在加入病例资料...', async () => {
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
      setMessage('文本资料已加入病例。');
    });
  }

  async function uploadFile(event) {
    const file = event.target.files?.[0];
    if (!activeCase || !file) return;
    await runOperation('正在上传并抽取资料...', async () => {
      const form = new FormData();
      form.append('file', file);
      form.append('modality', modality);
      await requestJSON(`/api/cases/${activeCase.id}/documents`, {
        method: 'POST',
        body: form,
      });
      await loadDocuments(activeCase.id);
      setMessage('文件已上传并抽取。');
      event.target.value = '';
    });
  }

  async function runAssessment() {
    if (!activeCase) return;
    await runOperation('正在运行术前评估 workflow...', async () => {
      const data = await requestJSON(`/api/cases/${activeCase.id}/analyze/preop`, { method: 'POST' });
      setReport(data);
      await loadCases();
      setMessage('术前麻醉评估草案已生成。');
    });
  }

  async function confirmReport() {
    if (!activeCase || !report) return;
    await runOperation('正在保存医生确认...', async () => {
      const data = await requestJSON(`/api/cases/${activeCase.id}/report/clinician-review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clinician_notes: report.clinician_notes || '',
          review_status: 'clinician_confirmed',
        }),
      });
      setReport(data);
      setMessage('医生确认状态已保存。');
    });
  }

  async function checkSafety() {
    if (!safetyText.trim()) return;
    await runOperation('正在检查安全边界...', async () => {
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
    await runOperation('正在导出 Markdown...', async () => {
      const res = await fetch(`${API_BASE}/api/cases/${activeCase.id}/report/export.md`);
      if (!res.ok) throw new Error('报告导出失败。');
      const markdown = await res.text();
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `periop-assessment-${activeCase.id}.md`;
      link.click();
      URL.revokeObjectURL(url);
      setMessage('Markdown report exported.');
    });
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <HeartPulse size={26} />
          <div>
            <h1>Periop Anesthesia Agent</h1>
            <p>Doctor-reviewed clinical AI template</p>
          </div>
        </div>
        <button className="primary" onClick={createCase} disabled={busy}>新建病例</button>
        <button className="sample-button" onClick={loadSampleCase} disabled={busy}>
          <PlayCircle size={17} />
          Load sample case
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
          {cases.length === 0 && <p className="sidebar-empty">No cases yet. Start with the sample.</p>}
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">LOCAL CLINICAL AI AGENT TEMPLATE</p>
            <h2>{activeCase?.title || '请先创建病例'}</h2>
          </div>
          <div className="status-strip">
            <Stat icon={<FileText size={18} />} label="资料" value={documents.length} />
            <Stat icon={<AlertTriangle size={18} />} label="高风险" value={highRiskCount} />
            <Stat icon={<CheckCircle2 size={18} />} label="状态" value={report?.review_status || 'draft'} />
          </div>
        </header>

        <div className="notice">
          <AlertTriangle size={18} />
          Doctor-reviewed draft only. No autonomous diagnosis, dosing, emergency instructions, or surgery clearance.
        </div>

        {busy && <div className="busy-bar">{operation || '处理中...'}</div>}
        {message && <div className="toast">{message}</div>}
        {error && <div className="error-banner">{error}</div>}

        <div className="grid">
          <section className="panel">
            <div className="panel-title">
              <Upload size={20} />
              <h3>资料上传与输入</h3>
            </div>
            <label className="field">
              资料类型
              <select value={modality} onChange={(event) => setModality(event.target.value)}>
                <option value="clinical_note">术前病历</option>
                <option value="ecg">心电图</option>
                <option value="lab">化验单</option>
                <option value="imaging">影像报告</option>
                <option value="medication">用药</option>
                <option value="airway">气道评估</option>
                <option value="other">其他</option>
              </select>
            </label>
            <label className="file-drop">
              <input type="file" onChange={uploadFile} disabled={!activeCase || busy} />
              上传 PDF / Word / 图片 / TXT
            </label>
            <textarea
              value={manualText}
              onChange={(event) => setManualText(event.target.value)}
              placeholder="粘贴术前病历、心电图报告、化验单文字..."
            />
            <button className="secondary" onClick={addManualText} disabled={!activeCase || busy || !manualText.trim()}>
              加入病例资料
            </button>
          </section>

          <section className="panel">
            <div className="panel-title">
              <FileText size={20} />
              <h3>抽取预览</h3>
            </div>
            <div className="doc-list">
              {documents.length === 0 && <div className="empty-state">No documents yet. Load the sample case or add pre-op materials.</div>}
              {documents.map((doc) => (
                <article key={doc.id} className="doc-card">
                  <div>
                    <strong>{doc.filename}</strong>
                    <span>{doc.modality}</span>
                  </div>
                  <p>{doc.extracted_text || '未抽取到文本。'}</p>
                  {doc.extraction_notes?.map((note) => <small key={note}>{note}</small>)}
                </article>
              ))}
            </div>
            <button className="primary" onClick={runAssessment} disabled={!activeCase || busy || documents.length === 0}>
              生成术前麻醉评估草案
            </button>
          </section>
        </div>

        <section className="panel safety-panel">
          <div className="panel-title">
            <AlertTriangle size={20} />
            <h3>医疗安全边界检查</h3>
          </div>
          <div className="safety-check-row">
            <textarea
              value={safetyText}
              onChange={(event) => setSafetyText(event.target.value)}
              placeholder="试试：这个患者能不能手术？诱导药给多少剂量？"
            />
            <button className="secondary" onClick={checkSafety} disabled={busy || !safetyText.trim()}>
              检查边界
            </button>
          </div>
          {safetyResult && (
            <div className={safetyResult.allowed ? 'safety-result allowed' : 'safety-result blocked'}>
              <strong>{safetyResult.allowed ? '允许：医生辅助任务' : '拦截：超出安全边界'}</strong>
              <span>{safetyResult.category}</span>
              <p>{safetyResult.reason}</p>
              <small>{safetyResult.safe_response}</small>
            </div>
          )}
        </section>

        <ReportView report={report} setReport={setReport} onConfirm={confirmReport} onExport={exportReport} busy={busy} />
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

function ReportView({ report, setReport, onConfirm, onExport, busy }) {
  if (!report) {
    return (
      <section className="panel empty-report">
        <Activity size={28} />
        <h3>等待生成评估草案</h3>
        <p>Load the synthetic sample or add pre-op materials to generate a structured doctor-reviewed draft.</p>
      </section>
    );
  }

  return (
    <section className="report">
      <div className="report-header">
        <div>
          <p className="eyebrow">术前麻醉评估草案</p>
          <h3>需麻醉医生复核确认</h3>
        </div>
        <div className="report-actions">
          <button className="secondary icon-button" onClick={onExport} disabled={busy}>
            <Download size={17} />
            Export Markdown
          </button>
          <button className="primary" onClick={onConfirm} disabled={busy}>保存医生确认</button>
        </div>
      </div>

      <div className="report-grid">
        <ReportBlock title="病例摘要">
          <div className="summary-grid">
            <SummaryItem label="年龄" value={report.patient_context.age} />
            <SummaryItem label="性别" value={report.patient_context.sex} />
            <SummaryItem label="身高/体重/BMI" value={report.patient_context.height_weight_bmi} />
            <SummaryItem label="拟行手术" value={report.patient_context.planned_surgery} />
            <SummaryItem label="手术属性" value={report.patient_context.urgency} />
          </div>
          <TagRow label="既往史" items={report.patient_context.history} />
          <TagRow label="用药" items={report.patient_context.medications} />
          <TagRow label="过敏/麻醉史" items={[...report.patient_context.allergies, ...report.patient_context.anesthesia_history]} />
        </ReportBlock>

        <ReportBlock title="风险分层">
          <p>{report.asa_suggestion}</p>
          <p>{report.rcri_summary}</p>
          <p>{report.stop_bang_summary}</p>
          <p>{report.ponv_summary}</p>
        </ReportBlock>

        <ReportBlock title="主要风险标签">
          {report.risk_flags.map((flag, index) => (
            <div key={`${flag.name}-${index}`} className={`risk ${flag.severity}`}>
              <strong>{flag.name}</strong>
              <span>{flag.severity}</span>
              <p>{flag.rationale}</p>
            </div>
          ))}
        </ReportBlock>

        <ReportBlock title="心电图发现">
          {report.ecg_findings.length === 0 && <p>未见可结构化识别的心电图资料。</p>}
          {report.ecg_findings.map((ecg, index) => (
            <div key={`${ecg.source}-${index}`} className="ecg-box">
              <strong>{ecg.source}</strong>
              <p>节律：{ecg.rhythm || '未抽取'}；心率：{ecg.heart_rate || '未抽取'}；PR：{ecg.pr_interval || '未抽取'}；QRS：{ecg.qrs_duration || '未抽取'}；QTc：{ecg.qtc || '未抽取'}</p>
              <TagRow label="ST-T/缺血" items={ecg.st_t_changes} />
              <TagRow label="传导" items={ecg.conduction_findings} />
              <TagRow label="心律失常" items={ecg.arrhythmia_findings} />
              {ecg.anesthesia_risk_notes.map((note) => <small key={note}>{note}</small>)}
              {ecg.missing_info.length > 0 && <small>缺失：{ecg.missing_info.join('；')}</small>}
            </div>
          ))}
        </ReportBlock>

        <ReportBlock title="关键化验">
          {!report.lab_findings?.length && <p>未见可结构化识别的关键化验。</p>}
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

        <ReportBlock title="缺失信息">
          <ul>{report.missing_information.map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title="建议追问">
          <ul>{report.suggested_follow_up_questions.map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title="补充检查与监测重点">
          <ul>{[...report.suggested_additional_checks, ...report.perioperative_monitoring_focus].map((item) => <li key={item}>{item}</li>)}</ul>
        </ReportBlock>

        <ReportBlock title="证据线索">
          {!report.source_findings?.length && <p>暂无结构化证据线索。</p>}
          {report.source_findings?.slice(0, 12).map((finding, index) => (
            <div className="finding-row" key={`${finding.source}-${finding.fact}-${index}`}>
              <strong>{finding.fact}</strong>
              <small>{finding.source} · {finding.confidence}</small>
            </div>
          ))}
        </ReportBlock>
      </div>

      <label className="field clinician-notes">
        医生备注与确认
        <textarea
          value={report.clinician_notes || ''}
          onChange={(event) => setReport({ ...report, clinician_notes: event.target.value })}
          placeholder="麻醉医生在这里修改、补充并确认..."
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

function SummaryItem({ label, value }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value || '待确认'}</strong>
    </div>
  );
}

function TagRow({ label, items }) {
  const values = items?.filter(Boolean) || [];
  return (
    <div className="tag-row">
      <span>{label}</span>
      <div>
        {values.length ? values.map((item) => <em key={item}>{item}</em>) : <small>待补充</small>}
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
