"""
FastAPI Backend for Clinical Trial Monitoring System - SQLite Version
Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
Sponsor: NexaVance Therapeutics Inc.

Local development API using SQLite database
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
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
load_dotenv(_env_path, override=False)

# Add project root to path so rules_engine can be imported
sys.path.insert(0, os.path.dirname(__file__))

# Shared state for batch job progress
_batch_jobs: Dict[str, Any] = {}

# ============================================================================
# RAG MODULE — Protocol document chunks + in-memory embeddings
# ============================================================================
# Loaded once at startup; used by /api/chat for deep protocol questions.

_rag_store: Dict[str, Any] = {
    "chunks": [],       # list of {"section": str, "text": str}
    "embeddings": None, # numpy array (N, D)
    "ready": False,
}

def _extract_protocol_chunks() -> list:
    """
    Extract text chunks from protocol_synopsis_v3.pdf.
    Falls back to structured DB fields if PDF cannot be read.
    Returns list of {"section": str, "text": str}.
    """
    chunks = []
    pdf_path = os.path.join(os.path.dirname(__file__), "tmf_documents", "study", "protocol_synopsis_v3.pdf")

    # Try PDF extraction first
    if os.path.exists(pdf_path):
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

            # Split into sections by detecting uppercase section headers
            import re
            # Split on lines that look like section headers (all caps, short)
            section_pattern = re.compile(r'\n([A-Z][A-Z\s/\-]{4,50})\n')
            parts = section_pattern.split(full_text)

            if len(parts) >= 3:
                # parts = [pre-text, header1, body1, header2, body2, ...]
                for i in range(1, len(parts) - 1, 2):
                    header = parts[i].strip()
                    body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                    if body and len(body) > 30:
                        chunks.append({"section": header, "text": f"{header}\n{body}"})
            else:
                # Couldn't split by headers — use whole document as one chunk
                chunks.append({"section": "Protocol Synopsis", "text": full_text})

            if chunks:
                return chunks
        except Exception:
            pass  # Fall through to DB fallback

    # Fallback: use structured DB fields as chunks
    try:
        import sqlite3 as _sq
        _db = os.path.join(os.path.dirname(__file__), 'clinical_trial.db')
        if os.path.exists(_db):
            con = _sq.connect(_db)
            cur = con.cursor()
            cur.execute("""
                SELECT protocol_number, protocol_name, phase, indication, sponsor_name,
                       primary_objective, primary_endpoint, secondary_endpoints,
                       key_inclusion_criteria, key_exclusion_criteria,
                       dosing_regimen, visit_schedule_summary, ae_reporting_rules,
                       randomisation_ratio, planned_sample_size
                FROM protocol_info LIMIT 1
            """)
            row = cur.fetchone()
            con.close()
            if row:
                cols = ["protocol_number","protocol_name","phase","indication","sponsor_name",
                        "primary_objective","primary_endpoint","secondary_endpoints",
                        "key_inclusion_criteria","key_exclusion_criteria",
                        "dosing_regimen","visit_schedule_summary","ae_reporting_rules",
                        "randomisation_ratio","planned_sample_size"]
                p = dict(zip(cols, row))
                section_map = [
                    ("Protocol Overview", f"Protocol: {p['protocol_number']} — {p['protocol_name']}\nPhase: {p['phase']} | Indication: {p['indication']} | Sponsor: {p['sponsor_name']}\nPlanned Sample Size: {p['planned_sample_size']}"),
                    ("Primary and Secondary Endpoints", f"Primary Objective: {p['primary_objective']}\nPrimary Endpoint: {p['primary_endpoint']}\nSecondary Endpoints: {p['secondary_endpoints']}"),
                    ("Inclusion Criteria", f"Key Inclusion Criteria:\n{p['key_inclusion_criteria']}"),
                    ("Exclusion Criteria", f"Key Exclusion Criteria:\n{p['key_exclusion_criteria']}"),
                    ("Dosing Regimen", f"Dosing Regimen:\n{p['dosing_regimen']}"),
                    ("Visit Schedule", f"Visit Schedule:\n{p['visit_schedule_summary']}"),
                    ("AE Reporting Rules", f"Adverse Event Reporting Rules:\n{p['ae_reporting_rules']}"),
                    ("Randomisation", f"Randomisation:\n{p['randomisation_ratio']}"),
                ]
                for section, text in section_map:
                    if text and text.strip():
                        chunks.append({"section": section, "text": text})
    except Exception:
        pass

    return chunks


def _cosine_similarity(a, b):
    """Compute cosine similarity between two 1-D numpy arrays."""
    import numpy as np
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _build_rag_store():
    """
    Build the in-memory RAG store at startup:
    1. Extract protocol chunks from PDF (or DB fallback)
    2. Embed each chunk using Anthropic embeddings
    Store results in _rag_store for use during chat.
    """
    global _rag_store
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return  # Can't embed without key; RAG stays disabled

    try:
        import numpy as np
        from anthropic import Anthropic as _Ant

        chunks = _extract_protocol_chunks()
        if not chunks:
            return

        client = _Ant(api_key=api_key)
        embeddings = []
        for chunk in chunks:
            resp = client.embeddings.create(
                model="voyage-3",
                input=[chunk["text"]],
            )
            embeddings.append(resp.embeddings[0].embedding)

        _rag_store["chunks"] = chunks
        _rag_store["embeddings"] = np.array(embeddings, dtype="float32")
        _rag_store["ready"] = True
        print(f"   ✓ RAG store built: {len(chunks)} protocol chunks embedded")
    except Exception as e:
        print(f"   ⚠ RAG store build failed (non-fatal): {e}")


def _rag_retrieve(query: str, top_k: int = 2) -> str:
    """
    Retrieve the top-k most relevant protocol chunks for a query.
    Returns concatenated text of best matching chunks.
    Returns empty string if RAG store not ready.
    """
    if not _rag_store["ready"]:
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    try:
        import numpy as np
        from anthropic import Anthropic as _Ant

        client = _Ant(api_key=api_key, timeout=8.0)
        resp = client.embeddings.create(
            model="voyage-3",
            input=[query],
        )
        q_emb = np.array(resp.embeddings[0].embedding, dtype="float32")

        store_embs = _rag_store["embeddings"]
        scores = [_cosine_similarity(q_emb, store_embs[i]) for i in range(len(store_embs))]
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        retrieved = []
        for idx in top_indices:
            if scores[idx] > 0.3:  # Minimum relevance threshold
                retrieved.append(_rag_store["chunks"][idx]["text"])

        return "\n\n---\n\n".join(retrieved)
    except Exception:
        return ""

app = FastAPI(
    title="Clinical Trial Monitoring API",
    description="API for NVX-1218.22 Clinical Trial Data (SQLite Version)",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    """Build RAG store in background thread so startup is non-blocking."""
    t = threading.Thread(target=_build_rag_store, daemon=True)
    t.start()

# ── Usage logging middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def usage_logging_middleware(request: Request, call_next):
    """Log every API request to usage_logs table for usage analytics."""
    import time as _time
    start = _time.time()
    response = await call_next(request)
    ms = int((_time.time() - start) * 1000)

    endpoint = request.url.path
    # Skip static assets, favicon and health-check-style paths
    _skip_prefixes = ("/assets/", "/favicon", "/_vite", "/@")
    if not any(endpoint.startswith(s) for s in _skip_prefixes):
        try:
            session_id = request.headers.get("X-Session-ID", "")
            # X-Forwarded-For is set by Railway's proxy; fall back to direct client IP
            ip = (request.headers.get("X-Forwarded-For", "") or "").split(",")[0].strip()
            if not ip and request.client:
                ip = request.client.host
            ua = request.headers.get("User-Agent", "")[:200]
            method = request.method
            status = response.status_code
            # message_text / site_id set by /api/chat endpoint via request.state
            message_text = getattr(request.state, "chat_message", None)
            site_id_log = getattr(request.state, "chat_site_id", None)

            with get_logs_db() as conn:
                conn.execute("""
                    INSERT INTO usage_logs
                        (session_id, ip_address, user_agent, endpoint, method,
                         status_code, response_ms, message_text, site_id, timestamp)
                    VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
                """, (session_id, ip[:50], ua, endpoint, method,
                      status, ms, message_text, site_id_log))
                conn.commit()
        except Exception:
            pass  # Never let logging failure affect the response

    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path — main clinical trial DB (re-seeded on every deploy)
DB_PATH = os.path.join(os.path.dirname(__file__), 'clinical_trial.db')

# Persistent logs DB — stored on Railway Volume at /data, survives redeploys
# Falls back to local file for development
_LOGS_DB_DEFAULT = os.path.join(os.path.dirname(__file__), 'access_logs.db')
LOGS_DB_PATH = os.environ.get('LOGS_DB', _LOGS_DB_DEFAULT)

def _init_logs_db():
    """Create usage_logs table in the persistent logs DB if it doesn't exist."""
    os.makedirs(os.path.dirname(LOGS_DB_PATH) if os.path.dirname(LOGS_DB_PATH) else '.', exist_ok=True)
    conn = sqlite3.connect(LOGS_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER,
            response_ms INTEGER,
            message_text TEXT,
            site_id TEXT,
            timestamp TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

# Initialise logs DB at startup
_init_logs_db()

@contextmanager
def get_db():
    """Context manager for main clinical trial database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_logs_db():
    """Context manager for persistent access logs database (survives redeploys)"""
    conn = sqlite3.connect(LOGS_DB_PATH)
    conn.row_factory = sqlite3.Row
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
    """Serve React frontend if built (production), otherwise return API info (local dev)."""
    index = os.path.join(os.path.dirname(__file__), "frontend", "dist", "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    # Local dev fallback — no frontend build present
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


@app.get("/api/admin/access-logs")
def get_access_logs():
    """Return access log summary: unique sessions by IP, user-agent, time, endpoints hit."""
    with get_logs_db() as conn:
        cur = conn.cursor()

        # Total requests (excluding static assets - already filtered at log time)
        cur.execute("SELECT COUNT(*) FROM usage_logs")
        total_requests = cur.fetchone()[0]

        # Unique IPs
        cur.execute("SELECT COUNT(DISTINCT ip_address) FROM usage_logs WHERE ip_address != ''")
        unique_ips = cur.fetchone()[0]

        # Unique sessions
        cur.execute("SELECT COUNT(DISTINCT session_id) FROM usage_logs WHERE session_id != ''")
        unique_sessions = cur.fetchone()[0]

        # Per-IP summary: first seen, last seen, request count, endpoints, user agents
        cur.execute("""
            SELECT
                ip_address,
                COUNT(*) as request_count,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen,
                COUNT(DISTINCT session_id) as sessions,
                GROUP_CONCAT(DISTINCT endpoint) as endpoints,
                GROUP_CONCAT(DISTINCT user_agent) as user_agents
            FROM usage_logs
            WHERE ip_address != ''
            GROUP BY ip_address
            ORDER BY last_seen DESC
        """)
        rows = cur.fetchall()
        per_ip = []
        for r in rows:
            per_ip.append({
                "ip": r[0],
                "request_count": r[1],
                "first_seen": r[2],
                "last_seen": r[3],
                "sessions": r[4],
                "endpoints": r[5].split(",") if r[5] else [],
                "user_agents": list(set(r[6].split(",") if r[6] else [])),
            })

        # Recent activity (last 50 requests)
        cur.execute("""
            SELECT timestamp, ip_address, endpoint, method, status_code, response_ms,
                   user_agent, message_text, site_id
            FROM usage_logs
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        recent = [dict_from_row(r) for r in cur.fetchall()]

        # Copilot questions asked
        cur.execute("""
            SELECT timestamp, ip_address, message_text, site_id
            FROM usage_logs
            WHERE message_text IS NOT NULL AND message_text != ''
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        chat_logs = [dict_from_row(r) for r in cur.fetchall()]

        # Hourly activity breakdown
        cur.execute("""
            SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour,
                   COUNT(*) as requests,
                   COUNT(DISTINCT ip_address) as unique_ips
            FROM usage_logs
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 48
        """)
        hourly = [dict_from_row(r) for r in cur.fetchall()]

    return {
        "summary": {
            "total_requests": total_requests,
            "unique_ips": unique_ips,
            "unique_sessions": unique_sessions,
        },
        "per_ip": per_ip,
        "recent_activity": recent,
        "copilot_questions": chat_logs,
        "hourly_breakdown": hourly,
    }


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
# ═══════════════════════════════════════════════════════════════════════════════
# CTMS — MONITORING VISITS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

def _calculate_risk(open_findings: int, critical_findings: int, enrollment_gap: int, planned_enrollment: int) -> str:
    """Deterministic site risk score: High / Medium / Low."""
    gap_pct = (enrollment_gap / planned_enrollment * 100) if planned_enrollment > 0 else 0
    if critical_findings > 0 or open_findings >= 3 or gap_pct >= 40:
        return 'High'
    elif open_findings >= 2 or gap_pct >= 20:
        return 'Medium'
    return 'Low'

@app.get("/api/ctms/site/{site_id}")
def get_ctms_site(site_id: str):
    """Get site details + monitoring visit timeline for a site."""
    import json as _json
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sites WHERE site_id = ?", (site_id,))
        site = cur.fetchone()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        site_data = dict_from_row(site)

        cur.execute("""
            SELECT mv.*,
                   (SELECT COUNT(*) FROM monitoring_visit_subjects mvs WHERE mvs.monitoring_visit_id = mv.monitoring_visit_id) as subject_count,
                   (SELECT COUNT(*) FROM visit_findings vf WHERE vf.monitoring_visit_id = mv.monitoring_visit_id AND vf.status = 'Open') as open_findings,
                   (SELECT report_status FROM visit_reports vr WHERE vr.monitoring_visit_id = mv.monitoring_visit_id LIMIT 1) as report_status
            FROM monitoring_visits mv
            WHERE mv.site_id = ?
            ORDER BY mv.planned_date ASC
        """, (site_id,))
        visits = [dict_from_row(r) for r in cur.fetchall()]

    for v in visits:
        if v.get('visit_objectives'):
            try:
                v['visit_objectives'] = _json.loads(v['visit_objectives'])
            except Exception:
                pass

    return {"site": site_data, "monitoring_visits": visits}


@app.get("/api/ctms/sites-overview")
def get_ctms_sites_overview():
    """
    Returns all sites with aggregated CRA workstation stats:
    subject count, open/critical findings, TMF readiness score, risk level.
    Also returns protocol banner for the study header.
    """
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM sites ORDER BY site_id")
        sites = [dict_from_row(r) for r in cur.fetchall()]

        for site in sites:
            sid = site['site_id']

            # Active subjects (not screen failed or withdrawn)
            cur.execute(
                "SELECT COUNT(*) FROM subjects WHERE site_id = ? AND study_status NOT IN ('Screen Failed','Withdrawn')",
                (sid,)
            )
            site['active_subjects'] = cur.fetchone()[0]

            # Open findings across all visits for this site
            cur.execute("""
                SELECT COUNT(*) FROM visit_findings vf
                JOIN monitoring_visits mv ON mv.monitoring_visit_id = vf.monitoring_visit_id
                WHERE mv.site_id = ? AND vf.status = 'Open'
            """, (sid,))
            site['open_findings'] = cur.fetchone()[0]

            # Critical open findings
            cur.execute("""
                SELECT COUNT(*) FROM visit_findings vf
                JOIN monitoring_visits mv ON mv.monitoring_visit_id = vf.monitoring_visit_id
                WHERE mv.site_id = ? AND vf.status = 'Open' AND vf.severity = 'Critical'
            """, (sid,))
            site['critical_findings'] = cur.fetchone()[0]

            # Visit stats
            cur.execute("""
                SELECT COUNT(*), MAX(COALESCE(actual_date, planned_date))
                FROM monitoring_visits WHERE site_id = ?
            """, (sid,))
            row = cur.fetchone()
            site['visit_count'] = row[0]
            site['last_visit_date'] = row[1]

            # Next planned visit
            cur.execute("""
                SELECT planned_date FROM monitoring_visits
                WHERE site_id = ? AND status IN ('Planned','Confirmed')
                ORDER BY planned_date ASC LIMIT 1
            """, (sid,))
            nv = cur.fetchone()
            site['next_visit_date'] = nv[0] if nv else None

            # TMF score: present / total mandatory required
            cur.execute("SELECT COUNT(*) FROM tmf_requirements WHERE is_mandatory = 1")
            total_req = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM tmf_documents
                WHERE site_id = ? AND status = 'Present'
            """, (sid,))
            present = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM tmf_documents WHERE site_id = ? AND status = 'Missing'", (sid,))
            missing = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM tmf_documents WHERE site_id = ? AND status = 'Expiring'", (sid,))
            expiring = cur.fetchone()[0]
            site['tmf_total_required'] = total_req
            site['tmf_present'] = present
            site['tmf_missing'] = missing
            site['tmf_expiring'] = expiring
            site['tmf_score'] = round(present / total_req * 100) if total_req > 0 else 0

            # Risk score
            enrollment_gap = max(0, (site.get('planned_enrollment') or 0) - (site.get('actual_enrollment') or 0))
            site['enrollment_gap'] = enrollment_gap
            site['risk'] = _calculate_risk(
                open_findings=site['open_findings'],
                critical_findings=site['critical_findings'],
                enrollment_gap=enrollment_gap,
                planned_enrollment=site.get('planned_enrollment') or 1
            )

        # Protocol banner
        cur.execute("""
            SELECT protocol_number, protocol_name, phase, indication, sponsor_name,
                   study_start_date, estimated_completion_date, planned_sample_size
            FROM protocol_info LIMIT 1
        """)
        protocol = dict_from_row(cur.fetchone())

    return {"protocol": protocol, "sites": sites}


# ─────────────────────────────────────────────────────────────────────────────
# TMF ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/tmf/site/{site_id}")
def get_tmf_site(site_id: str):
    """TMF document compliance status for a site."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT td.*, tr.is_mandatory, tr.validity_months
            FROM tmf_documents td
            LEFT JOIN tmf_requirements tr ON tr.document_type = td.document_type
            WHERE td.site_id = ?
            ORDER BY td.category, td.document_type
        """, (site_id,))
        docs = [dict_from_row(r) for r in cur.fetchall()]

        cur.execute("SELECT COUNT(*) FROM tmf_requirements WHERE is_mandatory = 1")
        total_req = cur.fetchone()[0]

    present = sum(1 for d in docs if d['status'] == 'Present')
    missing = sum(1 for d in docs if d['status'] == 'Missing')
    expiring = sum(1 for d in docs if d['status'] == 'Expiring')
    superseded = sum(1 for d in docs if d['status'] == 'Superseded')
    tmf_score = round(present / total_req * 100) if total_req > 0 else 0

    return {
        "site_id": site_id,
        "tmf_score": tmf_score,
        "total_required": total_req,
        "present": present,
        "missing": missing,
        "expiring": expiring,
        "superseded": superseded,
        "documents": docs
    }


