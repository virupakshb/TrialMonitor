"""
Create SQLite database from synthetic clinical trial data
"""

import json
import sqlite3
from datetime import datetime
import os

print("=" * 70)
print("Clinical Trial Data Layer - SQLite Database Creator")
print("Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)")
print("Sponsor: NexaVance Therapeutics Inc.")
print("=" * 70)

# Remove existing database if it exists
if os.path.exists('clinical_trial.db'):
    os.remove('clinical_trial.db')
    print("\n✓ Removed existing database")

# Create SQLite database
conn = sqlite3.connect('clinical_trial.db')
cur = conn.cursor()

print("\n1. Creating database schema...")

# Create tables (SQLite version of PostgreSQL schema)
schema_sql = """
-- Protocol Information
CREATE TABLE protocol_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol_number TEXT NOT NULL UNIQUE,
    protocol_name TEXT NOT NULL,
    short_title TEXT,
    sponsor_name TEXT NOT NULL,
    sponsor_address TEXT,
    phase TEXT,
    indication TEXT,
    study_type TEXT,
    study_design TEXT,
    therapeutic_area TEXT,
    investigational_product TEXT,
    primary_objective TEXT,
    primary_endpoint TEXT,
    planned_sample_size INTEGER,
    study_start_date TEXT,
    estimated_completion_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Sites
CREATE TABLE sites (
    site_id TEXT PRIMARY KEY,
    site_name TEXT NOT NULL,
    country TEXT NOT NULL,
    city TEXT,
    state_province TEXT,
    principal_investigator TEXT NOT NULL,
    site_coordinator TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    activation_date TEXT,
    site_status TEXT DEFAULT 'Active',
    planned_enrollment INTEGER,
    actual_enrollment INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Subjects
CREATE TABLE subjects (
    subject_id TEXT PRIMARY KEY,
    site_id TEXT,
    screening_number TEXT UNIQUE,
    randomization_number TEXT UNIQUE,
    initials TEXT,
    treatment_arm INTEGER CHECK (treatment_arm IN (1, 2)),
    treatment_arm_name TEXT,
    randomization_date TEXT,
    screening_date TEXT,
    consent_date TEXT,
    study_status TEXT DEFAULT 'Enrolled',
    discontinuation_date TEXT,
    discontinuation_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

-- Demographics
CREATE TABLE demographics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT UNIQUE,
    date_of_birth TEXT,
    age INTEGER,
    sex TEXT CHECK (sex IN ('Male', 'Female', 'Other')),
    race TEXT,
    ethnicity TEXT,
    weight_kg REAL,
    height_cm REAL,
    bmi REAL,
    ecog_performance_status INTEGER CHECK (ecog_performance_status IN (0, 1, 2)),
    smoking_status TEXT,
    smoking_pack_years REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Visits
CREATE TABLE visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    visit_number INTEGER NOT NULL,
    visit_name TEXT NOT NULL,
    scheduled_date TEXT NOT NULL,
    actual_date TEXT,
    visit_status TEXT DEFAULT 'Scheduled',
    window_lower_days INTEGER,
    window_upper_days INTEGER,
    days_from_randomization INTEGER,
    visit_type TEXT,
    visit_completed INTEGER DEFAULT 0,
    missed_visit INTEGER DEFAULT 0,
    visit_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    UNIQUE(subject_id, visit_number)
);

-- Vital Signs
CREATE TABLE vital_signs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER,
    subject_id TEXT,
    assessment_date TEXT NOT NULL,
    assessment_time TEXT,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature_celsius REAL,
    respiratory_rate INTEGER,
    weight_kg REAL,
    oxygen_saturation INTEGER,
    position TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Laboratory Results
CREATE TABLE laboratory_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER,
    subject_id TEXT,
    collection_date TEXT NOT NULL,
    collection_time TEXT,
    lab_category TEXT NOT NULL,
    test_name TEXT NOT NULL,
    test_value REAL,
    test_unit TEXT,
    normal_range_lower REAL,
    normal_range_upper REAL,
    abnormal_flag TEXT,
    clinically_significant INTEGER DEFAULT 0,
    lab_comments TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Adverse Events
CREATE TABLE adverse_events (
    ae_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    ae_term TEXT NOT NULL,
    meddra_code TEXT,
    meddra_preferred_term TEXT,
    onset_date TEXT NOT NULL,
    resolution_date TEXT,
    ongoing INTEGER DEFAULT 1,
    severity TEXT CHECK (severity IN ('Mild', 'Moderate', 'Severe', 'Life-threatening', 'Death')),
    ctcae_grade INTEGER CHECK (ctcae_grade IN (1, 2, 3, 4, 5)),
    seriousness TEXT CHECK (seriousness IN ('Yes', 'No')),
    serious_criteria TEXT,
    relationship_to_study_drug TEXT,
    action_taken TEXT,
    outcome TEXT,
    ae_description TEXT,
    reporter TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Medical History
CREATE TABLE medical_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    condition TEXT NOT NULL,
    meddra_code TEXT,
    diagnosis_date TEXT,
    ongoing INTEGER DEFAULT 0,
    resolution_date TEXT,
    condition_category TEXT,
    condition_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Concomitant Medications
CREATE TABLE concomitant_medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    medication_name TEXT NOT NULL,
    who_drug_code TEXT,
    indication TEXT,
    dose TEXT,
    dose_unit TEXT,
    frequency TEXT,
    route TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    ongoing INTEGER DEFAULT 1,
    medication_class TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Tumor Assessments
CREATE TABLE tumor_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER,
    subject_id TEXT,
    assessment_date TEXT NOT NULL,
    assessment_method TEXT,
    overall_response TEXT,
    target_lesion_sum REAL,
    new_lesions INTEGER DEFAULT 0,
    progression INTEGER DEFAULT 0,
    assessment_notes TEXT,
    radiologist TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- ECG Results
CREATE TABLE ecg_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER,
    subject_id TEXT,
    ecg_date TEXT NOT NULL,
    ecg_time TEXT,
    heart_rate INTEGER,
    pr_interval INTEGER,
    qrs_duration INTEGER,
    qt_interval INTEGER,
    qtc_interval INTEGER,
    qtcf_interval INTEGER,
    interpretation TEXT,
    abnormal INTEGER DEFAULT 0,
    clinically_significant INTEGER DEFAULT 0,
    reader TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Protocol Deviations
CREATE TABLE protocol_deviations (
    deviation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    deviation_type TEXT NOT NULL,
    deviation_category TEXT,
    description TEXT NOT NULL,
    deviation_date TEXT NOT NULL,
    reported_date TEXT,
    severity TEXT CHECK (severity IN ('Minor', 'Major', 'Critical')),
    impact_on_data INTEGER DEFAULT 0,
    impact_on_safety INTEGER DEFAULT 0,
    corrective_action TEXT,
    preventive_action TEXT,
    status TEXT DEFAULT 'Open',
    resolution_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Queries
CREATE TABLE queries (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    visit_id INTEGER,
    query_type TEXT NOT NULL,
    query_category TEXT,
    query_text TEXT NOT NULL,
    query_date TEXT NOT NULL,
    query_status TEXT DEFAULT 'Open',
    assigned_to TEXT,
    priority TEXT CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    response_text TEXT,
    response_date TEXT,
    resolution_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- ── CTMS: Monitoring Visits ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS monitoring_visits (
    monitoring_visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    visit_type TEXT NOT NULL,
    visit_label TEXT NOT NULL,
    planned_date TEXT NOT NULL,
    actual_date TEXT,
    cra_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Planned',
    visit_objectives TEXT,
    prep_generated INTEGER DEFAULT 0,
    prep_approved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monitoring_visit_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitoring_visit_id INTEGER NOT NULL,
    subject_id TEXT NOT NULL,
    sdv_status TEXT NOT NULL DEFAULT 'Not Started',
    sdv_percent INTEGER NOT NULL DEFAULT 0,
    priority TEXT NOT NULL DEFAULT 'Low',
    priority_reason TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS visit_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitoring_visit_id INTEGER NOT NULL,
    subject_id TEXT,
    finding_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    assigned_to TEXT,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'Open',
    resolved_date TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS visit_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitoring_visit_id INTEGER NOT NULL,
    report_status TEXT NOT NULL DEFAULT 'Draft',
    draft_content TEXT,
    cra_notes TEXT,
    finalised_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

cur.executescript(schema_sql)
print("✓ Schema created")

# Create indexes
print("\n2. Creating indexes...")
indexes_sql = """
CREATE INDEX idx_subjects_site ON subjects(site_id);
CREATE INDEX idx_subjects_status ON subjects(study_status);
CREATE INDEX idx_subjects_treatment_arm ON subjects(treatment_arm);

