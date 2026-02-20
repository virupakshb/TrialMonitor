"""
Templates for exclusion criteria evaluation
"""

# =============================================================================
# TEMPLATE 1: COMPLEX MEDICAL HISTORY EVALUATION (LLM + Tools)
# =============================================================================

COMPLEX_EXCLUSION_TEMPLATE = """
You are a clinical trial protocol expert evaluating an exclusion criterion.

TASK:
Determine if Subject {subject_id} meets this EXCLUSION criterion.
⚠️ If subject meets exclusion → Subject is INELIGIBLE for the study.

PROTOCOL CONTEXT:
Protocol: {protocol_number} - {protocol_name}
Exclusion Criterion ID: {criterion_id}
Description: "{criterion_description}"
Protocol Reference: {protocol_section}
Current Study Phase: {study_phase}

DOMAIN KNOWLEDGE:
{domain_knowledge}

EVALUATION CRITERIA:
{evaluation_criteria}

AVAILABLE TOOLS:
You have access to these tools to gather evidence:

1. check_medical_history(subject_id, search_terms, status_filter)
   - Searches medical history for conditions
   - status_filter: "ongoing", "resolved", or "any"
   - Returns: matching conditions with dates and status

2. check_conmeds(subject_id, medication_names, medication_classes)
   - Checks current and recent medications
   - Returns: active medications with details

3. check_labs(subject_id, test_names, timeframe_days)
   - Retrieves laboratory results
   - Returns: test values with dates

4. get_ecg_results(subject_id)
   - Checks ECG findings
   - Returns: ECG data with QTc values

SUBJECT DATA SUMMARY:
Subject ID: {subject_id}
Age: {age}, Sex: {sex}
Primary Diagnosis: {primary_diagnosis}
Study Status: {study_status}

Recent Medical History:
{recent_medical_history}

Current Medications:
{current_medications}

VISIT CONTEXT:
{visit_context}

INSTRUCTIONS:
1. Use available tools to gather ALL relevant evidence
2. Consider both current status AND history
3. Apply medical judgment for ambiguous cases
4. Determine if criterion is met (subject EXCLUDED)
5. Account for study phase (screening vs post-randomization)
6. Provide confidence level and reasoning

IMPORTANT - PHASE-SPECIFIC ACTIONS:
- If SCREENING phase: Exclusion = SCREEN FAILURE (do not enroll)
- If POST-RANDOMIZATION: Different handling based on timing:
  * New development (not present at baseline) = SAFETY SIGNAL
  * Missed at baseline = PROTOCOL DEVIATION

OUTPUT FORMAT (JSON):
{{
  "excluded": true/false,
  "confidence": "high/medium/low",
  "evidence": [
    "Evidence item 1",
    "Evidence item 2"
  ],
  "reasoning": "Step-by-step explanation of decision process",
  "tools_used": ["tool1", "tool2"],
  "missing_data": ["data_needed_1"] or [],
  "action_required": "SCREEN_FAILURE" or "PROTOCOL_DEVIATION" or "SAFETY_SIGNAL",
  "recommendation": "Detailed recommendation for CRA/physician",
  "requires_review": true/false
}}
"""

# =============================================================================
# TEMPLATE 2: SIMPLE THRESHOLD CHECK (Deterministic)
# =============================================================================

SIMPLE_THRESHOLD_TEMPLATE = """
DETERMINISTIC CHECK - No LLM Reasoning Needed

Rule: {criterion_description}
Type: Laboratory/ECG threshold check
Study Phase: {study_phase}

Execute: check_lab_threshold(
    subject_id="{subject_id}",
    test_name="{test_name}",
    operator="{operator}",
    threshold={threshold},
    timepoint="{timepoint}"
)

Evaluation Logic:
- At SCREENING/BASELINE: If test_value {operator} {threshold} → EXCLUDED (SCREEN FAILURE)
- POST-RANDOMIZATION: If test_value {operator} {threshold} → SAFETY SIGNAL (not exclusion)

This is a simple pass/fail check requiring no interpretation.
The tool will return the actual value and comparison result.
"""

# =============================================================================
# TEMPLATE 3: STATUS CHECK (Boolean/Field Check)
# =============================================================================

BOOLEAN_STATUS_TEMPLATE = """
BOOLEAN STATUS CHECK

Rule: {criterion_description}
Type: Status field verification
Study Phase: {study_phase}

Primary Check:
- Field: {field_name}
- Table: {table_name}
- Expected for Exclusion: {excluded_value}

Additional Verifications:
{additional_checks}

Evaluation:
- At SCREENING/BASELINE: If status = {excluded_value} → EXCLUDED (SCREEN FAILURE)
- POST-RANDOMIZATION: If status = {excluded_value} → Immediate action required

Example:
For pregnancy: Check demographics.pregnancy_status
If True → Subject excluded (screening) or immediate discontinuation (post-randomization)
"""


# =============================================================================
# TEMPLATE METADATA
# =============================================================================

EXCLUSION_TEMPLATES = {
    "COMPLEX_EXCLUSION_TEMPLATE": {
        "name": "Complex Medical History Evaluation",
        "type": "llm_with_tools",
        "template": COMPLEX_EXCLUSION_TEMPLATE,
        "suitable_for": [
            "Prior therapy exclusions",
            "Active disease states",
            "Complex medical conditions",
            "Requires clinical judgment"
        ]
    },
    "SIMPLE_THRESHOLD_TEMPLATE": {
        "name": "Simple Threshold Check",
        "type": "deterministic",
        "template": SIMPLE_THRESHOLD_TEMPLATE,
        "suitable_for": [
            "Lab value thresholds",
            "ECG parameter limits",
            "Vital sign ranges"
        ]
    },
    "BOOLEAN_STATUS_TEMPLATE": {
        "name": "Boolean Status Check",
        "type": "deterministic",
        "template": BOOLEAN_STATUS_TEMPLATE,
        "suitable_for": [
            "Pregnancy status",
            "Binary eligibility criteria",
            "Yes/No determinations"
        ]
    }
}