@app.get("/api/tmf/files/{site_id}/{filename}")
def serve_tmf_file(site_id: str, filename: str):
    """Serve a TMF PDF document for a site."""
    # Security: only allow alphanumeric, dash, underscore, dot
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename) or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = os.path.join(os.path.dirname(__file__), "tmf_documents", f"site_{site_id}", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(file_path, media_type="application/pdf",
                        headers={"Content-Disposition": f"inline; filename={filename}"})


@app.get("/api/tmf/files/study/{filename}")
def serve_tmf_study_file(filename: str):
    """Serve a study-level TMF PDF document."""
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename) or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = os.path.join(os.path.dirname(__file__), "tmf_documents", "study", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(file_path, media_type="application/pdf",
                        headers={"Content-Disposition": f"inline; filename={filename}"})


# ─────────────────────────────────────────────────────────────────────────────
# CRA COPILOT CHAT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/chat")
def cra_copilot_chat(body: dict, request: Request):
    """
    CRA Copilot — context-aware AI assistant.
    Receives: { message, site_id, visit_id, history }
    Returns: { type, text, document, table }
    """
    import json as _json

    message = body.get('message', '').strip()
    site_id = body.get('site_id') or ''
    visit_id = body.get('visit_id')
    history = body.get('history', [])

    # Expose message + site_id to usage logging middleware via request.state
    request.state.chat_message = message[:500] if message else None
    request.state.chat_site_id = site_id or None

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        from anthropic import Anthropic as _Anthropic
    except ImportError as e:
        return {"type": "text", "text": f"CRA Copilot unavailable — anthropic library not installed: {e}", "document": None, "table": None}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "type": "text",
            "text": "CRA Copilot is not available — ANTHROPIC_API_KEY not configured.",
            "document": None,
            "table": None
        }

    # ── Build context from DB ──────────────────────────────────────────────
    with get_db() as conn:
        cur = conn.cursor()

        # Protocol — full rich fields
        cur.execute("""
            SELECT protocol_number, protocol_name, phase, indication, sponsor_name,
                   primary_objective, primary_endpoint, secondary_endpoints,
                   key_inclusion_criteria, key_exclusion_criteria,
                   dosing_regimen, visit_schedule_summary, ae_reporting_rules,
                   randomisation_ratio, planned_sample_size,
                   study_start_date, estimated_completion_date
            FROM protocol_info LIMIT 1
        """)
        proto = dict_from_row(cur.fetchone()) or {}

        # Site info
        site_info = {}
        available_tmf_docs = []
        open_findings_list = []
        tmf_issues = []
        upcoming_visit = None

        if site_id:
            cur.execute("SELECT * FROM sites WHERE site_id = ?", (site_id,))
            s = cur.fetchone()
            if s:
                site_info = dict_from_row(s)

            cur.execute("""
                SELECT COUNT(*) FROM subjects
                WHERE site_id = ? AND study_status NOT IN ('Screen Failed','Withdrawn')
            """, (site_id,))
            active_count = cur.fetchone()[0]
            site_info['active_subjects'] = active_count

            # Open findings
            cur.execute("""
                SELECT vf.severity, vf.finding_type, vf.description, vf.subject_id,
                       vf.status, vf.due_date, mv.visit_label
                FROM visit_findings vf
                JOIN monitoring_visits mv ON mv.monitoring_visit_id = vf.monitoring_visit_id
                WHERE mv.site_id = ? AND vf.status = 'Open'
                ORDER BY CASE vf.severity WHEN 'Critical' THEN 1 WHEN 'Major' THEN 2 ELSE 3 END
            """, (site_id,))
            open_findings_list = [dict_from_row(r) for r in cur.fetchall()]

            # Upcoming visit
            cur.execute("""
                SELECT * FROM monitoring_visits
                WHERE site_id = ? AND status IN ('Planned','Confirmed')
                ORDER BY planned_date ASC LIMIT 1
            """, (site_id,))
            uv = cur.fetchone()
            if uv:
                upcoming_visit = dict_from_row(uv)

            # TMF issues
            cur.execute("""
                SELECT document_type, category, status, notes, expiry_date
                FROM tmf_documents
                WHERE site_id = ? AND status IN ('Missing','Expiring','Superseded')
            """, (site_id,))
            tmf_issues = [dict_from_row(r) for r in cur.fetchall()]

            # Available TMF documents (for document fetch intent)
            cur.execute("""
                SELECT document_type, title, version, file_path, status
                FROM tmf_documents WHERE site_id = ? AND file_path IS NOT NULL
            """, (site_id,))
            available_tmf_docs = [dict_from_row(r) for r in cur.fetchall()]

        # All sites summary (always loaded — supports study-wide mode)
        cur.execute("""
            SELECT s.site_id, s.site_name, s.country,
                COUNT(DISTINCT subj.subject_id) as enrolled,
                SUM(CASE WHEN vf.status='Open' THEN 1 ELSE 0 END) as open_findings,
                SUM(CASE WHEN vf.status='Open' AND vf.severity='Critical' THEN 1 ELSE 0 END) as critical_findings
            FROM sites s
            LEFT JOIN subjects subj ON subj.site_id = s.site_id
            LEFT JOIN monitoring_visits mv ON mv.site_id = s.site_id
            LEFT JOIN visit_findings vf ON vf.monitoring_visit_id = mv.monitoring_visit_id
            GROUP BY s.site_id, s.site_name, s.country
            ORDER BY s.site_id
        """)
        all_sites_summary = [dict_from_row(r) for r in cur.fetchall()]

    # ── Intent routing: classify question to decide what context to include ──
    # This avoids sending ~2,000 tokens of irrelevant context on every call.
    msg_lower = message.lower()

    _is_data_q = any(k in msg_lower for k in [
        'finding', 'enrollment', 'enrolled', 'subject', 'open', 'tmf',
        'document', 'missing', 'expiring', 'compliance', 'next visit',
        'upcoming', 'monitoring visit', 'cra', 'report', 'delegation',
        'show me', 'fetch', 'get me', 'status'
    ])
    _is_protocol_q = any(k in msg_lower for k in [
        'dosing', 'dose', 'regimen', 'criteria', 'endpoint', 'objective',
        'schedule', 'randomis', 'eligib', 'exclusion', 'inclusion',
        'ae report', 'adverse', 'primary', 'secondary', 'phase', 'arm',
        'treatment', 'placebo', 'sample size', 'indication', 'summarise',
        'summarize', 'visit schedule', 'who can', 'who cannot'
    ])
    # Default to protocol if unclear
    if not _is_data_q and not _is_protocol_q:
        _is_protocol_q = True

    # RAG only helps for deep protocol questions — skip for data/site questions
    _need_rag = _is_protocol_q and not _is_data_q
    rag_context = _rag_retrieve(message, top_k=2) if _need_rag else ""

    # ── Build system prompt (only include what's relevant) ───────────────────
    context_parts = []

    # Protocol header — always included (compact, ~120 tokens)
    context_parts.append(
        f"PROTOCOL: {proto.get('protocol_number')} — {proto.get('protocol_name')}\n"
        f"Phase: {proto.get('phase')} | Indication: {proto.get('indication')} | "
        f"Sponsor: {proto.get('sponsor_name')}\n"
        f"Randomisation: {proto.get('randomisation_ratio','')} | "
        f"N={proto.get('planned_sample_size')} | "
        f"Start: {proto.get('study_start_date')} | Est. completion: {proto.get('estimated_completion_date')}"
    )

    # Full protocol body — only for protocol questions (~600 tokens)
    if _is_protocol_q:
        context_parts.append(
            f"\nPRIMARY OBJECTIVE: {proto.get('primary_objective','')}"
            f"\nPRIMARY ENDPOINT: {proto.get('primary_endpoint','')}"
            f"\nSECONDARY ENDPOINTS: {proto.get('secondary_endpoints','')}"
            f"\n\nKEY INCLUSION CRITERIA:\n{proto.get('key_inclusion_criteria','')}"
            f"\n\nKEY EXCLUSION CRITERIA:\n{proto.get('key_exclusion_criteria','')}"
            f"\n\nDOSING REGIMEN:\n{proto.get('dosing_regimen','')}"
            f"\n\nVISIT SCHEDULE:\n{proto.get('visit_schedule_summary','')}"
            f"\n\nAE REPORTING RULES:\n{proto.get('ae_reporting_rules','')}"
        )

    # RAG chunks — only for deep protocol questions (~300 tokens max)
    if rag_context:
        context_parts.append(f"\nADDITIONAL PROTOCOL DETAIL (from protocol document):\n{rag_context}")

    # Site context — only when a site is selected
    if site_id and site_info:
        context_parts.append(
            f"\nCURRENT SITE: Site {site_id} — {site_info.get('site_name')}, "
            f"{site_info.get('city','')}, {site_info.get('country','')}\n"
            f"PI: {site_info.get('principal_investigator')} | "
            f"Coordinator: {site_info.get('site_coordinator')}\n"
            f"Enrolled: {site_info.get('actual_enrollment')}/{site_info.get('planned_enrollment')} | "
            f"Active: {site_info.get('active_subjects')}"
        )
    else:
        context_parts.append("\nCONTEXT: Study-level (no specific site selected)")

    # Open findings — always include when site selected (core CRA data)
    if open_findings_list:
        findings_text = "\n".join([
            f"  [{f['severity']}] {f['finding_type']} | Subj {f.get('subject_id','N/A')} | {f['description']} | Due: {f.get('due_date','TBD')}"
            for f in open_findings_list
        ])
        context_parts.append(f"\nOPEN FINDINGS ({len(open_findings_list)}):\n{findings_text}")
    elif site_id:
        context_parts.append("\nOPEN FINDINGS: None")

    # Next visit — always include when site selected
    if upcoming_visit:
        context_parts.append(
            f"\nNEXT VISIT: {upcoming_visit.get('visit_label')} on {upcoming_visit.get('planned_date')} "
            f"| CRA: {upcoming_visit.get('cra_name')} | Status: {upcoming_visit.get('status')}"
        )

    # TMF issues — always include when site selected
    if tmf_issues:
        tmf_text = "\n".join([
            f"  [{t['status']}] {t['document_type']} ({t['category']})"
            for t in tmf_issues
        ])
        context_parts.append(f"\nTMF ISSUES ({len(tmf_issues)}):\n{tmf_text}")

    # TMF available docs — only include when site selected (for document fetch)
    if available_tmf_docs:
        doc_list = "\n".join([
            f"  {d['document_type']}: \"{d['title']}\" v{d.get('version','')} | {d.get('file_path','')}"
            for d in available_tmf_docs
        ])
        context_parts.append(f"\nAVAILABLE TMF DOCUMENTS:\n{doc_list}")

    # All-sites summary — only in study-wide mode (no site selected)
    if not site_id:
        all_sites_text = "\n".join([
            f"  Site {s['site_id']}: {s['site_name']} ({s['country']}) — "
            f"{s['enrolled']} enrolled, {s['open_findings'] or 0} open findings "
            f"({s['critical_findings'] or 0} critical)"
            for s in all_sites_summary
        ])
        context_parts.append(f"\nALL SITES SUMMARY:\n{all_sites_text}")

    mode_label = f"Site {site_id} — {site_info.get('site_name','')}" if (site_id and site_info) else "Study Level"

    system_prompt = f"""You are CRA Copilot, an expert AI assistant for CRAs on trial NVX-1218.22 (NovaPlex-450, Advanced NSCLC).
Context: {mode_label}

{"".join(context_parts)}

ALWAYS respond in valid JSON (no markdown, no extra text):
{{"intent":"document_fetch|data_answer|protocol_qa","text":"...","document_type":null,"file_path":null,"document_title":null,"data_table":null}}

Rules:
- protocol_qa: answer from protocol data above, cite actual values
- data_answer: use data_table with headers+rows for findings/enrollment/subjects
- document_fetch: set file_path exactly from AVAILABLE TMF DOCUMENTS list
- study-wide questions: use ALL SITES SUMMARY
- unknown topic: say so and suggest where to find it
- Always concise, accurate, professional"""

    # ── Call LLM ────────────────────────────────────────────────────────────
    client = _Anthropic(api_key=api_key, timeout=25.0)

    messages = []
    # Conversation history — last 3 turns (6 messages was excessive)
    for h in history[-3:]:
        if h.get('role') in ('user', 'assistant') and h.get('content'):
            messages.append({"role": h['role'], "content": str(h['content'])})

    messages.append({"role": "user", "content": message})

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=system_prompt,
            messages=messages
        )
        raw = response.content[0].text.strip()

        # Parse JSON response
        try:
            if raw.startswith('```'):
                raw = raw.split('```')[1]
                if raw.startswith('json'):
                    raw = raw[4:]
            llm_data = _json.loads(raw)
        except Exception:
            # Fallback: return as plain text
            return {"type": "text", "text": raw, "document": None, "table": None}

        intent = llm_data.get('intent', 'text')
        text = llm_data.get('text', raw)
        doc_result = None
        table_result = None

        if intent == 'document_fetch':
            file_path = llm_data.get('file_path')
            doc_title = llm_data.get('document_title', llm_data.get('document_type', 'Document'))
            if file_path:
                # Build the API URL from the file_path
                # file_path format: tmf_documents/site_101/delegation_log_v1.pdf
                parts = file_path.replace('\\', '/').split('/')
                if len(parts) >= 3:
                    folder = parts[1]  # e.g. site_101
                    fname = parts[2]
                    if folder.startswith('site_'):
                        sid_from_path = folder.replace('site_', '')
                        doc_url = f"/api/tmf/files/{sid_from_path}/{fname}"
                    else:
                        doc_url = f"/api/tmf/files/study/{fname}"
                else:
                    doc_url = None
                doc_result = {
                    "title": doc_title,
                    "url": doc_url,
                    "file_path": file_path
                }

        if llm_data.get('data_table'):
            table_result = llm_data['data_table']

        return {
            "type": intent,
            "text": text,
            "document": doc_result,
            "table": table_result
        }

    except Exception as e:
        return {
            "type": "text",
            "text": f"An error occurred: {str(e)[:200]}",
            "document": None,
            "table": None
        }