CREATE INDEX idx_visits_subject ON visits(subject_id);
CREATE INDEX idx_visits_date ON visits(actual_date);
CREATE INDEX idx_visits_status ON visits(visit_status);

CREATE INDEX idx_vitals_subject ON vital_signs(subject_id);

CREATE INDEX idx_labs_subject ON laboratory_results(subject_id);
CREATE INDEX idx_labs_category ON laboratory_results(lab_category);
CREATE INDEX idx_labs_abnormal ON laboratory_results(abnormal_flag);

CREATE INDEX idx_ae_subject ON adverse_events(subject_id);
CREATE INDEX idx_ae_severity ON adverse_events(severity);
CREATE INDEX idx_ae_seriousness ON adverse_events(seriousness);

CREATE INDEX idx_queries_subject ON queries(subject_id);
CREATE INDEX idx_queries_status ON queries(query_status);

CREATE INDEX idx_deviations_subject ON protocol_deviations(subject_id);
CREATE INDEX idx_deviations_status ON protocol_deviations(status);
"""

cur.executescript(indexes_sql)
print("✓ Indexes created")

# Load JSON data
print("\n3. Loading data from JSON files...")

with open('synthetic_data_part1.json', 'r') as f:
    part1_data = json.load(f)

with open('synthetic_data_part2.json', 'r') as f:
    part2_data = json.load(f)

with open('synthetic_data_part3.json', 'r') as f:
    part3_data = json.load(f)

print("✓ JSON files loaded")

# Insert data
def insert_data(table_name, data, columns):
    if not data:
        return 0
    
    placeholders = ', '.join(['?' for _ in columns])
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    values = []
    for record in data:
        row = [record.get(col) for col in columns]
        values.append(tuple(row))
    
    cur.executemany(sql, values)
    return len(values)

print("\n4. Inserting data...")

# Protocol info
count = insert_data('protocol_info', part1_data['protocol_info'], [
    'protocol_number', 'protocol_name', 'short_title', 'sponsor_name',
    'sponsor_address', 'phase', 'indication', 'study_type', 'study_design',
    'therapeutic_area', 'investigational_product', 'primary_objective',
    'primary_endpoint', 'planned_sample_size', 'study_start_date',
    'estimated_completion_date'
])
print(f"   ✓ Protocol info: {count} records")

# Sites
count = insert_data('sites', part1_data['sites'], [
    'site_id', 'site_name', 'country', 'city', 'state_province',
    'principal_investigator', 'site_coordinator', 'contact_email',
    'contact_phone', 'activation_date', 'site_status',
    'planned_enrollment', 'actual_enrollment'
])
print(f"   ✓ Sites: {count} records")

# Subjects
count = insert_data('subjects', part1_data['subjects'], [
    'subject_id', 'site_id', 'screening_number', 'randomization_number',
    'initials', 'treatment_arm', 'treatment_arm_name', 'randomization_date',
    'screening_date', 'consent_date', 'study_status', 'discontinuation_date',
    'discontinuation_reason'
])
print(f"   ✓ Subjects: {count} records")

# Demographics
count = insert_data('demographics', part1_data['demographics'], [
    'subject_id', 'date_of_birth', 'age', 'sex', 'race', 'ethnicity',
    'weight_kg', 'height_cm', 'bmi', 'ecog_performance_status',
    'smoking_status', 'smoking_pack_years'
])
print(f"   ✓ Demographics: {count} records")

# Visits
count = insert_data('visits', part2_data['visits'], [
    'subject_id', 'visit_number', 'visit_name', 'scheduled_date',
    'actual_date', 'visit_status', 'window_lower_days', 'window_upper_days',
    'days_from_randomization', 'visit_type', 'visit_completed',
    'missed_visit', 'visit_notes'
])
print(f"   ✓ Visits: {count} records")

# Vital signs
count = insert_data('vital_signs', part2_data['vital_signs'], [
    'subject_id', 'assessment_date', 'assessment_time', 'systolic_bp',
    'diastolic_bp', 'heart_rate', 'temperature_celsius', 'respiratory_rate',
    'weight_kg', 'oxygen_saturation', 'position', 'notes'
])
print(f"   ✓ Vital signs: {count} records")

# Laboratory results
count = insert_data('laboratory_results', part2_data['laboratory_results'], [
    'subject_id', 'collection_date', 'collection_time', 'lab_category',
    'test_name', 'test_value', 'test_unit', 'normal_range_lower',
    'normal_range_upper', 'abnormal_flag', 'clinically_significant',
    'lab_comments'
])
print(f"   ✓ Laboratory results: {count} records")

# Adverse events
count = insert_data('adverse_events', part3_data['adverse_events'], [
    'subject_id', 'ae_term', 'meddra_code', 'meddra_preferred_term',
    'onset_date', 'resolution_date', 'ongoing', 'severity', 'ctcae_grade',
    'seriousness', 'serious_criteria', 'relationship_to_study_drug',
    'action_taken', 'outcome', 'ae_description', 'reporter'
])
print(f"   ✓ Adverse events: {count} records")

# Medical history
count = insert_data('medical_history', part3_data['medical_history'], [
    'subject_id', 'condition', 'meddra_code', 'diagnosis_date',
    'ongoing', 'resolution_date', 'condition_category', 'condition_notes'
])
print(f"   ✓ Medical history: {count} records")

# Concomitant medications
count = insert_data('concomitant_medications', part3_data['concomitant_medications'], [
    'subject_id', 'medication_name', 'who_drug_code', 'indication',
    'dose', 'dose_unit', 'frequency', 'route', 'start_date',
    'end_date', 'ongoing', 'medication_class'
])
print(f"   ✓ Concomitant medications: {count} records")

# Tumor assessments
count = insert_data('tumor_assessments', part3_data['tumor_assessments'], [
    'subject_id', 'assessment_date', 'assessment_method',
    'overall_response', 'target_lesion_sum', 'new_lesions',
    'progression', 'assessment_notes', 'radiologist'
])
print(f"   ✓ Tumor assessments: {count} records")

# ECG results
count = insert_data('ecg_results', part3_data['ecg_results'], [
    'subject_id', 'ecg_date', 'ecg_time', 'heart_rate', 'pr_interval',
    'qrs_duration', 'qt_interval', 'qtc_interval', 'qtcf_interval',
    'interpretation', 'abnormal', 'clinically_significant', 'reader'
])
print(f"   ✓ ECG results: {count} records")

# Protocol deviations
count = insert_data('protocol_deviations', part3_data['protocol_deviations'], [
    'subject_id', 'deviation_type', 'deviation_category', 'description',
    'deviation_date', 'reported_date', 'severity', 'impact_on_data',
    'impact_on_safety', 'corrective_action', 'preventive_action',
    'status', 'resolution_date'
])
print(f"   ✓ Protocol deviations: {count} records")

# Queries
count = insert_data('queries', part3_data['queries'], [
    'subject_id', 'query_type', 'query_category', 'query_text',
    'query_date', 'query_status', 'assigned_to', 'priority',
    'response_text', 'response_date', 'resolution_date'
])
print(f"   ✓ Queries: {count} records")

# ---------------------------------------------------------------------------
# Seed subject 101-901 (Margaret Chen) — demo/test subject used in evaluations
# ---------------------------------------------------------------------------
cur.execute("""
    INSERT OR IGNORE INTO subjects (
        subject_id, site_id, screening_number, randomization_number,
        initials, treatment_arm, treatment_arm_name, randomization_date,
        screening_date, consent_date, study_status,
        discontinuation_date, discontinuation_reason
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (
    '101-901', '101', 'SCR-901', 'RAND-901',
    'MC', 1, 'NovaPlex-450 + Chemotherapy', '2024-08-15',
    '2024-07-22', '2024-07-18', 'Discontinued',
    '2024-11-13', 'Adverse Event - Immune myocarditis with cardiac arrest'
))

