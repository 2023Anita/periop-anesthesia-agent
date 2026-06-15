const now = '2026-06-15T05:45:00.000Z';

const caseRecord = {
  id: 'demo-elderly-ortho',
  title: 'Synthetic elderly orthopedic high-risk case',
  status: 'assessed',
  created_at: now,
  updated_at: now,
};

const documentRecord = {
  id: 'doc-ecg-labs',
  case_id: caseRecord.id,
  filename: 'sample-preop-ecg.txt',
  modality: 'ecg',
  extracted_text:
    '82-year-old female for urgent hip fracture fixation. History: hypertension, coronary artery disease, chronic kidney disease. ECG: atrial fibrillation, HR 112 bpm, QTc 485 ms, nonspecific ST-T changes. Labs: Hb 88 g/L, K 3.2 mmol/L, creatinine 168 umol/L, platelets 118 x10^9/L.',
  extraction_notes: ['Loaded from the synthetic public demo sample.'],
  created_at: now,
};

const report = {
  case_id: caseRecord.id,
  generated_at: now,
  patient_context: {
    age: '82',
    sex: 'Female',
    height_weight_bmi: null,
    planned_surgery: 'Urgent hip fracture fixation',
    urgency: 'Urgent',
    history: ['Hypertension', 'Coronary artery disease', 'Chronic kidney disease'],
    medications: ['Antihypertensive therapy reported; antithrombotic history requires confirmation'],
    allergies: [],
    anesthesia_history: [],
  },
  source_findings: [
    { source: 'sample-preop-ecg.txt', fact: 'Urgent orthopedic surgery in an elderly patient', confidence: 'high' },
    { source: 'sample-preop-ecg.txt', fact: 'Atrial fibrillation with tachycardia and QTc prolongation', confidence: 'high' },
    { source: 'sample-preop-ecg.txt', fact: 'Anemia, renal dysfunction, hypokalemia, and thrombocytopenia', confidence: 'high' },
  ],
  ecg_findings: [
    {
      source: 'sample-preop-ecg.txt',
      analyzer_name: 'rule_based_text_ecg_adapter',
      adapter_version: '0.1.0',
      confidence: 'medium',
      heart_rate: '112 bpm',
      rhythm: 'Atrial fibrillation',
      pr_interval: null,
      qrs_duration: null,
      qtc: '485 ms',
      st_t_changes: ['Nonspecific ST-T changes'],
      conduction_findings: [],
      arrhythmia_findings: ['Atrial fibrillation with rapid ventricular response clue'],
      anesthesia_risk_notes: [
        'QTc prolongation requires focused clinician review of electrolytes and QT-prolonging medications.',
        'Atrial fibrillation and ST-T changes require correlation with symptoms, troponin, echo, or cardiology input.',
      ],
      missing_info: ['Symptoms, prior ECG, troponin, echocardiography status, anticoagulation history'],
      clinician_review_required: true,
    },
  ],
  lab_findings: [
    { name: 'Hemoglobin', value: '88', unit: 'g/L', interpretation: 'low', anesthesia_relevance: 'Anemia may affect oxygen delivery and transfusion planning.', source: 'sample-preop-ecg.txt' },
    { name: 'Potassium', value: '3.2', unit: 'mmol/L', interpretation: 'low', anesthesia_relevance: 'Hypokalemia can increase arrhythmia risk.', source: 'sample-preop-ecg.txt' },
    { name: 'Creatinine', value: '168', unit: 'umol/L', interpretation: 'high', anesthesia_relevance: 'Renal dysfunction affects fluid, medication, and postoperative monitoring decisions.', source: 'sample-preop-ecg.txt' },
    { name: 'Platelets', value: '118', unit: 'x10^9/L', interpretation: 'low', anesthesia_relevance: 'Platelet abnormality may affect bleeding and neuraxial anesthesia review.', source: 'sample-preop-ecg.txt' },
  ],
  risk_flags: [
    {
      name: 'Cardiovascular perioperative risk',
      severity: 'high',
      rationale: 'Elderly urgent orthopedic surgery with coronary disease clues, atrial fibrillation, tachycardia, QTc prolongation, and ST-T changes.',
      evidence: ['Atrial fibrillation HR 112', 'QTc 485 ms', 'Coronary artery disease history'],
      clinician_review_required: true,
    },
    {
      name: 'Renal and electrolyte risk',
      severity: 'high',
      rationale: 'Creatinine elevation and hypokalemia may affect perioperative medication, fluid, and arrhythmia risk.',
      evidence: ['Creatinine 168 umol/L', 'K 3.2 mmol/L'],
      clinician_review_required: true,
    },
    {
      name: 'Bleeding / oxygen-delivery risk',
      severity: 'medium',
      rationale: 'Anemia and thrombocytopenia require clinician review before anesthesia planning.',
      evidence: ['Hb 88 g/L', 'Platelets 118 x10^9/L'],
      clinician_review_required: true,
    },
  ],
  asa_suggestion: 'ASA draft: possibly class III-IV; the anesthesiologist must confirm using functional status, urgency, and source records.',
  rcri_summary: 'RCRI draft: cardiovascular and renal risk clues present; confirm with procedure type, creatinine, and cardiac status.',
  stop_bang_summary: 'STOP-Bang draft: cannot complete without BMI, neck circumference, snoring, and witnessed apnea history.',
  ponv_summary: 'PONV draft: supplement prior PONV, motion sickness, smoking history, and postoperative opioid plan.',
  missing_information: [
    'Confirm anticoagulant or antiplatelet use and last dose timing.',
    'Confirm functional capacity, chest pain, dyspnea, syncope, and heart failure symptoms.',
    'Confirm airway assessment, aspiration risk, and prior anesthesia complications.',
    'Clarify recent troponin, echocardiography, and cardiology recommendations when clinically indicated.',
  ],
  suggested_follow_up_questions: [
    'What is the exact urgency and expected blood loss of the orthopedic procedure?',
    'Is atrial fibrillation chronic or new, and is rate control adequate?',
    'Are electrolyte correction, renal function review, and anemia plan documented?',
  ],
  suggested_additional_checks: [
    'Repeat electrolytes after correction if clinically indicated.',
    'CBC and coagulation review before anesthesia technique selection.',
    'ECG comparison, troponin, echo, or cardiology input as decided by the clinical team.',
  ],
  perioperative_monitoring_focus: [
    'Hemodynamic stability, rhythm, oxygenation, bleeding, urine output, and delirium risk.',
    'PACU handoff should highlight ECG/lab abnormalities and urgent orthopedic context.',
  ],
  safety_notice:
    'This report is an anesthesiologist-facing pre-op assessment draft. It is not an autonomous diagnosis, treatment, medication, anesthetic plan, or final surgery-clearance decision.',
  review_status: 'draft',
  clinician_notes: '',
  postop_surveillance_plan: [
    'Focused PACU rhythm, blood pressure, oxygenation, pain, delirium, bleeding, and urine-output surveillance.',
    'Clinician-directed postoperative ECG, CBC, renal function, and electrolytes if risk or events persist.',
  ],
};

