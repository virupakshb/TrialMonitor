"""
FastAPI Backend for Clinical Trial Monitoring System - SQLite Version
Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
Sponsor: NexaVance Therapeutics Inc.

Local development API using SQLite database
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
import sqlite3
from contextlib import contextmanager
import os
import sys
import threading

# Load .env FIRST before anything else reads environment variables
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_env_path, override=True)

# Add project root to path so rules_engine can be imported
sys.path.insert(0, os.path.dirname(__file__))

# Shared state for batch job progress
_batch_jobs: Dict[str, Any] = {}

app = FastAPI(
    title="Clinical Trial Monitoring API",
    description="API for NVX-1218.22 Clinical Trial Data (SQLite Version)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'clinical_trial.db')

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    return dict(row) if row else None

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "api": "Clinical Trial Monitoring System",
        "protocol": "NVX-1218.22",
        "study": "NovaPlex-450 in Advanced NSCLC",
        "sponsor": "NexaVance Therapeutics Inc.",
        "version": "1.0.0",
        "database": "SQLite (local)",
        "status": "operational",
        "endpoints": {
            "protocol": "/api/protocol",
            "sites": "/api/sites",
            "subjects": "/api/subjects",
            "demographics": "/api/demographics/{subject_id}",
            "visits": "/api/visits",
            "vitals": "/api/vitals/{subject_id}",
            "labs": "/api/labs/{subject_id}",
            "adverse_events": "/api/adverse-events",
            "medical_history": "/api/medical-history/{subject_id}",
            "conmeds": "/api/conmeds/{subject_id}",
            "tumor_assessments": "/api/tumor-assessments/{subject_id}",
            "ecg": "/api/ecg/{subject_id}",
            "deviations": "/api/deviations",
            "queries": "/api/queries",
            "statistics": "/api/statistics"
        }
    }

# ============================================================================
# PROTOCOL ENDPOINTS
# ============================================================================

@app.get("/api/protocol")
def get_protocol():
    """Get protocol information"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM protocol_info LIMIT 1")
        protocol = cur.fetchone()
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return dict_from_row(protocol)

# ============================================================================
# SITE ENDPOINTS
# ============================================================================

@app.get("/api/sites")
def get_sites():
    """Get all sites"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sites ORDER BY site_id")
        sites = cur.fetchall()
    
    return [dict_from_row(site) for site in sites]

@app.get("/api/sites/{site_id}")
def get_site(site_id: str):
    """Get specific site"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sites WHERE site_id = ?", (site_id,))
        site = cur.fetchone()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return dict_from_row(site)

# ============================================================================
# SUBJECT ENDPOINTS
# ============================================================================

@app.get("/api/subjects")
def get_subjects(
    site_id: Optional[str] = None,
    treatment_arm: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get subjects with optional filters"""
    with get_db() as conn:
        cur = conn.cursor()
        
        query = "SELECT * FROM subjects WHERE 1=1"
        params = []
        
        if site_id:
            query += " AND site_id = ?"
            params.append(site_id)
        
        if treatment_arm:
            query += " AND treatment_arm = ?"
            params.append(treatment_arm)
        
        if status:
            query += " AND study_status = ?"
            params.append(status)
        
        query += f" ORDER BY subject_id LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        subjects = cur.fetchall()
    
    return [dict_from_row(subject) for subject in subjects]

@app.get("/api/subjects/{subject_id}")
def get_subject(subject_id: str):
    """Get specific subject"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM subjects WHERE subject_id = ?", (subject_id,))
        subject = cur.fetchone()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return dict_from_row(subject)

# ============================================================================
# DEMOGRAPHICS ENDPOINT
# ============================================================================