cur.execute("""
    INSERT OR IGNORE INTO demographics (
        subject_id, date_of_birth, age, sex, race, ethnicity,
        weight_kg, height_cm, bmi, ecog_performance_status,
        smoking_status, smoking_pack_years
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
""", (
    '101-901', '1963-03-14', 61, 'Female', 'Asian',
    'Not Hispanic or Latino', 58.5, 162.0, 22.3, 1,
    'Former', 18.0
))
print("   ✓ Demo subject 101-901 (Margaret Chen) seeded")

# Visits (DB is always freshly created above, so plain INSERT is safe)
cur.executemany("""
    INSERT INTO visits (subject_id, visit_number, visit_name, scheduled_date, actual_date,
        visit_status, visit_type, visit_completed, missed_visit, days_from_randomization,
        window_lower_days, window_upper_days)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
""", [
    ('101-901', 1, 'Screening',     '2024-07-22', '2024-07-22', 'Completed', 'Screening', 1, 0, -24, -7, 7),
    ('101-901', 2, 'Baseline/C1D1', '2024-08-15', '2024-08-15', 'Completed', 'Treatment', 1, 0,   0, -3, 3),
    ('101-901', 3, 'Week 3/C1D15',  '2024-09-05', '2024-09-05', 'Completed', 'Treatment', 1, 0,  21, -3, 3),
    ('101-901', 4, 'Week 6/C2D1',   '2024-10-03', '2024-10-03', 'Completed', 'Treatment', 1, 0,  49, -3, 3),
])
print("   ✓ 101-901 visits seeded")

