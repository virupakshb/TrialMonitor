"""
FastAPI Backend for Clinical Trial Monitoring System
Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
Sponsor: NexaVance Therapeutics Inc.

Simple REST API to serve synthetic clinical trial data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

app = FastAPI(
    title="Clinical Trial Monitoring API",
    description="API for NVX-1218.22 Clinical Trial Data",
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

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'clinical_trial'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

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
            "queries": "/api/queries"
        }
    }

# ============================================================================
# PROTOCOL ENDPOINTS
# ============================================================================

@app.get("/api/protocol")
def get_protocol():
    """Get protocol information"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM protocol_info LIMIT 1")
    protocol = cur.fetchone()
    cur.close()
    conn.close()
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return dict(protocol)

# ============================================================================
# SITE ENDPOINTS
# ============================================================================

@app.get("/api/sites")
def get_sites():
    """Get all sites"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sites ORDER BY site_id")
    sites = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(site) for site in sites]

@app.get("/api/sites/{site_id}")
def get_site(site_id: str):
    """Get specific site"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sites WHERE site_id = %s", (site_id,))
    site = cur.fetchone()
    cur.close()
    conn.close()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return dict(site)

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM subjects WHERE 1=1"
    params = []
    
    if site_id:
        query += " AND site_id = %s"
        params.append(site_id)
    
    if treatment_arm:
        query += " AND treatment_arm = %s"
        params.append(treatment_arm)
    
    if status:
        query += " AND study_status = %s"
        params.append(status)
    
    query += f" ORDER BY subject_id LIMIT %s"
    params.append(limit)
    
    cur.execute(query, params)
    subjects = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(subject) for subject in subjects]

@app.get("/api/subjects/{subject_id}")
def get_subject(subject_id: str):
    """Get specific subject"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subjects WHERE subject_id = %s", (subject_id,))
    subject = cur.fetchone()
    cur.close()
    conn.close()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return dict(subject)

# ============================================================================
# DEMOGRAPHICS ENDPOINT
# ============================================================================

@app.get("/api/demographics/{subject_id}")
def get_demographics(subject_id: str):
    """Get subject demographics"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM demographics WHERE subject_id = %s", (subject_id,))
    demo = cur.fetchone()
    cur.close()
    conn.close()
    
    if not demo:
        raise HTTPException(status_code=404, detail="Demographics not found")
    
    return dict(demo)

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM visits WHERE 1=1"
    params = []
    
    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)
    
    if visit_status:
        query += " AND visit_status = %s"
        params.append(visit_status)
    
    query += f" ORDER BY subject_id, visit_number LIMIT %s"
    params.append(limit)
    
    cur.execute(query, params)
    visits = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(visit) for visit in visits]

# ============================================================================
# VITAL SIGNS ENDPOINT
# ============================================================================

@app.get("/api/vitals/{subject_id}")
def get_vitals(subject_id: str):
    """Get vital signs for subject"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM vital_signs 
        WHERE subject_id = %s 
        ORDER BY assessment_date
    """, (subject_id,))
    vitals = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(vital) for vital in vitals]

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM laboratory_results WHERE subject_id = %s"
    params = [subject_id]
    
    if lab_category:
        query += " AND lab_category = %s"
        params.append(lab_category)
    
    if abnormal_only:
        query += " AND abnormal_flag != 'Normal'"
    
    query += " ORDER BY collection_date, lab_category, test_name"
    
    cur.execute(query, params)
    labs = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(lab) for lab in labs]

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM adverse_events WHERE 1=1"
    params = []
    
    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)
    
    if severity:
        query += " AND severity = %s"
        params.append(severity)
    
    if seriousness:
        query += " AND seriousness = %s"
        params.append(seriousness)
    
    if ongoing is not None:
        query += " AND ongoing = %s"
        params.append(ongoing)
    
    query += f" ORDER BY onset_date DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(query, params)
    aes = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(ae) for ae in aes]

# ============================================================================
# MEDICAL HISTORY ENDPOINT
# ============================================================================

@app.get("/api/medical-history/{subject_id}")
def get_medical_history(subject_id: str):
    """Get medical history for subject"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM medical_history 
        WHERE subject_id = %s 
        ORDER BY diagnosis_date DESC
    """, (subject_id,))
    history = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(h) for h in history]

# ============================================================================
# CONCOMITANT MEDICATIONS ENDPOINT
# ============================================================================

@app.get("/api/conmeds/{subject_id}")
def get_conmeds(subject_id: str):
    """Get concomitant medications for subject"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM concomitant_medications 
        WHERE subject_id = %s 
        ORDER BY start_date
    """, (subject_id,))
    conmeds = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(cm) for cm in conmeds]

# ============================================================================
# TUMOR ASSESSMENTS ENDPOINT
# ============================================================================

@app.get("/api/tumor-assessments/{subject_id}")
def get_tumor_assessments(subject_id: str):
    """Get tumor assessments for subject"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM tumor_assessments 
        WHERE subject_id = %s 
        ORDER BY assessment_date
    """, (subject_id,))
    assessments = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(assessment) for assessment in assessments]

# ============================================================================
# ECG ENDPOINT
# ============================================================================

@app.get("/api/ecg/{subject_id}")
def get_ecg(subject_id: str):
    """Get ECG results for subject"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ecg_results 
        WHERE subject_id = %s 
        ORDER BY ecg_date
    """, (subject_id,))
    ecgs = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(ecg) for ecg in ecgs]

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM protocol_deviations WHERE 1=1"
    params = []
    
    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)
    
    if deviation_type:
        query += " AND deviation_type = %s"
        params.append(deviation_type)
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if severity:
        query += " AND severity = %s"
        params.append(severity)
    
    query += f" ORDER BY deviation_date DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(query, params)
    deviations = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(deviation) for deviation in deviations]

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    query_sql = "SELECT * FROM queries WHERE 1=1"
    params = []
    
    if subject_id:
        query_sql += " AND subject_id = %s"
        params.append(subject_id)
    
    if query_status:
        query_sql += " AND query_status = %s"
        params.append(query_status)
    
    if priority:
        query_sql += " AND priority = %s"
        params.append(priority)
    
    query_sql += f" ORDER BY query_date DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(query_sql, params)
    queries = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(q) for q in queries]

# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@app.get("/api/statistics")
def get_statistics():
    """Get overall statistics"""
    conn = get_db_connection()
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
    
    cur.close()
    conn.close()
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