@app.get("/api/ctms/monitoring-visits/{monitoring_visit_id}")
def get_monitoring_visit(monitoring_visit_id: int):
    """Get full detail for one monitoring visit including subjects, findings, report."""
    import json as _json
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM monitoring_visits WHERE monitoring_visit_id = ?", (monitoring_visit_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Monitoring visit not found")
        visit = dict_from_row(row)

        if visit.get('visit_objectives'):
            try:
                visit['visit_objectives'] = _json.loads(visit['visit_objectives'])
            except Exception:
                pass

        # Subjects
        cur.execute("""
            SELECT mvs.*, s.study_status, s.treatment_arm_name
            FROM monitoring_visit_subjects mvs
            JOIN subjects s ON s.subject_id = mvs.subject_id
            WHERE mvs.monitoring_visit_id = ?
            ORDER BY CASE mvs.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
        """, (monitoring_visit_id,))
        subjects = [dict_from_row(r) for r in cur.fetchall()]

        # Findings
        cur.execute("""
            SELECT * FROM visit_findings WHERE monitoring_visit_id = ?
            ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'Major' THEN 2 ELSE 3 END, created_at
        """, (monitoring_visit_id,))
        findings = [dict_from_row(r) for r in cur.fetchall()]

        # Report
        cur.execute("SELECT * FROM visit_reports WHERE monitoring_visit_id = ? LIMIT 1", (monitoring_visit_id,))
        row = cur.fetchone()
        report = dict_from_row(row) if row else None

    return {
        "visit": visit,
        "subjects": subjects,
        "findings": findings,
        "report": report
    }