const defaultEvent = {
  id: 'event-rapid-af',
  case_id: caseRecord.id,
  event_type: 'arrhythmia',
  severity: 'high',
  description: 'Intraoperative hypotension with rapid atrial fibrillation during positioning.',
  observed_at: now,
  clinician_action_summary: 'Team documented hemodynamic support, rhythm review, and PACU escalation awareness.',
  created_at: now,
};

function buildPostopPlan(events = [defaultEvent]) {
  const eventFocus = events.map((event) => `${event.severity} ${event.event_type}: ${event.description}`);
  return {
    case_id: caseRecord.id,
    generated_at: now,
    surveillance_focus: [
      'Cardiac rhythm and ischemia surveillance because ECG risk clues and intraoperative arrhythmia were documented.',
      'Hemodynamics, oxygenation, bleeding, delirium, renal function, and electrolyte status.',
      ...eventFocus,
    ],
    suggested_checks: [
      'Clinician-directed ECG or telemetry if rhythm concern persists.',
      'CBC, renal function, potassium, and magnesium reassessment according to local protocol.',
      'Escalation to higher monitoring level if instability persists.',
    ],
    escalation_triggers: [
      'Persistent hypotension, hypoxemia, chest pain, altered mental status, active bleeding, or new/worsening arrhythmia.',
    ],
    safety_notice: report.safety_notice,
  };
}