@app.get("/api/demographics/{subject_id}")
def get_demographics(subject_id: str):
    """Get subject demographics"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM demographics WHERE subject_id = ?", (subject_id,))
        demo = cur.fetchone()
    
    if not demo:
        raise HTTPException(status_code=404, detail="Demographics not found")
    
    return dict_from_row(demo)

# ============================================================================
# VISIT ENDPOINTS
# ============================================================================

@app.get("/api/visits")
def get_visits(
    subject_id: Optional[str] = None,
    visit_status: Optional[str] = None,
    limit: int = Query(default=500, le=5000)
):
    """Get visits"""
    with get_db() as conn:
        cur = conn.cursor()
        
        query = "SELECT * FROM visits WHERE 1=1"
        params = []
        
        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id)
        
        if visit_status:
            query += " AND visit_status = ?"
            params.append(visit_status)
        
        query += f" ORDER BY subject_id, visit_number LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        visits = cur.fetchall()
    
    return [dict_from_row(visit) for visit in visits]

# ============================================================================
# VITAL SIGNS ENDPOINT
# ============================================================================

@app.get("/api/vitals/{subject_id}")
def get_vitals(subject_id: str):
    """Get vital signs for subject"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM vital_signs 
            WHERE subject_id = ? 
            ORDER BY assessment_date
        """, (subject_id,))
        vitals = cur.fetchall()
    
    return [dict_from_row(vital) for vital in vitals]

# ============================================================================
# LABORATORY ENDPOINTS
# ============================================================================

@app.get("/api/labs/{subject_id}")
def get_labs(
    subject_id: str,
    lab_category: Optional[str] = None,
    abnormal_only: bool = False
):
    """Get laboratory results for subject"""
    with get_db() as conn:
        cur = conn.cursor()
        
        query = "SELECT * FROM laboratory_results WHERE subject_id = ?"
        params = [subject_id]
        
        if lab_category:
            query += " AND lab_category = ?"
            params.append(lab_category)
        
        if abnormal_only:
            query += " AND abnormal_flag != 'Normal'"
        
        query += " ORDER BY collection_date, lab_category, test_name"
        
        cur.execute(query, params)
        labs = cur.fetchall()
    
    return [dict_from_row(lab) for lab in labs]

# ============================================================================
# ADVERSE EVENTS ENDPOINTS
# ============================================================================

@app.get("/api/adverse-events")
def get_adverse_events(
    subject_id: Optional[str] = None,
    severity: Optional[str] = None,
    seriousness: Optional[str] = None,
    ongoing: Optional[bool] = None,
    limit: int = Query(default=500, le=5000)
):
    """Get adverse events"""
    with get_db() as conn:
        cur = conn.cursor()
        
        query = "SELECT * FROM adverse_events WHERE 1=1"
        params = []
        
        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if seriousness:
            query += " AND seriousness = ?"
            params.append(seriousness)
        
        if ongoing is not None:
            query += " AND ongoing = ?"
            params.append(1 if ongoing else 0)
        
        query += f" ORDER BY onset_date DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        aes = cur.fetchall()
    
    return [dict_from_row(ae) for ae in aes]

# ============================================================================
# MEDICAL HISTORY ENDPOINT
# ============================================================================

@app.get("/api/medical-history/{subject_id}")
def get_medical_history(subject_id: str):
    """Get medical history for subject"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM medical_history 
            WHERE subject_id = ? 
            ORDER BY diagnosis_date DESC
        """, (subject_id,))
        history = cur.fetchall()
    
    return [dict_from_row(h) for h in history]

# ============================================================================
# CONCOMITANT MEDICATIONS ENDPOINT
# ============================================================================

@app.get("/api/conmeds/{subject_id}")
def get_conmeds(subject_id: str):
    """Get concomitant medications for subject"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM concomitant_medications 
            WHERE subject_id = ? 
            ORDER BY start_date
        """, (subject_id,))
        conmeds = cur.fetchall()
    
    return [dict_from_row(cm) for cm in conmeds]

# ============================================================================
# TUMOR ASSESSMENTS ENDPOINT
# ============================================================================

@app.get("/api/tumor-assessments/{subject_id}")
def get_tumor_assessments(subject_id: str):
    """Get tumor assessments for subject"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM tumor_assessments 
            WHERE subject_id = ? 
            ORDER BY assessment_date
        """, (subject_id,))
        assessments = cur.fetchall()
    
    return [dict_from_row(assessment) for assessment in assessments]

# ============================================================================
# ECG ENDPOINT
# ============================================================================

@app.get("/api/ecg/{subject_id}")
def get_ecg(subject_id: str):
    """Get ECG results for subject"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM ecg_results 
            WHERE subject_id = ? 
            ORDER BY ecg_date
        """, (subject_id,))
        ecgs = cur.fetchall()
    
    return [dict_from_row(ecg) for ecg in ecgs]

# ============================================================================
# PROTOCOL DEVIATIONS ENDPOINTS
# ============================================================================

@app.get("/api/deviations")
def get_deviations(
    subject_id: Optional[str] = None,
    deviation_type: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=200, le=2000)
):
    """Get protocol deviations"""
    with get_db() as conn:
        cur = conn.cursor()
        
        query = "SELECT * FROM protocol_deviations WHERE 1=1"
        params = []
        
        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id)
        
        if deviation_type:
            query += " AND deviation_type = ?"
            params.append(deviation_type)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += f" ORDER BY deviation_date DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        deviations = cur.fetchall()
    
    return [dict_from_row(deviation) for deviation in deviations]

# ============================================================================
# QUERIES ENDPOINTS
# ============================================================================

@app.get("/api/queries")
def get_queries(
    subject_id: Optional[str] = None,
    query_status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=200, le=2000)
):
    """Get data queries"""
    with get_db() as conn:
        cur = conn.cursor()
        
        query_sql = "SELECT * FROM queries WHERE 1=1"
        params = []
        
        if subject_id:
            query_sql += " AND subject_id = ?"
            params.append(subject_id)
        
        if query_status:
            query_sql += " AND query_status = ?"
            params.append(query_status)
        
        if priority:
            query_sql += " AND priority = ?"
            params.append(priority)
        
        query_sql += f" ORDER BY query_date DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query_sql, params)
        queries = cur.fetchall()
    
    return [dict_from_row(q) for q in queries]

# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@app.get("/api/statistics")
def get_statistics():
    """Get overall statistics"""
    with get_db() as conn:
        cur = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = [
            'sites', 'subjects', 'visits', 'vital_signs', 'laboratory_results',
            'adverse_events', 'medical_history', 'concomitant_medications',
            'tumor_assessments', 'ecg_results', 'protocol_deviations', 'queries'
        ]
        
        for table in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cur.fetchone()
            stats[table] = result['count']
        
        # Additional statistics
        cur.execute("SELECT COUNT(*) as count FROM subjects WHERE study_status = 'Enrolled'")
        stats['subjects_enrolled'] = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM adverse_events WHERE seriousness = 'Yes'")
        stats['serious_adverse_events'] = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM protocol_deviations WHERE status = 'Open'")
        stats['open_deviations'] = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM queries WHERE query_status = 'Open'")
        stats['open_queries'] = cur.fetchone()['count']
    
    return stats

# ============================================================================
# RULES ENDPOINTS
# ============================================================================

@app.get("/api/rules")
def get_rules():
    """Get all rules from all YAML configuration files"""
    import yaml
    from pathlib import Path

    rule_configs_dir = Path(os.path.dirname(__file__)) / 'rule_configs'
    normalized = []

    try:
        yaml_files = sorted(rule_configs_dir.glob('*.yaml'))
        for yaml_file in yaml_files:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if not config:
                continue
            # Each YAML file has one top-level list key (skip 'protocol' metadata)
            for key, value in config.items():
                if key == 'protocol':
                    continue
                if isinstance(value, list):
                    for r in value:
                        if not isinstance(r, dict) or 'rule_id' not in r:
                            continue
                        normalized.append({
                            "rule_id": r.get("rule_id"),
                            "name": r.get("name"),
                            "description": r.get("description"),
                            "category": r.get("category", "exclusion"),
                            "severity": r.get("severity", "major"),
                            "status": r.get("status", "active"),
                            "complexity": r.get("complexity", "simple"),
                            "evaluation_type": r.get("evaluation_type", "deterministic"),
                            "template_name": r.get("template_name", ""),
                            "protocol_reference": r.get("protocol_section", ""),
                            "tools_needed": r.get("tools_needed", []),
                            "source_file": yaml_file.name,
                        })

        # Sort by rule_id for consistent display
        normalized.sort(key=lambda r: r["rule_id"] or "")
        return {"rules": normalized, "total": len(normalized)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates")
def get_templates():
    """Get all rule templates with metadata"""
    return {
        "COMPLEX_EXCLUSION_TEMPLATE": {
            "name": "Complex Medical History Evaluation",
            "type": "llm_with_tools",
            "description": "Uses Claude LLM with clinical data tools to evaluate complex exclusion criteria requiring medical judgment.",
            "suitable_for": [
                "Prior therapy exclusions",
                "Active disease states",
                "Complex medical conditions",
                "Requires clinical judgment"
            ],
            "tools_available": [
                "check_medical_history(subject_id, search_terms, status_filter)",
                "check_conmeds(subject_id, medication_names, medication_classes)",
                "check_labs(subject_id, test_names, timeframe_days)",
                "get_ecg_results(subject_id)"
            ],
            "output_fields": ["excluded", "confidence", "evidence", "reasoning", "tools_used", "missing_data", "action_required", "recommendation", "requires_review"],
            "phase_logic": {
                "screening": "Exclusion = SCREEN FAILURE (do not enroll)",
                "post_randomization": "New finding = SAFETY SIGNAL | Missed at baseline = PROTOCOL DEVIATION"
            }
        },
        "SIMPLE_THRESHOLD_TEMPLATE": {
            "name": "Simple Threshold Check",
            "type": "deterministic",
            "description": "Deterministic pass/fail check for lab values, ECG parameters, or vital signs against a fixed threshold. No LLM reasoning needed.",
            "suitable_for": [
                "Lab value thresholds (e.g. QTcF >470ms)",
                "ECG parameter limits",
                "Vital sign ranges"
            ],
            "tools_available": [
                "check_lab_threshold(subject_id, test_name, operator, threshold, timepoint)"
            ],
            "output_fields": ["excluded", "actual_value", "threshold", "operator", "action_required"],
            "phase_logic": {
                "screening": "Value exceeds threshold = SCREEN FAILURE",
                "post_randomization": "Value exceeds threshold = SAFETY SIGNAL"
            }
        },
        "BOOLEAN_STATUS_TEMPLATE": {
            "name": "Boolean Status Check",
            "type": "deterministic",
            "description": "Simple yes/no field verification. Used for binary eligibility criteria like pregnancy status.",
            "suitable_for": [
                "Pregnancy status",
                "Binary eligibility criteria",
                "Yes/No determinations"
            ],
            "tools_available": [
                "check_field_value(subject_id, table_name, field_name, expected_value)"
            ],
            "output_fields": ["excluded", "field_value", "expected_value", "action_required"],
            "phase_logic": {
                "screening": "Field matches exclusion value = SCREEN FAILURE",
                "post_randomization": "Field matches exclusion value = Immediate action required"
            }
        },
        "SAE_REPORTING_TEMPLATE": {
            "name": "Serious Adverse Event Reporting",
            "type": "llm_with_tools",
            "description": "Uses LLM to detect SAEs, verify 24-hour reporting compliance, and flag Grade 3-4 events requiring immediate sponsor notification per ICH E6.",
            "suitable_for": [
                "SAE detection and classification",
                "Reporting timeline compliance (24hr rule)",
                "Grade 3-4 adverse event escalation",
                "Drug discontinuation due to AE"
            ],
            "tools_available": [
                "get_adverse_events(subject_id, sae_only, min_grade)",
                "get_visits(subject_id)",
                "check_medical_history(subject_id, search_terms)"
            ],
            "output_fields": ["violated", "severity", "action_required", "evidence", "reasoning", "confidence"],
            "phase_logic": {
                "post_randomization": "SAE detected = IMMEDIATE sponsor notification required within 24 hours",
                "screening": "Grade 3-4 AE at screening = SCREEN FAILURE or delayed enrolment"
            }
        },
        "AE_GRADING_TEMPLATE": {
            "name": "Adverse Event Grading & Dose Management",
            "type": "llm_with_tools",
            "description": "Evaluates CTCAE grading of adverse events and determines required dose modifications, holds, or discontinuations per protocol safety rules.",
            "suitable_for": [
                "Grade 3-4 AE detection",
                "Dose modification triggers",
                "Drug discontinuation criteria",
                "Haematologic toxicity management"
            ],
            "tools_available": [
                "get_adverse_events(subject_id, min_grade)",
                "get_labs(subject_id, test_names)",
                "get_visits(subject_id)"
            ],
            "output_fields": ["violated", "severity", "action_required", "evidence", "reasoning", "confidence"],
            "phase_logic": {
                "post_randomization": "Grade >=3 AE = dose modification or discontinuation required",
                "screening": "Pre-existing Grade >=3 condition = eligibility review"
            }
        },
        "AESI_DETECTION_TEMPLATE": {
            "name": "Immune-Related Adverse Events of Special Interest",
            "type": "llm_with_tools",
            "description": "Identifies immune-related AESIs (irAE) such as pneumonitis, myocarditis, colitis, hepatitis, and thyroiditis following checkpoint inhibitor therapy. Requires clinical judgment to distinguish from pre-existing conditions.",
            "suitable_for": [
                "irAE detection (myocarditis, pneumonitis, thyroiditis, colitis, hepatitis)",
                "Distinguishing new immune-related events from pre-existing conditions",
                "AESI reporting to sponsor",
                "Post-immunotherapy safety surveillance"
            ],
            "tools_available": [
                "get_adverse_events(subject_id)",
                "check_medical_history(subject_id, search_terms)",
                "get_labs(subject_id, test_names)",
                "get_visits(subject_id)"
            ],
            "output_fields": ["violated", "severity", "action_required", "evidence", "reasoning", "confidence"],
            "phase_logic": {
                "post_randomization": "irAESI confirmed = AESI report required; consider immunosuppression and drug hold/discontinuation",
                "screening": "Pre-existing autoimmune condition = eligibility exclusion review"
            }
        }
    }


@app.get("/api/templates/{template_name}")
def get_template(template_name: str):
    """Get a specific template by name"""
    all_templates = get_templates()
    if template_name not in all_templates:
        raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
    return all_templates[template_name]


@app.get("/api/templates/{template_name}/sample-input")
def get_template_sample_input(template_name: str, subject_id: str = "101-001"):
    """Return a real sample input that would be passed to the given template for a subject"""
    with get_db() as conn:
        cur = conn.cursor()

        # Subject info
        cur.execute("SELECT * FROM subjects WHERE subject_id = ?", (subject_id,))
        subject = dict_from_row(cur.fetchone())
        if not subject:
            raise HTTPException(status_code=404, detail=f"Subject {subject_id} not found")

        # Medical history
        cur.execute("SELECT condition, diagnosis_date, ongoing, condition_category, condition_notes FROM medical_history WHERE subject_id = ? LIMIT 5", (subject_id,))
        med_history = [dict_from_row(r) for r in cur.fetchall()]

        # Conmeds
        cur.execute("SELECT medication_name, indication, dose, frequency, start_date, ongoing FROM concomitant_medications WHERE subject_id = ? LIMIT 5", (subject_id,))
        conmeds = [dict_from_row(r) for r in cur.fetchall()]

        # Labs
        cur.execute("SELECT test_name, test_value, test_unit, collection_date, normal_range_lower, normal_range_upper, clinically_significant FROM laboratory_results WHERE subject_id = ? ORDER BY collection_date DESC LIMIT 6", (subject_id,))
        labs = [dict_from_row(r) for r in cur.fetchall()]

        # ECG
        cur.execute("SELECT ecg_date, qtcf_interval, heart_rate, interpretation, abnormal FROM ecg_results WHERE subject_id = ? ORDER BY ecg_date DESC LIMIT 2", (subject_id,))
        ecg = [dict_from_row(r) for r in cur.fetchall()]

    if template_name == "COMPLEX_EXCLUSION_TEMPLATE":
        return {
            "template": template_name,
            "subject_id": subject_id,
            "description": "These are the actual fields passed to the LLM prompt when evaluating this template for the subject.",
            "input": {
                "subject_id": subject_id,
                "protocol_number": "NVX-1218.22",
                "protocol_name": "NovaPlex-450 in Advanced NSCLC",
                "criterion_id": "EXCL-001",
                "criterion_description": "Prior therapy with PD-1/PD-L1 or CTLA-4 checkpoint inhibitors",
                "protocol_section": "Section 4.2.1",
                "study_phase": "post_randomization" if subject.get("randomization_date") else "screening",
                "age": "Derived from demographics",
                "sex": "Derived from demographics",
                "primary_diagnosis": next((m["condition"] for m in med_history if m["condition_category"] == "Primary Diagnosis"), "N/A"),
                "study_status": subject.get("study_status"),
                "recent_medical_history": med_history,
                "current_medications": [c for c in conmeds if c["ongoing"]],
                "visit_context": f"Randomization date: {subject.get('randomization_date')} | Screening: {subject.get('screening_date')}",
                "tools_that_will_be_called": [
                    {"tool": "check_medical_history", "args": {"subject_id": subject_id, "search_terms": ["pembrolizumab", "nivolumab", "keytruda", "opdivo", "PD-1 inhibitor", "checkpoint inhibitor"], "status_filter": "any"}},
                    {"tool": "check_conmeds", "args": {"subject_id": subject_id, "medication_names": ["pembrolizumab", "nivolumab", "atezolizumab", "ipilimumab"], "medication_classes": ["PD-1 inhibitor", "PD-L1 inhibitor", "CTLA-4 inhibitor"]}}
                ]
            }
        }

    elif template_name == "SIMPLE_THRESHOLD_TEMPLATE":
        latest_ecg = ecg[0] if ecg else {}
        return {
            "template": template_name,
            "subject_id": subject_id,
            "description": "These are the exact parameters passed to the deterministic threshold check function.",
            "input": {
                "subject_id": subject_id,
                "criterion_description": "QTcF >470 msec on screening ECG",
                "study_phase": "post_randomization" if subject.get("randomization_date") else "screening",
                "test_name": "QTcF",
                "operator": ">",
                "threshold": 470,
                "unit": "msec",
                "timepoint": "screening",
                "actual_ecg_data_found": latest_ecg,
                "evaluation": {
                    "actual_value": latest_ecg.get("qtcf_interval", "N/A"),
                    "threshold": 470,
                    "operator": ">",
                    "result": "EXCLUDED" if latest_ecg.get("qtcf_interval", 0) > 470 else "PASS",
                    "interpretation": latest_ecg.get("interpretation", "N/A")
                }
            }
        }

    elif template_name == "BOOLEAN_STATUS_TEMPLATE":
        return {
            "template": template_name,
            "subject_id": subject_id,
            "description": "These are the exact field lookups performed for the boolean check.",
            "input": {
                "subject_id": subject_id,
                "criterion_description": "Subject is pregnant or breastfeeding",
                "study_phase": "post_randomization" if subject.get("randomization_date") else "screening",
                "field_name": "pregnancy_status",
                "table_name": "demographics",
                "expected_value_for_exclusion": True,
                "additional_checks": [
                    {"field": "breastfeeding", "table": "demographics", "excluded_if": True}
                ],
                "subject_record": {
                    "subject_id": subject_id,
                    "study_status": subject.get("study_status"),
                    "treatment_arm": subject.get("treatment_arm_name")
                }
            }
        }

    # AE-related templates — pull adverse events + visits
    with get_db() as conn2:
        cur2 = conn2.cursor()
        cur2.execute("""SELECT ae_term, ctcae_grade, seriousness, onset_date, outcome,
                        relationship_to_study_drug, action_taken, ae_description
                        FROM adverse_events WHERE subject_id = ? ORDER BY onset_date DESC LIMIT 6""", (subject_id,))
        aes = [dict_from_row(r) for r in cur2.fetchall()]

        cur2.execute("""SELECT visit_name, actual_date, visit_notes
                        FROM visits WHERE subject_id = ? ORDER BY actual_date DESC LIMIT 4""", (subject_id,))
        visits = [dict_from_row(r) for r in cur2.fetchall()]

    if template_name == "SAE_REPORTING_TEMPLATE":
        saes = [a for a in aes if a.get("seriousness") and a.get("seriousness").lower() != "no"]
        return {
            "template": template_name,
            "subject_id": subject_id,
            "description": "Inputs passed to the LLM when checking SAE detection and 24-hour reporting compliance.",
            "input": {
                "subject_id": subject_id,
                "protocol_number": "NVX-1218.22",
                "study_phase": "post_randomization",
                "rule": "All SAEs must be reported to sponsor within 24 hours of site awareness (ICH E6)",
                "adverse_events_found": aes,
                "saes_flagged": saes,
                "sae_count": len(saes),
                "recent_visits": visits,
                "tools_that_will_be_called": [
                    {"tool": "get_adverse_events", "args": {"subject_id": subject_id, "sae_only": True, "note": "seriousness field used"}},
                    {"tool": "get_visits", "args": {"subject_id": subject_id}}
                ]
            }
        }

    elif template_name == "AE_GRADING_TEMPLATE":
        return {
            "template": template_name,
            "subject_id": subject_id,
            "description": "Inputs passed to the LLM when evaluating Grade 3-4 AEs and required dose modifications.",
            "input": {
                "subject_id": subject_id,
                "protocol_number": "NVX-1218.22",
                "study_phase": "post_randomization",
                "rule": "Grade >=3 AEs require dose modification or discontinuation review per protocol Section 5.4",
                "all_adverse_events": aes,
                "grade3_plus_events": [a for a in aes if (a.get("ctcae_grade") or 0) >= 3],
                "recent_labs": labs,
                "tools_that_will_be_called": [
                    {"tool": "get_adverse_events", "args": {"subject_id": subject_id, "min_grade": 3}},
                    {"tool": "get_labs", "args": {"subject_id": subject_id, "test_names": ["ANC", "Haemoglobin", "Platelets"]}}
                ]
            }
        }

    elif template_name == "AESI_DETECTION_TEMPLATE":
        iraes = [a for a in aes if any(kw in (a.get("ae_term") or "").lower()
                 for kw in ["immune", "pneumonitis", "myocarditis", "thyroiditis", "colitis", "hepatitis"])]
        return {
            "template": template_name,
            "subject_id": subject_id,
            "description": "Inputs passed to the LLM when detecting immune-related AESIs after checkpoint inhibitor therapy.",
            "input": {
                "subject_id": subject_id,
                "protocol_number": "NVX-1218.22",
                "study_phase": "post_randomization",
                "rule": "All irAESIs (myocarditis, pneumonitis, colitis, hepatitis, thyroiditis) must be reported as AESIs",
                "all_adverse_events": aes,
                "suspected_iraes": iraes,
                "pre_existing_conditions": med_history,
                "recent_labs": labs,
                "tools_that_will_be_called": [
                    {"tool": "get_adverse_events", "args": {"subject_id": subject_id}},
                    {"tool": "check_medical_history", "args": {"subject_id": subject_id, "search_terms": ["thyroid", "autoimmune", "hypothyroid", "pneumonitis"]}},
                    {"tool": "get_labs", "args": {"subject_id": subject_id, "test_names": ["TSH", "Troponin", "ALT", "AST"]}}
                ]
            }
        }

    raise HTTPException(status_code=404, detail=f"No sample input defined for template {template_name}")


@app.put("/api/rules/{rule_id}/status")
def update_rule_status(rule_id: str, status: str):
    """Toggle a rule's active/inactive status — searches all YAML files"""
    import yaml
    from pathlib import Path

    rule_configs_dir = Path(os.path.dirname(__file__)) / 'rule_configs'

    try:
        yaml_files = sorted(rule_configs_dir.glob('*.yaml'))
        for yaml_file in yaml_files:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if not config:
                continue

            updated = False
            for key, value in config.items():
                if key == 'protocol' or not isinstance(value, list):
                    continue
                for r in value:
                    if isinstance(r, dict) and r.get('rule_id') == rule_id:
                        r['status'] = status
                        updated = True
                        break
                if updated:
                    break

            if updated:
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                return {"message": f"Rule {rule_id} status updated to {status}", "file": yaml_file.name}

        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found in any config file")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RULE EXECUTION / EVALUATE ENDPOINTS