# Vital signs (visit_id=NULL; date-based join in API links these to visits)
cur.executemany("""
    INSERT INTO vital_signs (subject_id, assessment_date, assessment_time,
        systolic_bp, diastolic_bp, heart_rate, temperature_celsius,
        respiratory_rate, weight_kg, oxygen_saturation, position)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", [
    ('101-901', '2024-07-22', '09:00', 138, 88,  82, 36.6, 16, 58.5, 97, 'Sitting'),
    ('101-901', '2024-08-15', '08:45', 142, 90,  88, 36.7, 17, 58.2, 96, 'Sitting'),
    ('101-901', '2024-09-05', '09:10', 148, 94,  96, 37.1, 18, 57.5, 95, 'Sitting'),
    ('101-901', '2024-10-03', '08:30', 156, 98, 108, 37.4, 20, 56.8, 93, 'Sitting'),
])
print("   ✓ 101-901 vital signs seeded")

# Lab results (visit_id=NULL, collection_date = visit actual_date for date-based join)
_labs_901 = [
    # Screening 2024-07-22 — Hematology
    ('101-901', '2024-07-22', 'Hematology', 'WBC',        7.8,  '10^9/L', 4.0,  11.0, None,  0),
    ('101-901', '2024-07-22', 'Hematology', 'Hemoglobin', 11.9, 'g/dL',   12.0, 16.0, 'L',   0),
    ('101-901', '2024-07-22', 'Hematology', 'Platelets',  224,  '10^9/L', 150,  400,  None,  0),
    # Screening — Chemistry
    ('101-901', '2024-07-22', 'Chemistry',  'Creatinine', 0.82, 'mg/dL',  0.5,  1.1,  None,  0),
    ('101-901', '2024-07-22', 'Chemistry',  'ALT',        28,   'U/L',    7,    56,   None,  0),
    ('101-901', '2024-07-22', 'Chemistry',  'AST',        24,   'U/L',    10,   40,   None,  0),
    # Baseline 2024-08-15 — Hematology
    ('101-901', '2024-08-15', 'Hematology', 'WBC',        7.2,  '10^9/L', 4.0,  11.0, None,  0),
    ('101-901', '2024-08-15', 'Hematology', 'Hemoglobin', 11.6, 'g/dL',   12.0, 16.0, 'L',   0),
    ('101-901', '2024-08-15', 'Hematology', 'Platelets',  210,  '10^9/L', 150,  400,  None,  0),
    # Baseline — Chemistry
    ('101-901', '2024-08-15', 'Chemistry',  'Creatinine', 0.85, 'mg/dL',  0.5,  1.1,  None,  0),
    ('101-901', '2024-08-15', 'Chemistry',  'ALT',        31,   'U/L',    7,    56,   None,  0),
    ('101-901', '2024-08-15', 'Chemistry',  'AST',        27,   'U/L',    10,   40,   None,  0),
    # Week 3 2024-09-05 — Hematology
    ('101-901', '2024-09-05', 'Hematology', 'WBC',        9.4,  '10^9/L', 4.0,  11.0, None,  0),
    ('101-901', '2024-09-05', 'Hematology', 'Hemoglobin', 10.8, 'g/dL',   12.0, 16.0, 'L',   1),
    ('101-901', '2024-09-05', 'Hematology', 'Platelets',  198,  '10^9/L', 150,  400,  None,  0),
    # Week 3 — Chemistry
    ('101-901', '2024-09-05', 'Chemistry',  'Creatinine', 0.91, 'mg/dL',  0.5,  1.1,  None,  0),
    ('101-901', '2024-09-05', 'Chemistry',  'ALT',        52,   'U/L',    7,    56,   None,  0),
    ('101-901', '2024-09-05', 'Chemistry',  'AST',        48,   'U/L',    10,   40,   None,  0),
    # Week 3 — Cardiac markers (elevated — early myocarditis signal)
    ('101-901', '2024-09-05', 'Cardiac',    'Troponin-I', 0.08, 'ng/mL',  0.0,  0.04, 'H',   1),
    ('101-901', '2024-09-05', 'Cardiac',    'BNP',        185,  'pg/mL',  0,    100,  'H',   1),
    ('101-901', '2024-09-05', 'Chemistry',  'CRP',        18.4, 'mg/L',   0,    5.0,  'H',   1),
    # Week 6 2024-10-03 — Hematology
    ('101-901', '2024-10-03', 'Hematology', 'WBC',        11.8, '10^9/L', 4.0,  11.0, 'H',   1),
    ('101-901', '2024-10-03', 'Hematology', 'Hemoglobin', 9.9,  'g/dL',   12.0, 16.0, 'L',   1),
    ('101-901', '2024-10-03', 'Hematology', 'Platelets',  176,  '10^9/L', 150,  400,  None,  0),
    # Week 6 — Chemistry
    ('101-901', '2024-10-03', 'Chemistry',  'Creatinine', 1.02, 'mg/dL',  0.5,  1.1,  None,  0),
    ('101-901', '2024-10-03', 'Chemistry',  'ALT',        89,   'U/L',    7,    56,   'H',   1),
    ('101-901', '2024-10-03', 'Chemistry',  'AST',        76,   'U/L',    10,   40,   'H',   1),
    # Week 6 — Cardiac markers (critically elevated)
    ('101-901', '2024-10-03', 'Cardiac',    'Troponin-I', 0.52, 'ng/mL',  0.0,  0.04, 'H',   1),
    ('101-901', '2024-10-03', 'Cardiac',    'BNP',        892,  'pg/mL',  0,    100,  'H',   1),
    ('101-901', '2024-10-03', 'Chemistry',  'CRP',        64.7, 'mg/L',   0,    5.0,  'H',   1),
]
cur.executemany("""
    INSERT INTO laboratory_results
        (subject_id, collection_date, lab_category, test_name, test_value, test_unit,
         normal_range_lower, normal_range_upper, abnormal_flag, clinically_significant)
    VALUES (?,?,?,?,?,?,?,?,?,?)
""", _labs_901)
print("   ✓ 101-901 laboratory results seeded")

# Adverse events
cur.executemany("""
    INSERT INTO adverse_events
        (subject_id, ae_term, onset_date, resolution_date, ongoing, severity,
         ctcae_grade, seriousness, serious_criteria, relationship_to_study_drug,
         action_taken, outcome, ae_description)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
""", [
    ('101-901', 'Fatigue', '2024-08-20', None, 1, 'Mild', 1,
     'No', None, 'Possibly Related', 'None', 'Not Recovered',
     'Grade 1 fatigue, consistent with chemotherapy treatment'),
    ('101-901', 'Pneumonitis', '2024-09-20', '2024-11-01', 0, 'Severe', 3,
     'Yes', 'Requires Hospitalisation', 'Probably Related', 'Drug Interrupted', 'Recovered',
     'Grade 3 immune-related pneumonitis requiring hospitalisation and steroid treatment'),
    ('101-901', 'Immune myocarditis', '2024-10-18', None, 1, 'Life-threatening', 4,
     'Yes', 'Life Threatening;Requires Hospitalisation', 'Probably Related',
     'Drug Discontinued', 'Not Recovered',
     'Grade 4 immune-mediated myocarditis with reduced ejection fraction (EF 32%). Study drug permanently discontinued.'),
    ('101-901', 'Cardiac arrest', '2024-10-25', '2024-10-25', 0, 'Life-threatening', 5,
     'Yes', 'Life Threatening;Requires Hospitalisation', 'Probably Related',
     'Drug Discontinued', 'Recovered',
     'Cardiac arrest secondary to immune myocarditis. Resuscitated successfully. ICU admission.'),
])
print("   ✓ 101-901 adverse events seeded")

# Medical history
cur.executemany("""
    INSERT INTO medical_history
        (subject_id, condition, meddra_code, diagnosis_date, ongoing,
         condition_category, condition_notes)
    VALUES (?,?,?,?,?,?,?)
""", [
    ('101-901', 'Non-Small Cell Lung Cancer', 'PT10029530', '2023-10-05', 1,
     'Primary Diagnosis', 'Stage IV lung adenocarcinoma, EGFR/ALK negative, PD-L1 TPS 65%'),
    ('101-901', 'Hypertension', 'PT73123064', '2019-03-10', 1,
     'Comorbidity', 'Well-controlled on Amlodipine'),
    ('101-901', 'Type 2 Diabetes Mellitus', 'PT10067585', '2017-06-20', 1,
     'Comorbidity', 'Managed with Metformin, HbA1c 7.1%'),
])
print("   ✓ 101-901 medical history seeded")

# Concomitant medications
cur.executemany("""
    INSERT INTO concomitant_medications
        (subject_id, medication_name, indication, dose, dose_unit,
         frequency, route, start_date, end_date, ongoing, medication_class)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", [
    ('101-901', 'Carboplatin', 'NSCLC - study chemotherapy', 'AUC 5', 'mg',
     'Q3W', 'IV', '2024-08-15', '2024-11-13', 0, 'Antineoplastic'),
    ('101-901', 'Pemetrexed', 'NSCLC - study chemotherapy', '500', 'mg/m2',
     'Q3W', 'IV', '2024-08-15', '2024-11-13', 0, 'Antineoplastic'),
    ('101-901', 'Amlodipine', 'Hypertension', '5', 'mg',
     'QD', 'Oral', '2019-03-15', None, 1, 'Antihypertensive'),
    ('101-901', 'Metformin', 'Type 2 Diabetes Mellitus', '1000', 'mg',
     'BID', 'Oral', '2017-06-25', None, 1, 'Antidiabetic'),
    ('101-901', 'Methylprednisolone', 'Immune myocarditis treatment', '1', 'mg/kg',
     'QD', 'IV', '2024-10-18', None, 1, 'Corticosteroid'),
])
print("   ✓ 101-901 concomitant medications seeded")

