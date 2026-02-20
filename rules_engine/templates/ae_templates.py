"""
Templates for Adverse Event monitoring
"""

# SAE Regulatory Compliance Template
SAE_REPORTING_TEMPLATE = """
SAE REGULATORY COMPLIANCE CHECK

SAE Details:
- Subject: {subject_id}
- AE Term: {ae_term}
- Onset: {onset_date}
- Seriousness Criteria: {serious_criteria}
- Outcome: {outcome}

Regulatory Requirements:
- Fatal/Life-threatening: Report within 24 hours
- Other SAEs: Report within 7 calendar days

Calculation:
- SAE Onset: {onset_date}
- Report Due: {due_date}
- Actual Report: {reported_date}
- Days Delay: {days_delay}

OUTPUT (JSON):
{{
  "compliant": true/false,
  "days_late": {days_delay},
  "severity": "critical",
  "regulatory_risk": "high/medium/low",
  "action_required": "Report description"
}}
"""

# AE Grading Template
AE_GRADING_TEMPLATE = """
You are validating CTCAE v5.0 grading for an adverse event.

AE: {ae_term}
Reported Grade: {reported_grade}
Description: {ae_description}

Clinical Data:
{clinical_context}

Tools: check_ctcae_criteria, check_labs, check_vital_signs

Task: Validate if reported grade matches CTCAE v5.0 criteria

OUTPUT (JSON):
{{
  "grade_appropriate": true/false,
  "reported_grade": {reported_grade},
  "expected_grade": X,
  "evidence": [...],
  "recommendation": "..."
}}
"""

# AESI Detection Template
AESI_DETECTION_TEMPLATE = """
Identify if AE is an Adverse Event of Special Interest (AESI).

Protocol AESI Categories:
1. Immune-Related AEs (irAE): pneumonitis, colitis, hepatitis, endocrine, rash
2. Infusion Reactions: within 24hrs of infusion
3. Severe Infections: opportunistic, Grade 3+
4. Cardiac Events: myocarditis, QTc prolongation

AE Under Review:
- Term: {ae_term}
- Description: {ae_description}
- Onset: {onset_date}
- Grade: {ctcae_grade}
- Last Infusion: {last_infusion_date}

Tools: check_timing_relative_to_infusion, check_lab_support, check_imaging

OUTPUT (JSON):
{{
  "is_aesi": true/false,
  "aesi_category": "...",
  "evidence": [...],
  "severity": "...",
  "action_required": [...]
}}
"""

AE_TEMPLATES = {
    "SAE_REPORTING": SAE_REPORTING_TEMPLATE,
    "AE_GRADING": AE_GRADING_TEMPLATE,
    "AESI_DETECTION": AESI_DETECTION_TEMPLATE
}