function buildBandTrace(events = [defaultEvent]) {
  return {
    case_id: caseRecord.id,
    generated_at: now,
    band_configured: false,
    room_id: null,
    minimum_agent_requirement_met: true,
    agent_roles: [
      { name: 'Periop Intake Agent', band_mention: '@Periop Intake Agent', responsibility: 'Summarize source documents and missing information.' },
      { name: 'ECG Lab Risk Agent', band_mention: '@ECG Lab Risk Agent', responsibility: 'Review ECG and lab findings for anesthesia-relevant risk clues.' },
      { name: 'Periop Safety Reviewer', band_mention: '@Periop Safety Reviewer', responsibility: 'Audit output for blocked medical decision categories.' },
      { name: 'Postop Surveillance Agent', band_mention: '@Postop Surveillance Agent', responsibility: 'Convert pre-op risks and intra-op events into a postoperative surveillance draft.' },
    ],
    collaboration_steps: [
      {
        order: 1,
        from_agent: 'Clinician Workbench',
        to_agent: 'Periop Intake Agent',
        handoff: 'Synthetic pre-op note, ECG text, lab snippets, and surgery context were structured for review.',
        shared_context: ['Urgent orthopedic surgery', 'Elderly patient', 'ECG/lab abnormalities'],
        expected_output: 'Case summary and missing-data list',
        status: 'local_trace',
      },
      {
        order: 2,
        from_agent: 'Periop Intake Agent',
        to_agent: 'ECG Lab Risk Agent',
        handoff: 'ECG and laboratory clues were routed to focused review.',
        shared_context: ['Atrial fibrillation', 'QTc prolongation', 'Anemia', 'Renal dysfunction', 'Hypokalemia'],
        expected_output: 'Anesthesia-relevant risk clues and follow-up checks',
        status: 'local_trace',
      },
      {
        order: 3,
        from_agent: 'ECG Lab Risk Agent',
        to_agent: 'Periop Safety Reviewer',
        handoff: 'Draft risk assessment was checked against blocked medical decision categories.',
        shared_context: ['No autonomous clearance', 'No medication dosing', 'No emergency commands'],
        expected_output: 'Clinician-safe draft boundary review',
        status: 'local_trace',
      },
      {
        order: 4,
        from_agent: 'Periop Safety Reviewer',
        to_agent: 'Postop Surveillance Agent',
        handoff: `Postoperative surveillance draft created using ${events.length} intraoperative event(s).`,
        shared_context: ['PACU monitoring', 'Rhythm surveillance', 'Renal/electrolyte follow-up'],
        expected_output: 'Postoperative surveillance plan for clinician confirmation',
        status: 'local_trace',
      },
    ],
    audit_notes: [
      'Static public demo uses synthetic data only.',
      'Live Band credentials are optional and intentionally not embedded in the browser demo.',
    ],
  };
}

function safetyCheck(text) {
  const lower = text.toLowerCase();
  const blocked = ['clear', 'dose', 'emergency', 'medication', 'patient advice'].some((term) => lower.includes(term));
  return {
    allowed: !blocked,
    category: blocked ? 'blocked_medical_decision' : 'clinician_review_draft',
    reason: blocked
      ? 'The request may imply clearance, dosing, emergency action, medication decisions, or patient-facing advice.'
      : 'The text can be handled as a clinician-reviewed draft.',
    safe_response: blocked
      ? 'The system can organize evidence and missing information, but the anesthesiologist must make final clinical decisions.'
      : 'It can continue to be displayed as a clinician-reviewed draft.',
    matched_terms: blocked ? ['clearance/dosing/emergency boundary'] : [],
  };
}