# ============================================================================

def _get_executor():
    """Lazy-load the RuleExecutor with API key from environment"""
    from rules_engine.core.executor import RuleExecutor
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    return RuleExecutor(api_key=api_key)


@app.get("/api/usage")
def get_usage():
    """Return current session token usage and estimated cost"""
    from rules_engine.evaluators.llm_evaluator import get_usage_stats
    return get_usage_stats()


@app.post("/api/usage/reset")
def reset_usage():
    """Reset the session usage counter"""
    from rules_engine.evaluators.llm_evaluator import reset_usage_stats
    reset_usage_stats()
    return {"message": "Usage stats reset"}


@app.post("/api/evaluate/subject/{subject_id}")
def evaluate_subject(subject_id: str):
    """Run all active rules for a single subject and return results"""
    import uuid, time, json as _json
    try:
        from rules_engine.evaluators.llm_evaluator import get_usage_stats
        executor = _get_executor()
        result = executor.execute_all_rules(subject_id)
        result["usage"] = get_usage_stats()

        # Save to disk so it appears in the Results tab
        try:
            job_id = f"single-{subject_id}-{str(uuid.uuid4())[:6]}"
            violations = result.get("violations", [])
            # Normalise violation shape to match batch format
            all_violations = []
            for v in violations:
                if isinstance(v, dict):
                    all_violations.append({
                        "subject_id": subject_id,
                        "rule_id": v.get("rule_id", ""),
                        "severity": v.get("severity"),
                        "action_required": v.get("action_required"),
                        "evidence": v.get("evidence", []),
                        "reasoning": v.get("reasoning", ""),
                    })
            # Serialise results list to plain JSON-safe dicts
            results_list = _json.loads(_json.dumps(result.get("results", []), default=str))
            save_data = {
                "job_id": job_id,
                "run_type": "single",
                "subject_id": subject_id,
                "status": "done",
                "total_subjects": 1,
                "completed_subjects": 1,
                "total_violations": len(all_violations),
                "all_violations": all_violations,
                "results": [{"subject_id": subject_id, "results": results_list,
                             "violations": all_violations, "violations_found": len(all_violations)}],
                "usage": result["usage"],
                "started_at": time.time(),
                "finished_at": time.time(),
            }
            _save_batch_result(job_id, save_data)
            result["job_id"] = job_id
        except Exception as save_err:
            print(f"Warning: could not save single-subject result: {save_err}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate/subject/{subject_id}/rule/{rule_id}")