# ECG results (visit_id=NULL; ecg_date = visit actual_date for date-based join)
cur.executemany("""
    INSERT INTO ecg_results
        (subject_id, ecg_date, ecg_time, heart_rate, pr_interval, qrs_duration,
         qt_interval, qtcf_interval, interpretation, abnormal, clinically_significant, reader)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
""", [
    ('101-901', '2024-07-22', '09:15', 75,  148, 92, 412, 428, 'Normal Sinus Rhythm',                0, 0, 'Dr. K. Patel'),
    ('101-901', '2024-08-15', '09:00', 82,  152, 94, 418, 441, 'Normal Sinus Rhythm',                0, 0, 'Dr. K. Patel'),
    ('101-901', '2024-09-05', '09:20', 95,  156, 96, 438, 462, 'Sinus Tachycardia',                  0, 0, 'Dr. K. Patel'),
    ('101-901', '2024-10-03', '08:45', 110, 162, 98, 455, 489, 'Sinus Tachycardia; QTc Prolongation', 1, 1, 'Dr. K. Patel'),
])
print("   ✓ 101-901 ECG results seeded")

# Tumor assessments
cur.executemany("""
    INSERT INTO tumor_assessments
        (subject_id, assessment_date, assessment_method, overall_response,
         target_lesion_sum, new_lesions, progression, assessment_notes, radiologist)
    VALUES (?,?,?,?,?,?,?,?,?)
""", [
    ('101-901', '2024-07-22', 'CT Scan', 'Not Applicable (Baseline)',
     67.4, 0, 0, 'Baseline scan. Multiple mediastinal and hilar lymph nodes. Primary lesion RUL 42mm.', 'Dr. L. Wang'),
    ('101-901', '2024-10-03', 'CT Scan', 'Stable Disease',
     61.2, 0, 0, 'Stable disease per RECIST 1.1. Primary lesion reduced to 38mm. No new lesions. Study discontinued due to cardiac AE.', 'Dr. L. Wang'),
])
print("   ✓ 101-901 tumor assessments seeded")
print("   ✓ Full clinical dataset for 101-901 complete")