let cases = [];
let documents = [];
let currentReport = null;
let events = [];

export function isStaticDemoMode() {
  return import.meta.env.VITE_STATIC_DEMO === 'true';
}

export async function staticDemoRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();

  if (path === '/api/system/status') {
    return {
      deterministic_workflow_available: true,
      agents_sdk_refinement_configured: true,
      band_collaboration_configured: false,
      eval_case_count: 4,
      safety_boundary_categories: ['clearance', 'dosing', 'emergency', 'medication_decision', 'patient_advice'],
    };
  }

  if (path === '/api/cases' && method === 'GET') return cases;
  if (path === '/api/cases' && method === 'POST') {
    cases = [{ ...caseRecord, id: `demo-${Date.now()}`, title: 'Static demo case', status: 'draft' }];
    documents = [];
    currentReport = null;
    events = [];
    return cases[0];
  }

  if (path === '/api/demo/sample-case' && method === 'POST') {
    cases = [caseRecord];
    documents = [documentRecord];
    currentReport = report;
    events = [defaultEvent];
    return { case: caseRecord, documents, report };
  }

  if (path.endsWith('/documents') && method === 'GET') return documents;
  if (path.endsWith('/documents/text') && method === 'POST') {
    const payload = JSON.parse(options.body || '{}');
    const doc = {
      id: `doc-${Date.now()}`,
      case_id: caseRecord.id,
      filename: payload.filename || 'manual-input.txt',
      modality: payload.modality || 'clinical_note',
      extracted_text: payload.text || '',
      extraction_notes: ['Static demo manual input.'],
      created_at: now,
    };
    documents = [...documents, doc];
    return doc;
  }
  if (path.endsWith('/documents') && method === 'POST') return documentRecord;
  if (path.endsWith('/analyze/preop') && method === 'POST') {
    currentReport = report;
    cases = [{ ...caseRecord, status: 'assessed' }];
    return currentReport;
  }
  if (path.endsWith('/report') && method === 'GET') {
    if (!currentReport) throw new Error('No report has been generated yet.');
    return currentReport;
  }
  if (path.endsWith('/report/clinician-review') && method === 'PATCH') {
    currentReport = { ...report, review_status: 'clinician_confirmed' };
    return currentReport;
  }
  if (path.endsWith('/intraop-events') && method === 'GET') return events;
  if (path.endsWith('/intraop-events') && method === 'POST') {
    const payload = JSON.parse(options.body || '{}');
    const event = {
      id: `event-${Date.now()}`,
      case_id: caseRecord.id,
      event_type: payload.event_type || 'other',
      severity: payload.severity || 'medium',
      description: payload.description || '',
      clinician_action_summary: payload.clinician_action_summary || '',
      observed_at: payload.observed_at || now,
      created_at: now,
    };
    events = [...events, event];
    cases = [{ ...caseRecord, status: 'intraop_event_logged' }];
    return event;
  }
  if (path.endsWith('/postop-plan') && method === 'GET') return buildPostopPlan(events);
  if (path.endsWith('/band-collaboration') && method === 'POST') return buildBandTrace(events);
  if (path === '/api/safety/check' && method === 'POST') {
    const payload = JSON.parse(options.body || '{}');
    return safetyCheck(payload.text || '');
  }

  throw new Error(`Static demo route is not implemented: ${method} ${path}`);
}

export function staticDemoMarkdown(kind) {
  if (kind === 'band') {
    return '# Band collaboration trace\n\nThis static demo shows four specialized agent roles, handoffs, safety review, and postoperative surveillance planning using synthetic data only.\n';
  }
  return '# Perioperative assessment draft\n\nSynthetic static demo export. Clinician review is required before any clinical decision.\n';
}