def evaluate_single_rule(subject_id: str, rule_id: str):
    """Run a specific rule for a single subject"""
    try:
        executor = _get_executor()
        result = executor.execute_rule(rule_id, subject_id)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch_results')
os.makedirs(RESULTS_DIR, exist_ok=True)


def _save_batch_result(job_id: str, data: dict):
    """Save batch job result to disk as JSON"""
    import json, time
    data["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _run_batch_job(job_id: str, subject_ids: list, rule_ids: list):
    """Background thread function for batch evaluation"""
    _batch_jobs[job_id]["status"] = "running"
    all_results = []
    all_violations = []
    total = len(subject_ids)

    try:
        executor = _get_executor()
        for i, subject_id in enumerate(subject_ids):
            subject_results = []
            subject_violations = []

            rules_to_run = rule_ids if rule_ids else list(executor.rules.keys())
            for rule_id in rules_to_run:
                try:
                    result = executor.execute_rule(rule_id, subject_id)
                    r = result.to_dict()
                    r["subject_id"] = subject_id
                    subject_results.append(r)
                    if result.violated:
                        v = {"subject_id": subject_id, "rule_id": rule_id,
                             "severity": r.get("severity"), "action_required": r.get("action_required"),
                             "evidence": r.get("evidence", []), "reasoning": r.get("reasoning", "")}
                        subject_violations.append(v)
                        all_violations.append(v)
                except Exception as e:
                    subject_results.append({"subject_id": subject_id, "rule_id": rule_id,
                                            "error": str(e), "passed": False})

            all_results.append({"subject_id": subject_id, "results": subject_results,
                                 "violations": subject_violations,
                                 "violations_found": len(subject_violations)})

            # Update progress
            _batch_jobs[job_id]["completed"] = i + 1
            _batch_jobs[job_id]["progress_pct"] = round(((i + 1) / total) * 100)
            _batch_jobs[job_id]["violations_so_far"] = len(all_violations)

        from rules_engine.evaluators.llm_evaluator import get_usage_stats
        import time
        final_data = {
            "job_id": job_id,
            "status": "done",
            "results": all_results,
            "total_violations": len(all_violations),
            "all_violations": all_violations,
            "total_subjects": total,
            "completed_subjects": total,
            "usage": get_usage_stats(),
            "started_at": _batch_jobs[job_id].get("started_at"),
            "finished_at": time.time(),
        }
        _batch_jobs[job_id].update(final_data)
        _save_batch_result(job_id, final_data)

    except Exception as e:
        _batch_jobs[job_id]["status"] = "error"
        _batch_jobs[job_id]["error"] = str(e)
        _save_batch_result(job_id, {**_batch_jobs[job_id], "error": str(e)})


@app.post("/api/evaluate/batch")
def start_batch_evaluation(body: dict, background_tasks: BackgroundTasks):
    """
    Start batch evaluation for multiple subjects.
    Body: { "subject_ids": ["101-001", ...] or "all", "rule_ids": [] (optional, empty = all active) }
    Returns a job_id to poll for progress.
    """
    import uuid
    import time

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT subject_id FROM subjects ORDER BY subject_id")
        all_subjects = [r["subject_id"] for r in cur.fetchall()]

    requested = body.get("subject_ids", "all")
    subject_ids = all_subjects if requested == "all" else requested
    rule_ids = body.get("rule_ids", [])

    job_id = str(uuid.uuid4())[:8]
    _batch_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "total": len(subject_ids),
        "completed": 0,
        "progress_pct": 0,
        "violations_so_far": 0,
        "started_at": time.time(),
    }

    # Run in background thread so the API returns immediately
    t = threading.Thread(target=_run_batch_job, args=(job_id, subject_ids, rule_ids), daemon=True)
    t.start()

    return {"job_id": job_id, "total_subjects": len(subject_ids), "status": "queued"}