# Commit and close
conn.commit()

# ── CTMS Synthetic Data ───────────────────────────────────────────────────────
print("\n4b. Seeding CTMS monitoring visit data for Site 101...")

# 3 monitoring visits for Site 101
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (1, '101', 'IMV', 'IMV-1', '2024-10-15', '2024-10-15',
        'Sarah Mitchell',
        'Completed',
        '["Review first 10 subjects SDV","Verify ICF signatures","Review AE documentation","Check lab results against protocol thresholds"]',
        1, 1)
""")

cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (2, '101', 'IMV', 'IMV-2', '2025-01-14', '2025-01-14',
        'Sarah Mitchell',
        'Completed',
        '["Follow up on IMV-1 action items","SDV subjects 101-011 to 101-020","Review SAE for 101-901 Margaret Chen","Close 3 open queries","Review protocol deviation corrective actions"]',
        1, 1)
""")

cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (3, '101', 'IMV', 'IMV-3', '2025-03-05', NULL,
        'Sarah Mitchell',
        'Planned',
        NULL,
        0, 0)
""")

# monitoring_visit_subjects for IMV-2 (completed — has real SDV data)
imv2_subjects = [
    (2, '101-901', 'Complete',  100, 'High',   'Critical violations: Grade 4 immune myocarditis, cardiac arrest, SAE reporting overdue. Requires immediate review.'),
    (2, '101-003', 'Complete',   85, 'High',   'Two open queries older than 30 days, visit window deviation at Week 6.'),
    (2, '101-007', 'Complete',   90, 'Medium', 'Overdue Week 9 lab results, one open query on conmed documentation.'),
    (2, '101-012', 'Complete',  100, 'Medium', 'Grade 2 fatigue ongoing — monitor AE progression.'),
    (2, '101-015', 'Complete',   75, 'Low',    'SDV incomplete from prior visit. No active issues.'),
    (2, '101-018', 'In Progress', 60, 'Low',   'Routine review — no significant findings.'),
    (2, '101-021', 'Complete',  100, 'Low',    'Clean subject — all data complete and within protocol.'),
]
cur.executemany("""
    INSERT INTO monitoring_visit_subjects
        (monitoring_visit_id, subject_id, sdv_status, sdv_percent, priority, priority_reason)
    VALUES (?, ?, ?, ?, ?, ?)