@app.put("/api/ctms/monitoring-visits/{monitoring_visit_id}/confirm")
def confirm_monitoring_visit(monitoring_visit_id: int):
    """CRA confirms the visit date — status moves from Planned to Confirmed."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE monitoring_visits
            SET status = 'Confirmed', updated_at = datetime('now')
            WHERE monitoring_visit_id = ? AND status = 'Planned'
        """, (monitoring_visit_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=400, detail="Visit not in Planned status or not found")
        conn.commit()
    return {"success": True, "status": "Confirmed"}


@app.post("/api/ctms/monitoring-visits/{monitoring_visit_id}/generate-prep")
def generate_visit_prep(monitoring_visit_id: int):
    """
    Generate visit prep agenda — deterministic prioritisation of site subjects.
    Reviews open queries, deviations, AEs, violations for site 101 subjects
    and assigns High/Medium/Low priority with reasons. No LLM used (cost-conscious).
    """
    import json as _json
    import hashlib

    with get_db() as conn:
        cur = conn.cursor()

        # Get the monitoring visit
        cur.execute("SELECT * FROM monitoring_visits WHERE monitoring_visit_id = ?", (monitoring_visit_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Monitoring visit not found")
        visit = dict_from_row(row)
        site_id = visit['site_id']

        # Get all subjects at this site
        cur.execute("SELECT subject_id, study_status FROM subjects WHERE site_id = ?", (site_id,))
        all_subjects = cur.fetchall()

        # Clear existing subject assignments for this visit
        cur.execute("DELETE FROM monitoring_visit_subjects WHERE monitoring_visit_id = ?", (monitoring_visit_id,))

        subject_rows = []
        for (subject_id, study_status) in all_subjects:
            # Count open queries
            cur.execute("SELECT COUNT(*) FROM queries WHERE subject_id = ? AND query_status = 'Open'", (subject_id,))
            open_queries = cur.fetchone()[0]

            # Count queries open > 14 days
            cur.execute("""
                SELECT COUNT(*) FROM queries
                WHERE subject_id = ? AND query_status = 'Open'
                AND julianday('now') - julianday(query_date) > 14
            """, (subject_id,))
            aged_queries = cur.fetchone()[0]

            # Count open deviations
            cur.execute("SELECT COUNT(*) FROM protocol_deviations WHERE subject_id = ? AND status = 'Open'", (subject_id,))
            open_devs = cur.fetchone()[0]

            # Count serious AEs
            cur.execute("SELECT COUNT(*) FROM adverse_events WHERE subject_id = ? AND seriousness = 'Yes' AND (ongoing = 1 OR resolution_date IS NULL)", (subject_id,))
            serious_aes = cur.fetchone()[0]

            # Count Grade 3+ AEs
            cur.execute("SELECT COUNT(*) FROM adverse_events WHERE subject_id = ? AND ctcae_grade >= 3 AND (ongoing = 1 OR resolution_date IS NULL)", (subject_id,))
            high_grade_aes = cur.fetchone()[0]

            # Missed visits
            cur.execute("SELECT COUNT(*) FROM visits WHERE subject_id = ? AND missed_visit = 1", (subject_id,))
            missed = cur.fetchone()[0]

            # Assign priority
            reasons = []
            if serious_aes > 0:
                reasons.append(f"{serious_aes} ongoing serious AE(s) requiring SAE documentation review")
            if high_grade_aes > 0:
                reasons.append(f"{high_grade_aes} Grade 3+ adverse event(s) ongoing")
            if open_devs > 0:
                reasons.append(f"{open_devs} open protocol deviation(s)")
            if aged_queries > 0:
                reasons.append(f"{aged_queries} query/queries open >14 days")
            if open_queries > 0 and aged_queries == 0:
                reasons.append(f"{open_queries} open query/queries")
            if missed > 0:
                reasons.append(f"{missed} missed visit(s)")

            if serious_aes > 0 or open_devs > 0 or high_grade_aes > 0:
                priority = 'High'
            elif aged_queries > 0 or open_queries > 1 or missed > 0:
                priority = 'Medium'
            else:
                priority = 'Low'

            priority_reason = '; '.join(reasons) if reasons else 'No active issues — routine SDV review'

            # Rough SDV percent (simulate based on subject number)
            h = int(hashlib.md5(subject_id.encode()).hexdigest(), 16) % 5
            sdv_map = {0: 100, 1: 100, 2: 85, 3: 75, 4: 60}
            sdv_pct = sdv_map[h]
            sdv_status = 'Complete' if sdv_pct == 100 else ('In Progress' if sdv_pct >= 75 else 'Not Started')

            subject_rows.append((monitoring_visit_id, subject_id, sdv_status, sdv_pct, priority, priority_reason))

        cur.executemany("""
            INSERT INTO monitoring_visit_subjects
                (monitoring_visit_id, subject_id, sdv_status, sdv_percent, priority, priority_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, subject_rows)

        # Generate objectives based on site data
        cur.execute("SELECT COUNT(*) FROM queries WHERE subject_id LIKE ? AND query_status = 'Open'", (f'{site_id}-%',))
        total_open_q = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM queries WHERE subject_id LIKE ? AND query_status = 'Open'
            AND julianday('now') - julianday(query_date) > 14
        """, (f'{site_id}-%',))
        total_aged_q = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM protocol_deviations WHERE subject_id LIKE ? AND status = 'Open'", (f'{site_id}-%',))
        total_devs = cur.fetchone()[0]
        high_priority = [r for r in subject_rows if r[4] == 'High']
        medium_priority = [r for r in subject_rows if r[4] == 'Medium']
        not_started_sdv = [r for r in subject_rows if r[2] == 'Not Started']

        objectives = [f"Priority review: {len(high_priority)} high-priority subject(s) with active safety concerns"]
        if total_open_q > 0:
            objectives.append(f"Close {total_open_q} open quer{'y' if total_open_q == 1 else 'ies'} ({total_aged_q} aged >14 days)")
        if total_devs > 0:
            objectives.append(f"Review and close {total_devs} open protocol deviation(s)")
        if not_started_sdv:
            objectives.append(f"Complete SDV for {len(not_started_sdv)} subject(s) with 0% SDV")
        if medium_priority:
            objectives.append(f"Follow up on {len(medium_priority)} medium-priority subject(s)")
        objectives.append("Verify ICF signatures for any newly consented subjects")
        objectives.append("Review corrective actions from previous visit findings")

        cur.execute("""
            UPDATE monitoring_visits
            SET prep_generated = 1, visit_objectives = ?, updated_at = datetime('now')
            WHERE monitoring_visit_id = ?
        """, (_json.dumps(objectives), monitoring_visit_id))

        conn.commit()

        # Return full prep data
        cur.execute("""
            SELECT mvs.*, s.study_status FROM monitoring_visit_subjects mvs
            JOIN subjects s ON s.subject_id = mvs.subject_id
            WHERE mvs.monitoring_visit_id = ?
            ORDER BY CASE mvs.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
        """, (monitoring_visit_id,))
        subjects_out = [dict_from_row(r) for r in cur.fetchall()]

    return {
        "success": True,
        "objectives": objectives,
        "subjects": subjects_out,
        "summary": {
            "total": len(subject_rows),
            "high": len(high_priority),
            "medium": len(medium_priority),
            "low": len(subject_rows) - len(high_priority) - len(medium_priority)
        }
    }


@app.put("/api/ctms/monitoring-visits/{monitoring_visit_id}/approve-prep")
def approve_prep(monitoring_visit_id: int):
    """CRA approves the generated prep agenda — locks it."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE monitoring_visits
            SET prep_approved = 1, status = 'Confirmed', updated_at = datetime('now')
            WHERE monitoring_visit_id = ?
        """, (monitoring_visit_id,))
        conn.commit()
    return {"success": True, "prep_approved": True}


@app.put("/api/ctms/monitoring-visits/{monitoring_visit_id}/sdv")
def update_sdv(monitoring_visit_id: int, subject_id: str, sdv_status: str, sdv_percent: int):
    """CRA updates SDV status for a subject during the visit."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE monitoring_visit_subjects
            SET sdv_status = ?, sdv_percent = ?, updated_at = datetime('now')
            WHERE monitoring_visit_id = ? AND subject_id = ?
        """, (sdv_status, sdv_percent, monitoring_visit_id, subject_id))
        conn.commit()
    return {"success": True}