@app.get("/api/evaluate/batch/{job_id}")
def get_batch_status(job_id: str):
    """Poll the status and progress of a batch evaluation job. Falls back to disk if not in memory."""
    import json
    job = _batch_jobs.get(job_id)
    if not job:
        # Try loading from disk
        path = os.path.join(RESULTS_DIR, f"{job_id}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


# ============================================================================
# RESULTS ENDPOINTS - List and retrieve past batch runs
# ============================================================================

@app.get("/api/results")
def list_results():
    """List all saved batch run results"""
    import json, time
    results = []
    for fname in sorted(os.listdir(RESULTS_DIR), reverse=True):
        if fname.endswith(".json"):
            path = os.path.join(RESULTS_DIR, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
                # Return summary only (not full results array)
                results.append({
                    "job_id": data.get("job_id", fname.replace(".json", "")),
                    "run_type": data.get("run_type", "batch"),
                    "subject_id": data.get("subject_id"),  # only set for single-subject runs
                    "status": data.get("status"),
                    "total_subjects": data.get("total_subjects", 0),
                    "completed_subjects": data.get("completed_subjects", data.get("total_subjects", 0)),
                    "total_violations": data.get("total_violations", 0),
                    "saved_at": data.get("saved_at"),
                    "usage": data.get("usage", {}),
                })
            except Exception:
                pass
    return results


@app.get("/api/results/{job_id}")
def get_result(job_id: str):
    """Get full result for a specific batch run"""
    import json
    # Check memory first
    if job_id in _batch_jobs and _batch_jobs[job_id].get("status") == "done":
        return _batch_jobs[job_id]
    # Load from disk
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Result {job_id} not found")
    with open(path) as f:
        return json.load(f)


@app.get("/api/results/{job_id}/violations")
def get_result_violations(job_id: str):
    """Get just the violations list from a batch run"""
    import json
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    if not os.path.exists(path):
        # Try memory
        job = _batch_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Result {job_id} not found")
        return {"job_id": job_id, "violations": job.get("all_violations", [])}
    with open(path) as f:
        data = json.load(f)
    return {"job_id": job_id, "violations": data.get("all_violations", [])}


# ============================================================================
# SUBJECT DETAIL — VISITS WITH NESTED DATA
# ============================================================================

@app.get("/api/subjects/{subject_id}/visits")
def get_subject_visits_detail(subject_id: str):
    """Get all visits for a subject with nested vitals, ECG, labs per visit"""
    with get_db() as conn:
        cur = conn.cursor()

        # Check subject exists
        cur.execute("SELECT subject_id FROM subjects WHERE subject_id = ?", (subject_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Subject not found")

        # All visits ordered by visit number
        cur.execute("""
            SELECT visit_id, visit_number, visit_name, scheduled_date, actual_date,
                   visit_status, visit_type, visit_completed, missed_visit,
                   days_from_randomization, window_lower_days, window_upper_days, visit_notes
            FROM visits WHERE subject_id = ? ORDER BY visit_number ASC
        """, (subject_id,))
        visits = [dict_from_row(r) for r in cur.fetchall()]

        for v in visits:
            vid = v["visit_id"]
            vdate = v["actual_date"] or v["scheduled_date"]

            # Vitals — join by visit_id first, fall back to date match
            cur.execute("""
                SELECT systolic_bp, diastolic_bp, heart_rate, temperature_celsius,
                       respiratory_rate, weight_kg, oxygen_saturation, position, notes, assessment_date
                FROM vital_signs WHERE subject_id = ? AND (visit_id = ? OR assessment_date = ?)
            """, (subject_id, vid, vdate))
            v["vitals"] = [dict_from_row(r) for r in cur.fetchall()]

            # ECG — join by visit_id first, fall back to date match
            cur.execute("""
                SELECT ecg_date, heart_rate, pr_interval, qrs_duration, qt_interval,
                       qtcf_interval, interpretation, abnormal, clinically_significant
                FROM ecg_results WHERE subject_id = ? AND (visit_id = ? OR ecg_date = ?)
            """, (subject_id, vid, vdate))
            v["ecg"] = [dict_from_row(r) for r in cur.fetchall()]

            # Labs — join by visit_id first, fall back to collection_date match
            cur.execute("""
                SELECT lab_category, test_name, test_value, test_unit,
                       normal_range_lower, normal_range_upper, abnormal_flag,
                       clinically_significant, collection_date, lab_comments
                FROM laboratory_results
                WHERE subject_id = ? AND (visit_id = ? OR collection_date = ?)
                ORDER BY lab_category, test_name
            """, (subject_id, vid, vdate))
            v["labs"] = [dict_from_row(r) for r in cur.fetchall()]

            # Tumor assessment — join by visit_id first, fall back to date match
            cur.execute("""
                SELECT assessment_date, assessment_method, overall_response,
                       target_lesion_sum, new_lesions, progression, assessment_notes
                FROM tumor_assessments WHERE subject_id = ? AND (visit_id = ? OR assessment_date = ?)
            """, (subject_id, vid, vdate))
            v["tumor_assessment"] = dict_from_row(cur.fetchone())

    return {"subject_id": subject_id, "visits": visits, "total": len(visits)}


# ============================================================================
# SUBJECT VIOLATIONS — Latest run scoped to one subject
# ============================================================================

@app.get("/api/subjects/{subject_id}/violations")
def get_subject_violations(subject_id: str):
    """Get violations for a specific subject from their latest evaluation run"""
    import json, glob as globmod

    # Search all result files for this subject
    pattern = os.path.join(RESULTS_DIR, "*.json")
    files = sorted(globmod.glob(pattern), key=os.path.getmtime, reverse=True)

    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            # Check if this run includes the subject
            all_v = data.get("all_violations", [])
            subject_v = [v for v in all_v if v.get("subject_id") == subject_id]
            if subject_v or data.get("subject_id") == subject_id:
                # Also get per-rule results for this subject
                results_for_subject = []
                for sr in data.get("results", []):
                    if sr.get("subject_id") == subject_id:
                        results_for_subject = sr.get("results", [])
                        break
                return {
                    "subject_id": subject_id,
                    "job_id": data.get("job_id"),
                    "run_date": data.get("saved_at") or data.get("finished_at"),
                    "violations": subject_v,
                    "violations_found": len(subject_v),
                    "all_rule_results": results_for_subject,
                    "usage": data.get("usage", {})
                }
        except Exception:
            continue

    return {
        "subject_id": subject_id,
        "job_id": None,
        "run_date": None,
        "violations": [],
        "violations_found": 0,
        "all_rule_results": [],
        "usage": {}
    }


# ============================================================================
# GLOBAL VIOLATIONS — All subjects, all runs (deduplicated by subject+rule)
# ============================================================================

@app.get("/api/violations")
def get_all_violations(
    severity: Optional[str] = None,
    subject_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    limit: int = Query(default=500, le=2000)
):
    """Get all violations across all result runs, deduplicated to latest per subject+rule"""
    import json, glob as globmod

    pattern = os.path.join(RESULTS_DIR, "*.json")
    files = sorted(globmod.glob(pattern), key=os.path.getmtime, reverse=True)

    # Deduplicate: keep latest violation per (subject_id, rule_id)
    seen = {}
    all_violations = []

    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            run_date = data.get("saved_at") or data.get("finished_at", "")
            job_id = data.get("job_id", "")
            for v in data.get("all_violations", []):
                key = (v.get("subject_id"), v.get("rule_id"))
                if key not in seen:
                    seen[key] = True
                    all_violations.append({**v, "run_date": run_date, "job_id": job_id})
        except Exception:
            continue

    # Apply filters
    if severity:
        all_violations = [v for v in all_violations if v.get("severity") == severity]
    if subject_id:
        all_violations = [v for v in all_violations if v.get("subject_id") == subject_id]
    if rule_id:
        all_violations = [v for v in all_violations if v.get("rule_id") == rule_id]

    # Sort by severity order
    sev_order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
    all_violations.sort(key=lambda v: sev_order.get(v.get("severity", "info"), 9))

    # Summary counts
    summary = {
        "total": len(all_violations),
        "critical": sum(1 for v in all_violations if v.get("severity") == "critical"),
        "major": sum(1 for v in all_violations if v.get("severity") == "major"),
        "minor": sum(1 for v in all_violations if v.get("severity") == "minor"),
        "info": sum(1 for v in all_violations if v.get("severity") == "info"),
    }

    return {
        "summary": summary,
        "violations": all_violations[:limit],
        "unique_subjects": len(set(v.get("subject_id") for v in all_violations)),
        "unique_rules": len(set(v.get("rule_id") for v in all_violations))
    }


# ---------------------------------------------------------------------------
# Serve React frontend build (production / Railway deployment)
# ---------------------------------------------------------------------------
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Always mount assets if the directory exists
_assets_dir = os.path.join(FRONTEND_BUILD, "assets")
if os.path.exists(_assets_dir):
    app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    """Catch-all: return index.html so React Router handles client-side routing."""
    index = os.path.join(FRONTEND_BUILD, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    # Fallback if frontend not built
    from fastapi.responses import JSONResponse
    return JSONResponse({"message": "Frontend not built. API is running.", "docs": "/docs"})


if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("Clinical Trial Monitoring API - SQLite Local Version")
    print("Protocol: NVX-1218.22")
    print("=" * 70)
    print("\nStarting server at http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000)