""", imv2_subjects)

# monitoring_visit_subjects for IMV-3 (upcoming — no subjects yet, agent will populate on Generate Prep)
# (left empty — populated by agent on generate-prep call)

# visit_findings for IMV-2 (completed visit — mix of open and resolved)
imv2_findings = [
    (2, '101-901', 'Protocol Deviation', 'SAE (immune myocarditis Grade 4, onset 2024-10-18) not reported to sponsor within required 24-hour window. Reported 72 hours after onset.', 'Critical', 'Jessica Martinez', '2025-01-28', 'Open', None),
    (2, '101-901', 'Query',              'Cardiac arrest event (2024-10-25) — source document (ECG strip and resuscitation record) not yet uploaded to EDC. Required for SAE narrative.', 'Major',    'Jessica Martinez', '2025-01-28', 'Open', None),
    (2, '101-003', 'Query',              'Visit 4 (Week 6) conducted on 2024-10-08 — 5 days outside protocol window of C2D1 +/- 3 days. No deviation form raised.', 'Major',    'Dr. Emily Chen',   '2025-01-21', 'Resolved', '2025-01-20'),
    (2, '101-007', 'SDV Finding',        'Week 9 haematology results (ANC 0.9 x10^9/L) recorded in source but not entered into EDC. Grade 3 neutropenia threshold breached — requires AE entry.', 'Critical', 'Jessica Martinez', '2025-01-21', 'Open', None),
    (2, '101-015', 'Action Item',        'SDV for visits 3 and 4 incomplete from IMV-1. CRA to complete at IMV-3. Site coordinator to ensure CRFs are fully signed before next visit.', 'Minor',    'Jessica Martinez', '2025-03-05', 'Open', None),
]
cur.executemany("""
    INSERT INTO visit_findings
        (monitoring_visit_id, subject_id, finding_type, description, severity,
         assigned_to, due_date, status, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", imv2_findings)

# visit_findings for IMV-1 (older completed visit — all resolved)
imv1_findings = [
    (1, '101-005', 'Query',       'Concomitant medication (Metformin) start date missing in EDC. Source document confirms start date as 2024-07-01.', 'Minor', 'Jessica Martinez', '2024-10-29', 'Resolved', '2024-10-28'),
    (1, '101-009', 'SDV Finding', 'Screening weight recorded as 68 kg in source but entered as 86 kg in EDC — data entry error. Corrected and verified.', 'Major', 'Jessica Martinez', '2024-10-22', 'Resolved', '2024-10-21'),
]
cur.executemany("""
    INSERT INTO visit_findings
        (monitoring_visit_id, subject_id, finding_type, description, severity,
         assigned_to, due_date, status, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", imv1_findings)

# visit_report for IMV-2 (finalised)
imv2_report = """# Monitoring Visit Report — IMV-2
**Site:** 101 — Memorial Cancer Center, Boston, MA
**Visit Date:** 14 January 2025
**Visit Type:** Interim Monitoring Visit (IMV-2)
**CRA:** Sarah Mitchell
**Principal Investigator:** Dr. Emily Chen
**Site Coordinator:** Jessica Martinez

---

## 1. Visit Summary

An interim monitoring visit was conducted at Memorial Cancer Center on 14 January 2025.
The visit was conducted in accordance with the Monitoring Plan for Protocol NVX-1218.22.
The primary objectives were to follow up on IMV-1 action items, complete SDV for subjects
101-011 through 101-021, review the SAE for subject 101-901, and close outstanding queries.

**Attendees:** Sarah Mitchell (CRA), Dr. Emily Chen (PI), Jessica Martinez (Site Coordinator)
**Duration:** 08:30 — 17:00

---

## 2. Subjects Reviewed

| Subject | SDV Status | SDV % | Priority | Notes |
|---------|-----------|-------|----------|-------|
| 101-901 | Complete | 100% | HIGH | SAE review — critical findings (see Section 4) |
| 101-003 | Complete | 85% | HIGH | Protocol deviation resolved; query closed |
| 101-007 | Complete | 90% | MEDIUM | EDC entry error identified (see findings) |
| 101-012 | Complete | 100% | MEDIUM | AE monitoring ongoing — stable |
| 101-015 | Complete | 75% | LOW | SDV carries forward to IMV-3 |
| 101-018 | In Progress | 60% | LOW | To be completed at IMV-3 |
| 101-021 | Complete | 100% | LOW | Clean — no findings |

---

## 3. Objectives Review

- [x] Follow up on IMV-1 action items — 2 of 2 resolved
- [x] SDV subjects 101-011 to 101-020 — completed (75-100% per subject)
- [x] Review SAE for 101-901 Margaret Chen — reviewed; critical finding raised
- [x] Close 3 open queries — 1 of 3 closed; 2 remain open
- [x] Review protocol deviation corrective actions — 1 deviation form raised and resolved

---

## 4. Findings & Action Items

### CRITICAL

**Finding 1 — Subject 101-901 — Protocol Deviation (SAE Reporting Timeline)**
The SAE for immune myocarditis (Grade 4, onset 2024-10-18) was not reported to the sponsor
within the required 24-hour window per ICH E6 and Protocol Section 8.2. Report was submitted
72 hours after onset awareness. A protocol deviation form must be raised immediately.
**Assigned to:** Jessica Martinez | **Due:** 28 January 2025 | **Status:** OPEN

**Finding 2 — Subject 101-007 — SDV Finding (Missing AE Entry)**
Grade 3 neutropenia (ANC 0.9 x10^9/L) identified in source haematology results at Week 9 but
not entered into EDC as an Adverse Event. Entry required per protocol safety reporting obligations.
**Assigned to:** Jessica Martinez | **Due:** 21 January 2025 | **Status:** OPEN

### MAJOR

**Finding 3 — Subject 101-901 — Query (Missing Source Document)**
ECG strip and resuscitation record for cardiac arrest event (2024-10-25) not uploaded to EDC.
Required for complete SAE narrative. Site to upload within 14 days.
**Assigned to:** Jessica Martinez | **Due:** 28 January 2025 | **Status:** OPEN

### MINOR

**Finding 4 — Subject 101-015 — Action Item (SDV Carry-Forward)**
SDV for visits 3 and 4 incomplete from IMV-1. CRAs to prioritise at IMV-3.
**Assigned to:** Jessica Martinez | **Due:** 05 March 2025 | **Status:** OPEN

### RESOLVED AT THIS VISIT

**Finding 5 — Subject 101-003 — Query (Visit Window Deviation)**
Visit 4 conducted 5 days outside protocol window. Deviation form raised and approved by PI.
**Resolved:** 20 January 2025

---

## 5. Outstanding Issues

- 2 queries open >14 days (101-901 SAE documentation, 101-007 AE entry)
- 1 critical protocol deviation open (SAE reporting timeline for 101-901)
- SDV incomplete for subjects 101-015 (75%) and 101-018 (60%)

---

## 6. Next Steps & Follow-Up

1. Jessica Martinez to raise protocol deviation form for 101-901 SAE reporting delay — **by 28 Jan 2025**
2. Jessica Martinez to enter Grade 3 neutropenia AE for 101-007 in EDC — **by 21 Jan 2025**
3. Jessica Martinez to upload source documents for 101-901 cardiac arrest — **by 28 Jan 2025**
4. IMV-3 scheduled for **05 March 2025** — priority: complete SDV for 101-015, 101-018; verify action item closure

---

*Report prepared by: Sarah Mitchell, CRA*
*Report date: 17 January 2025*
*Next monitoring visit: IMV-3 — 05 March 2025*
"""

cur.execute("""
    INSERT INTO visit_reports
        (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (2, 'Finalised', ?, 'All findings discussed with PI and site coordinator on the day. PI acknowledged the SAE deviation and committed to corrective action within protocol timelines.', '2025-01-17')
""", (imv2_report,))

# visit_report for IMV-1 (older, finalised, brief)
imv1_report = """# Monitoring Visit Report — IMV-1
**Site:** 101 — Memorial Cancer Center, Boston, MA
**Visit Date:** 15 October 2024
**Visit Type:** Interim Monitoring Visit (IMV-1)
**CRA:** Sarah Mitchell

---

## 1. Visit Summary
First interim monitoring visit following site initiation. SDV completed for subjects 101-001
through 101-010. Two minor findings identified and resolved.

## 2. Subjects Reviewed
Subjects 101-001 to 101-010 reviewed. SDV 100% complete for 9 of 10 subjects. Subject 101-009
required data correction (weight transcription error).

## 3. Findings
All findings resolved at or shortly after the visit. No critical or major outstanding issues.

## 4. Next Steps
IMV-2 scheduled for January 2025. Site to ensure CRFs for subjects 101-011 onwards are complete
prior to next visit.

*Report finalised: 20 October 2024*
"""

cur.execute("""
    INSERT INTO visit_reports
        (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (1, 'Finalised', ?, NULL, '2024-10-20')
""", (imv1_report,))

conn.commit()
print("✓ CTMS monitoring visit data seeded (Site 101: 3 visits, 5 findings, 2 reports)")

# Get statistics
print("\n5. Database Statistics:")
tables = [
    'sites', 'subjects', 'demographics', 'visits', 'vital_signs',
    'laboratory_results', 'adverse_events', 'medical_history',
    'concomitant_medications', 'tumor_assessments', 'ecg_results',
    'protocol_deviations', 'queries',
    'monitoring_visits', 'monitoring_visit_subjects', 'visit_findings', 'visit_reports'
]

total_records = 0
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    total_records += count
    print(f"   {table:30s}: {count:6,d} records")

# Get database size
import os
db_size = os.path.getsize('clinical_trial.db') / (1024 * 1024)
print(f"\n   Database size: {db_size:.2f} MB")
print(f"   Total records: {total_records:,}")

conn.close()

print("\n" + "=" * 70)
print("✅ SQLite database created successfully!")
print("=" * 70)
print("\nDatabase file: clinical_trial.db")
print("Ready to use with the local API server!")