@app.post("/api/ctms/monitoring-visits/{monitoring_visit_id}/findings")
def log_finding(monitoring_visit_id: int, body: dict):
    """CRA logs a finding during the visit."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visit_findings
                (monitoring_visit_id, subject_id, finding_type, description, severity,
                 assigned_to, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Open')
        """, (
            monitoring_visit_id,
            body.get('subject_id'),
            body.get('finding_type'),
            body.get('description'),
            body.get('severity'),
            body.get('assigned_to'),
            body.get('due_date')
        ))
        finding_id = cur.lastrowid
        conn.commit()
    return {"success": True, "finding_id": finding_id}


@app.put("/api/ctms/findings/{finding_id}/resolve")
def resolve_finding(finding_id: int):
    """Mark a finding as resolved."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE visit_findings
            SET status = 'Resolved', resolved_date = date('now')
            WHERE finding_id = ?
        """, (finding_id,))
        conn.commit()
    return {"success": True}


@app.post("/api/ctms/monitoring-visits/{monitoring_visit_id}/generate-report")
def generate_visit_report(monitoring_visit_id: int):
    """
    Generate a monitoring visit report draft — deterministic templating, no LLM.
    Builds the report from visit data, findings, and SDV status.
    """
    import json as _json
    from datetime import date as _date

    with get_db() as conn:
        cur = conn.cursor()

        # Visit
        cur.execute("""
            SELECT mv.*, s.site_name, s.principal_investigator, s.site_coordinator, s.city, s.state_province
            FROM monitoring_visits mv JOIN sites s ON s.site_id = mv.site_id
            WHERE mv.monitoring_visit_id = ?
        """, (monitoring_visit_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Visit not found")
        v = dict_from_row(row)
        objectives = _json.loads(v['visit_objectives']) if v.get('visit_objectives') else []

        # Subjects
        cur.execute("""
            SELECT mvs.subject_id, mvs.sdv_status, mvs.sdv_percent, mvs.priority, mvs.priority_reason
            FROM monitoring_visit_subjects mvs
            WHERE mvs.monitoring_visit_id = ?
            ORDER BY CASE mvs.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
        """, (monitoring_visit_id,))
        subjects = [dict_from_row(r) for r in cur.fetchall()]

        # Findings
        cur.execute("""
            SELECT * FROM visit_findings WHERE monitoring_visit_id = ?
            ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'Major' THEN 2 ELSE 3 END
        """, (monitoring_visit_id,))
        findings = [dict_from_row(r) for r in cur.fetchall()]

        critical_f = [f for f in findings if f['severity'] == 'Critical']
        major_f    = [f for f in findings if f['severity'] == 'Major']
        minor_f    = [f for f in findings if f['severity'] == 'Minor']
        open_f     = [f for f in findings if f['status'] == 'Open']
        resolved_f = [f for f in findings if f['status'] == 'Resolved']

        visit_date = v.get('actual_date') or v.get('planned_date')
        today = _date.today().isoformat()

        # Build report markdown
        subj_table = "| Subject | Priority | SDV Status | SDV % | Notes |\n|---------|----------|-----------|-------|-------|\n"
        for s in subjects:
            subj_table += f"| {s['subject_id']} | {s['priority']} | {s['sdv_status']} | {s['sdv_percent']}% | {(s['priority_reason'] or '')[:60]}{'...' if len(s.get('priority_reason') or '') > 60 else ''} |\n"

        obj_list = "\n".join([f"- [ ] {o}" for o in objectives]) if objectives else "- No objectives recorded"

        def findings_section(flist, label):
            if not flist:
                return f"### {label}\nNo {label.lower()} findings.\n"
            out = f"### {label}\n"
            for i, f in enumerate(flist, 1):
                subj = f"Subject {f['subject_id']} — " if f.get('subject_id') else ""
                out += f"\n**Finding {i} — {subj}{f['finding_type']}**\n"
                out += f"{f['description']}\n"
                out += f"**Assigned to:** {f.get('assigned_to', 'TBD')} | **Due:** {f.get('due_date', 'TBD')} | **Status:** {f['status']}\n"
            return out

        report = f"""# Monitoring Visit Report — {v['visit_label']}

**Site:** {v['site_id']} — {v['site_name']}, {v['city']}, {v['state_province']}
**Visit Date:** {visit_date}
**Visit Type:** {v['visit_type']} ({v['visit_label']})
**CRA:** {v['cra_name']}
**Principal Investigator:** {v['principal_investigator']}
**Site Coordinator:** {v['site_coordinator']}
**Report Generated:** {today}

---

## 1. Visit Summary

This interim monitoring visit was conducted at {v['site_name']} in accordance with the
Monitoring Plan for Protocol NVX-1218.22 (NovaPlex-450 in Advanced NSCLC).

**Subjects reviewed:** {len(subjects)}
**Total findings:** {len(findings)} ({len(critical_f)} Critical, {len(major_f)} Major, {len(minor_f)} Minor)
**Open findings:** {len(open_f)} | **Resolved at visit:** {len(resolved_f)}

---

## 2. Subjects Reviewed

{subj_table}

---

## 3. Visit Objectives

{obj_list}

---

## 4. Findings & Action Items

{findings_section(critical_f, 'Critical')}
{findings_section(major_f, 'Major')}
{findings_section(minor_f, 'Minor')}

### Resolved at This Visit
{findings_section(resolved_f, 'Resolved') if resolved_f else 'No findings resolved at this visit.'}

---

## 5. Outstanding Issues

{'- ' + chr(10) + '- '.join([f"{f['severity']} — Subject {f.get('subject_id', 'N/A')}: {f['description'][:80]}..." for f in open_f]) if open_f else 'No outstanding issues.'}

---

## 6. Next Steps & Follow-Up

- CRA to follow up on {len(open_f)} open finding(s) before next visit
- Site coordinator to ensure all action items are resolved by due dates
- Next monitoring visit to be scheduled per monitoring plan

---

*Report prepared by: {v['cra_name']}, CRA*
*Report date: {today}*
*This is a system-generated draft — please review and add CRA notes before finalising.*
"""

        # Upsert report
        cur.execute("SELECT report_id FROM visit_reports WHERE monitoring_visit_id = ?", (monitoring_visit_id,))
        existing = cur.fetchone()
        if existing:
            cur.execute("""
                UPDATE visit_reports
                SET draft_content = ?, report_status = 'Draft', updated_at = datetime('now')
                WHERE monitoring_visit_id = ?
            """, (report, monitoring_visit_id))
        else:
            cur.execute("""
                INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content)
                VALUES (?, 'Draft', ?)
            """, (monitoring_visit_id, report))

        # Mark visit as In Progress
        cur.execute("""
            UPDATE monitoring_visits SET status = 'In Progress', updated_at = datetime('now')
            WHERE monitoring_visit_id = ? AND status NOT IN ('Completed', 'Cancelled')
        """, (monitoring_visit_id,))

        conn.commit()

    return {"success": True, "report": report}


@app.put("/api/ctms/monitoring-visits/{monitoring_visit_id}/report-status")
def update_report_status(monitoring_visit_id: int, status: str, cra_notes: str = None):
    """Update report status: Draft → CRA Reviewed → Finalised."""
    valid = ['Draft', 'CRA Reviewed', 'Finalised']
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE visit_reports
            SET report_status = ?,
                cra_notes = COALESCE(?, cra_notes),
                finalised_at = CASE WHEN ? = 'Finalised' THEN datetime('now') ELSE finalised_at END,
                updated_at = datetime('now')
            WHERE monitoring_visit_id = ?
        """, (status, cra_notes, status, monitoring_visit_id))
        if status == 'Finalised':
            cur.execute("""
                UPDATE monitoring_visits SET status = 'Completed', updated_at = datetime('now')
                WHERE monitoring_visit_id = ?
            """, (monitoring_visit_id,))
        conn.commit()
    return {"success": True, "report_status": status}


# ═══════════════════════════════════════════════════════════════════════════════
# STATIC FILE SERVING (keep at the very bottom — catch-all must be last)
# ═══════════════════════════════════════════════════════════════════════════════

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
