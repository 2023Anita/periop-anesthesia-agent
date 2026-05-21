from __future__ import annotations

from app.schemas.periop import ECGFinding, LabFinding, PatientContext, PreopAssessmentReport, RiskFlag


def render_report_markdown(report: PreopAssessmentReport) -> str:
    sections = [
        f"# Perioperative Anesthesia Assessment Draft\n",
        f"- Case ID: `{report.case_id}`",
        f"- Generated at: `{report.generated_at.isoformat()}`",
        f"- Review status: `{report.review_status.value}`",
        "",
        "## Safety Notice",
        report.safety_notice,
        "",
        "## Patient Context",
        _render_context(report.patient_context),
        "",
        "## Risk Stratification",
        f"- {report.asa_suggestion}",
        f"- {report.rcri_summary}",
        f"- {report.stop_bang_summary}",
        f"- {report.ponv_summary}",
        "",
        "## Risk Flags",
        _render_risk_flags(report.risk_flags),
        "",
        "## ECG Findings",
        _render_ecg_findings(report.ecg_findings),
        "",
        "## Lab Findings",
        _render_lab_findings(report.lab_findings),
        "",
        "## Missing Information",
        _render_list(report.missing_information),
        "",
        "## Follow-up Questions",
        _render_list(report.suggested_follow_up_questions),
        "",
        "## Additional Checks and Monitoring Focus",
        _render_list([*report.suggested_additional_checks, *report.perioperative_monitoring_focus]),
        "",
        "## Clinician Notes",
        report.clinician_notes or "Not yet documented.",
        "",
    ]
    return "\n".join(sections)


def _render_context(context: PatientContext) -> str:
    lines = [
        f"- Age: {context.age or 'needs confirmation'}",
        f"- Sex: {context.sex or 'needs confirmation'}",
        f"- Height / weight / BMI: {context.height_weight_bmi or 'needs confirmation'}",
        f"- Planned surgery: {context.planned_surgery or 'needs confirmation'}",
        f"- Urgency: {context.urgency or 'needs confirmation'}",
        f"- History: {', '.join(context.history) or 'not extracted'}",
        f"- Medications: {', '.join(context.medications) or 'not extracted'}",
        f"- Allergies: {', '.join(context.allergies) or 'not extracted'}",
        f"- Anesthesia history: {', '.join(context.anesthesia_history) or 'not extracted'}",
    ]
    return "\n".join(lines)


def _render_risk_flags(flags: list[RiskFlag]) -> str:
    if not flags:
        return "No structured risk flags were generated."
    return "\n".join(
        f"- **{flag.name}** (`{flag.severity}`): {flag.rationale}"
        for flag in flags
    )


def _render_ecg_findings(findings: list[ECGFinding]) -> str:
    if not findings:
        return "No structured ECG findings were extracted."
    blocks = []
    for finding in findings:
        blocks.append(
            "\n".join(
                [
                    f"### {finding.source}",
                    f"- Rhythm: {finding.rhythm or 'not extracted'}",
                    f"- Heart rate: {finding.heart_rate or 'not extracted'}",
                    f"- PR / QRS / QTc: {finding.pr_interval or 'not extracted'} / "
                    f"{finding.qrs_duration or 'not extracted'} / {finding.qtc or 'not extracted'}",
                    f"- ST-T changes: {', '.join(finding.st_t_changes) or 'none extracted'}",
                    f"- Conduction findings: {', '.join(finding.conduction_findings) or 'none extracted'}",
                    f"- Arrhythmia findings: {', '.join(finding.arrhythmia_findings) or 'none extracted'}",
                    f"- Anesthesia risk notes: {'; '.join(finding.anesthesia_risk_notes) or 'none'}",
                    f"- Missing ECG info: {'; '.join(finding.missing_info) or 'none'}",
                ]
            )
        )
    return "\n\n".join(blocks)


def _render_lab_findings(findings: list[LabFinding]) -> str:
    if not findings:
        return "No structured lab findings were extracted."
    lines = ["| Test | Value | Interpretation | Relevance | Source |", "| --- | --- | --- | --- | --- |"]
    for lab in findings:
        value = f"{lab.value}{lab.unit or ''}"
        lines.append(
            f"| {lab.name} | {value} | {lab.interpretation} | {lab.anesthesia_relevance} | {lab.source} |"
        )
    return "\n".join(lines)


def _render_list(items: list[str]) -> str:
    if not items:
        return "None documented."
    return "\n".join(f"- {item}" for item in items)
