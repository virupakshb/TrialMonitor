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
    secondary_endpoints TEXT,
    key_inclusion_criteria TEXT,
    key_exclusion_criteria TEXT,
    dosing_regimen TEXT,
    visit_schedule_summary TEXT,
    ae_reporting_rules TEXT,
    randomisation_ratio TEXT,
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
    'primary_endpoint', 'secondary_endpoints', 'key_inclusion_criteria',
    'key_exclusion_criteria', 'dosing_regimen', 'visit_schedule_summary',
    'ae_reporting_rules', 'randomisation_ratio',
    'planned_sample_size', 'study_start_date', 'estimated_completion_date'
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

# ─────────────────────────────────────────────────────────────────────────────
# CTMS Synthetic Data — Sites 102-105
# ─────────────────────────────────────────────────────────────────────────────

# --- Site 102: London Oncology Institute — HIGH RISK ---
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (4, '102', 'IMV', 'IMV-1', '2024-09-10', '2024-09-10',
        'David Park', 'Completed',
        '["Review first 10 subjects SDV","Verify ICF version 1.0 signatures","Review AE documentation","Confirm lab certification is current"]',
        1, 1)
""")
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (5, '102', 'IMV', 'IMV-2', '2025-02-04', '2025-02-04',
        'David Park', 'Completed',
        '["Follow up on IMV-1 action items","Verify ICF re-consent for amendment v2.1","Review haematology data entry","Confirm randomisation date source documents","SDV subjects 102-011 to 102-022"]',
        1, 1)
""")

imv5_findings = [
    (5, '102-003', 'Protocol Deviation',
     'ICF re-consent not obtained following protocol amendment v2.1 (issued 2024-11-15). Subject continued on study without updated consent.',
     'Critical', 'Dr. James Harrison', '2025-02-18', 'Open', None),
    (5, '102-007', 'Protocol Deviation',
     'ICF re-consent not obtained following protocol amendment v2.1 (issued 2024-11-15). Subject continued on study without updated consent.',
     'Critical', 'Dr. James Harrison', '2025-02-18', 'Open', None),
    (5, '102-011', 'Protocol Deviation',
     'ICF re-consent not obtained following protocol amendment v2.1 (issued 2024-11-15). Subject continued on study without updated consent.',
     'Critical', 'Dr. James Harrison', '2025-02-18', 'Open', None),
    (5, '102-014', 'Query',
     'Haematology results at Week 6 visit missing from EDC. Source confirms labs were collected 2024-12-19 but not entered.',
     'Major', 'Dr. James Harrison', '2025-02-18', 'Open', None),
    (5, '102-019', 'SDV Finding',
     'Randomisation date recorded in EDC (2024-10-22) does not match source document (2024-10-21). Requires data correction and PI countersignature.',
     'Major', 'Dr. James Harrison', '2025-02-18', 'Open', None),
]
imv4_findings = [
    (4, '102-001', 'Query',
     'Subject weight transcription error at baseline: source=72.3kg, EDC=27.3kg. Corrected and PI countersigned.',
     'Major', 'Dr. James Harrison', '2024-09-24', 'Resolved', '2024-09-20'),
]
cur.executemany("""
    INSERT INTO visit_findings
        (monitoring_visit_id, subject_id, finding_type, description, severity,
         assigned_to, due_date, status, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", imv5_findings + imv4_findings)

imv4_report = """# Monitoring Visit Report — IMV-1

**Site:** 102 — London Oncology Institute, London, United Kingdom
**Visit Date:** 2024-09-10
**Visit Type:** IMV (IMV-1)
**CRA:** David Park
**Principal Investigator:** Dr. James Harrison
**Report Generated:** 2024-09-12

---

## 1. Visit Summary
Site 102 is performing well overall. 1 minor transcription error identified and resolved at visit.
SDV of first 10 subjects completed. No safety concerns identified.

**Subjects reviewed:** 10
**Total findings:** 1 (0 Critical, 1 Major, 0 Minor)
**Open findings:** 0 | **Resolved at visit:** 1

---

## 2. Next Steps
- Continue SDV per monitoring plan
- ICF amendment v2.1 to be distributed when approved — site to re-consent all active subjects

*Report finalised: 12 September 2024*
"""
cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (4, 'Finalised', ?, 'All items discussed with PI. Site in good standing.', '2024-09-12')
""", (imv4_report,))
cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (5, 'Draft', ?, NULL, NULL)
""", ("# Monitoring Visit Report — IMV-2\n\n**DRAFT — Pending CRA Review**\n\nSite 102 has 3 critical findings related to ICF re-consent failure following protocol amendment v2.1. Immediate corrective action required. PI to initiate re-consent for subjects 102-003, 102-007, 102-011 within 5 business days.",))

conn.commit()
print("✓ Site 102 CTMS data seeded (2 visits, 6 findings)")

# --- Site 103: Toronto Research Hospital — MEDIUM RISK ---
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (6, '103', 'IMV', 'IMV-1', '2024-08-20', '2024-08-20',
        'Sarah Mitchell', 'Completed',
        '["SDV first 10 subjects","Verify ICF signatures","Review AE documentation","Check visit window compliance"]',
        1, 1)
""")
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (7, '103', 'IMV', 'IMV-2', '2024-12-03', '2024-12-03',
        'Sarah Mitchell', 'Completed',
        '["Follow up IMV-1 actions","SDV subjects 103-011 to 103-020","Close open AE grade query","Verify vital signs countersignature","Review recruitment rate"]',
        1, 1)
""")
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (8, '103', 'IMV', 'IMV-3', '2025-04-08', NULL,
        'Sarah Mitchell', 'Planned', NULL, 0, 0)
""")

imv7_findings = [
    (7, '103-005', 'Query',
     'AE term "nausea" recorded but CTCAE grade not specified in source document. Grade must be documented per protocol Section 7.3.',
     'Minor', 'Dr. Priya Sharma', '2025-01-07', 'Open', None),
    (7, '103-012', 'Action Item',
     'SDV for visits 2 and 3 outstanding. To be completed at IMV-3 per monitoring plan.',
     'Minor', 'Dr. Priya Sharma', '2025-04-08', 'Open', None),
    (7, '103-008', 'SDV Finding',
     'Vital signs at Week 9 recorded in paper source but visit was conducted by nurse practitioner without PI countersignature. PI countersignature obtained at visit.',
     'Major', 'Dr. Priya Sharma', '2024-12-17', 'Resolved', '2024-12-15'),
]
cur.executemany("""
    INSERT INTO visit_findings
        (monitoring_visit_id, subject_id, finding_type, description, severity,
         assigned_to, due_date, status, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", imv7_findings)

cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (6, 'Finalised', ?, 'Clean visit. Site performing well.', '2024-08-22')
""", ("# Monitoring Visit Report — IMV-1\n\n**Site:** 103 — Toronto Research Hospital, Toronto, Canada\n**Visit Date:** 2024-08-20\n**CRA:** Sarah Mitchell\n\nClean visit. SDV of 10 subjects completed. No significant findings. Site 103 is well-organised with strong PI engagement.\n\n*Finalised: 22 August 2024*",))
cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (7, 'Finalised', ?, 'Two minor open items to follow up at IMV-3. Site performing well overall.', '2024-12-05')
""", ("# Monitoring Visit Report — IMV-2\n\n**Site:** 103 — Toronto Research Hospital, Toronto, Canada\n**Visit Date:** 2024-12-03\n**CRA:** Sarah Mitchell\n\n1 Major finding resolved at visit. 2 minor open items carried forward to IMV-3 (AE grade documentation, SDV completion).\n\n*Finalised: 05 December 2024*",))

conn.commit()
print("✓ Site 103 CTMS data seeded (3 visits, 3 findings)")

# --- Site 104: Sydney Cancer Center — LOW RISK ---
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (9, '104', 'IMV', 'IMV-1', '2024-10-22', '2024-10-22',
        'Sarah Mitchell', 'Completed',
        '["SDV first 10 subjects","Review ICF signatures","Check AE documentation","Verify concomitant medication records"]',
        1, 1)
""")
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (10, '104', 'IMV', 'IMV-2', '2025-01-28', '2025-01-28',
        'Sarah Mitchell', 'Completed',
        '["Follow up IMV-1 items","SDV subjects 104-011 to 104-018","Verify lab results transcription","Review tumour assessment records"]',
        1, 1)
""")

imv10_findings = [
    (10, '104-002', 'Query',
     'Concomitant medication start date missing for Pantoprazole. Source confirms 2024-09-10. Corrected and PI countersigned at visit.',
     'Minor', 'Dr. David O\'Connor', '2025-02-04', 'Resolved', '2025-01-28'),
    (10, '104-009', 'SDV Finding',
     'Week 5 lab results: ALT and AST values transposed in EDC transcription. Source: ALT=32 U/L, AST=28 U/L. Corrected and PI countersigned.',
     'Minor', 'Dr. David O\'Connor', '2025-02-04', 'Resolved', '2025-01-28'),
]
cur.executemany("""
    INSERT INTO visit_findings
        (monitoring_visit_id, subject_id, finding_type, description, severity,
         assigned_to, due_date, status, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", imv10_findings)

cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (9, 'Finalised', ?, 'Excellent visit. Site 104 is a model site.', '2024-10-24')
""", ("# Monitoring Visit Report — IMV-1\n\n**Site:** 104 — Sydney Cancer Center, Sydney, Australia\n**Visit Date:** 2024-10-22\n**CRA:** Sarah Mitchell\n\nExcellent first IMV. No significant findings. All SDV complete. Site 104 demonstrates excellent data quality practices.\n\n*Finalised: 24 October 2024*",))
cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (10, 'Finalised', ?, '2 minor findings both resolved at visit. Site 104 remains in excellent standing.', '2025-01-30')
""", ("# Monitoring Visit Report — IMV-2\n\n**Site:** 104 — Sydney Cancer Center, Sydney, Australia\n**Visit Date:** 2025-01-28\n**CRA:** Sarah Mitchell\n\n2 minor findings identified and resolved at visit. No open issues. All SDV complete. Site performing to highest standards.\n\n*Finalised: 30 January 2025*",))

conn.commit()
print("✓ Site 104 CTMS data seeded (2 visits, 2 findings — all resolved)")

# --- Site 105: Singapore Medical Research — HIGH RISK ---
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (11, '105', 'IMV', 'IMV-1', '2024-11-12', '2024-11-12',
        'David Park', 'Completed',
        '["SDV first 8 subjects","Verify screening ECG documentation","Review randomisation procedures","Check ECOG assessment documentation","Confirm tumour assessment upload"]',
        1, 1)
""")
cur.execute("""
    INSERT INTO monitoring_visits
        (monitoring_visit_id, site_id, visit_type, visit_label, planned_date, actual_date,
         cra_name, status, visit_objectives, prep_generated, prep_approved)
    VALUES (12, '105', 'IMV', 'IMV-2', '2025-03-18', NULL,
        'David Park', 'Planned', NULL, 0, 0)
""")

imv11_findings = [
    (11, '105-001', 'Protocol Deviation',
     'Screening ECG not performed within the required 7-day window prior to randomisation. ECG performed 11 days before randomisation (protocol window: 7 days per Section 5.2.1).',
     'Major', 'Dr. Wei Zhang', '2025-01-12', 'Open', None),
    (11, '105-004', 'Query',
     'Baseline tumour assessment CT scan report not uploaded to EDC. Radiologist confirms scan completed 2024-09-30 but report is absent from site file.',
     'Major', 'Dr. Wei Zhang', '2025-01-12', 'Open', None),
    (11, '105-007', 'Query',
     'ECOG performance status recorded as 0 at screening in EDC but treating physician notes indicate ECOG 1. Source verification required.',
     'Minor', 'Dr. Wei Zhang', '2025-01-12', 'Open', None),
]
cur.executemany("""
    INSERT INTO visit_findings
        (monitoring_visit_id, subject_id, finding_type, description, severity,
         assigned_to, due_date, status, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", imv11_findings)

cur.execute("""
    INSERT INTO visit_reports (monitoring_visit_id, report_status, draft_content, cra_notes, finalised_at)
    VALUES (11, 'CRA Reviewed', ?, 'Reviewed by David Park. 3 open findings require urgent site follow-up before IMV-2.', NULL)
""", ("# Monitoring Visit Report — IMV-1\n\n**Site:** 105 — Singapore Medical Research, Singapore\n**Visit Date:** 2024-11-12\n**CRA:** David Park\n\nFirst IMV identified 3 open findings (2 Major, 1 Minor). Site requires corrective action on ECG window deviation and missing CT scan documentation. ECOG discrepancy to be clarified.\n\n*CRA Reviewed — pending finalisation*",))

conn.commit()
print("✓ Site 105 CTMS data seeded (2 visits, 3 findings)")

# ─────────────────────────────────────────────────────────────────────────────
# TMF Tables + Seed Data
# ─────────────────────────────────────────────────────────────────────────────

cur.executescript("""
CREATE TABLE IF NOT EXISTS tmf_requirements (
    requirement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL,
    category TEXT NOT NULL,
    is_mandatory INTEGER DEFAULT 1,
    validity_months INTEGER
);

CREATE TABLE IF NOT EXISTS tmf_documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    version TEXT,
    file_path TEXT,
    document_date TEXT,
    expiry_date TEXT,
    status TEXT NOT NULL DEFAULT 'Present',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
""")

# TMF Requirements — study-level mandatory document types
tmf_reqs = [
    ('Delegation Log',                  'Staff',      1, None),
    ('IRB Ethics Approval',             'Regulatory', 1, 12),
    ('IRB Approval Amendment',          'Regulatory', 1, None),
    ('ICF Current Version',             'Consent',    1, None),
    ('Investigator CV',                 'Staff',      1, 24),
    ('GCP Certificate PI',              'Staff',      1, 24),
    ('GCP Certificate Coordinator',     'Staff',      1, 24),
    ('Lab Certification',               'Lab',        1, 12),
    ('Lab Normal Ranges',               'Lab',        1, 12),
    ('Drug Accountability Log',         'IP',         1, None),
    ('SAE Narrative',                   'Safety',     1, None),
    ('Previous Visit Follow-up Letter', 'Regulatory', 0, None),
]
cur.executemany("""
    INSERT INTO tmf_requirements (document_type, category, is_mandatory, validity_months)
    VALUES (?, ?, ?, ?)
""", tmf_reqs)

# TMF Documents per site
# Status: 'Present' | 'Missing' | 'Expiring' | 'Superseded'

# Site 101 — 10/12 present, 1 Expiring, 1 Missing → score ~83%
tmf_101 = [
    ('101','Delegation Log',                  'Staff',      'Site Delegation Log v1.0',         'v1.0', 'tmf_documents/site_101/delegation_log_v1.pdf',   '2024-01-15', None,         'Present',  None),
    ('101','IRB Ethics Approval',             'Regulatory', 'IRB Initial Approval — NVX-1218.22','v1.0', 'tmf_documents/site_101/irb_approval_2024.pdf',   '2024-01-10', '2025-01-10', 'Present',  None),
    ('101','IRB Approval Amendment',          'Regulatory', 'IRB Amendment Approval v2.1',       'v2.1', 'tmf_documents/site_101/irb_amendment_v2_1.pdf',  '2024-11-20', None,         'Present',  None),
    ('101','ICF Current Version',             'Consent',    'Informed Consent Form v2.1',        'v2.1', 'tmf_documents/site_101/icf_v2_1.pdf',            '2024-11-15', None,         'Present',  None),
    ('101','Investigator CV',                 'Staff',      'CV — Dr. Emily Chen',               'v3.0', 'tmf_documents/site_101/pi_cv.pdf',               '2024-03-01', '2026-03-01', 'Present',  None),
    ('101','GCP Certificate PI',              'Staff',      'GCP Certificate — Dr. Emily Chen',  '2024', 'tmf_documents/site_101/gcp_cert_pi.pdf',         '2024-02-10', '2026-02-10', 'Present',  None),
    ('101','GCP Certificate Coordinator',     'Staff',      'GCP Certificate — Jessica Martinez','2024', 'tmf_documents/site_101/gcp_cert_coord.pdf',      '2023-04-01', '2025-04-15', 'Expiring', 'Expires 2025-04-15 — renewal in progress'),
    ('101','Lab Certification',               'Lab',        'Central Lab Accreditation',         '2024', 'tmf_documents/site_101/lab_certification.pdf',   '2024-06-01', '2025-06-01', 'Present',  None),
    ('101','Lab Normal Ranges',               'Lab',        'Lab Normal Ranges — NVX-1218.22',   'v2.0', 'tmf_documents/site_101/lab_normal_ranges.pdf',  '2024-06-01', '2025-06-01', 'Present',  None),
    ('101','Drug Accountability Log',         'IP',         'Drug Accountability Log — Site 101','v1.0', 'tmf_documents/site_101/drug_accountability.pdf', '2024-01-15', None,         'Present',  None),
    ('101','SAE Narrative',                   'Safety',     'SAE Narrative — Subject 101-901',   'v1.0', 'tmf_documents/site_101/sae_narrative_901.pdf',   '2024-09-15', None,         'Present',  None),
    ('101','Previous Visit Follow-up Letter', 'Regulatory', 'Follow-up Letter — IMV-2',          None,   None,                                              None,         None,         'Missing',  'Follow-up letter for IMV-2 not yet filed in TMF'),
]

# Site 102 — 9/12 present, 2 Missing, 1 Superseded → score ~75%
tmf_102 = [
    ('102','Delegation Log',                  'Staff',      'Site Delegation Log v1.0',         'v1.0', 'tmf_documents/site_102/delegation_log_v1.pdf',   '2024-02-01', None,         'Present',  None),
    ('102','IRB Ethics Approval',             'Regulatory', 'IRB Initial Approval — NVX-1218.22','v1.0', 'tmf_documents/site_102/irb_approval_2024.pdf',  '2024-02-05', '2025-02-05', 'Present',  None),
    ('102','IRB Approval Amendment',          'Regulatory', 'IRB Amendment Approval v2.1',       None,   None,                                             None,         None,         'Missing',  'Amendment v2.1 IRB approval not uploaded — ICF re-consent cannot proceed without this'),
    ('102','ICF Current Version',             'Consent',    'Informed Consent Form v1.0',        'v1.0', 'tmf_documents/site_102/icf_v1_0.pdf',           '2024-02-01', None,         'Superseded','ICF v2.1 not yet filed — subjects consented on superseded v1.0'),
    ('102','Investigator CV',                 'Staff',      'CV — Dr. James Harrison',           'v2.0', 'tmf_documents/site_102/pi_cv.pdf',              '2023-09-01', '2025-09-01', 'Present',  None),
    ('102','GCP Certificate PI',              'Staff',      'GCP Certificate — Dr. James Harrison','2023','tmf_documents/site_102/gcp_cert_pi.pdf',       '2023-07-15', '2025-07-15', 'Present',  None),
    ('102','GCP Certificate Coordinator',     'Staff',      'GCP Certificate — Sophie Williams', '2024', 'tmf_documents/site_102/gcp_cert_coord.pdf',     '2024-01-20', '2026-01-20', 'Present',  None),
    ('102','Lab Certification',               'Lab',        'Central Lab Accreditation',         '2024', 'tmf_documents/site_102/lab_certification.pdf',  '2024-06-01', '2025-06-01', 'Present',  None),
    ('102','Lab Normal Ranges',               'Lab',        'Lab Normal Ranges — NVX-1218.22',   'v2.0', 'tmf_documents/site_102/lab_normal_ranges.pdf', '2024-06-01', '2025-06-01', 'Present',  None),
    ('102','Drug Accountability Log',         'IP',         'Drug Accountability Log — Site 102','v1.0', 'tmf_documents/site_102/drug_accountability.pdf','2024-02-01', None,         'Present',  None),
    ('102','SAE Narrative',                   'Safety',     'SAE Narrative — Not Required',      None,   None,                                             None,         None,         'Missing',  'No SAEs reported at this site — not applicable'),
    ('102','Previous Visit Follow-up Letter', 'Regulatory', 'Follow-up Letter — IMV-1',          None,   'tmf_documents/site_102/followup_imv1.pdf',       '2024-09-14', None,         'Present',  None),
]

# Site 103 — 11/12 present, 1 Expiring → score ~92%
tmf_103 = [
    ('103','Delegation Log',                  'Staff',      'Site Delegation Log v1.0',         'v1.0', 'tmf_documents/site_103/delegation_log_v1.pdf',   '2024-01-20', None,         'Present',  None),
    ('103','IRB Ethics Approval',             'Regulatory', 'IRB Initial Approval — NVX-1218.22','v1.0', 'tmf_documents/site_103/irb_approval_2024.pdf',  '2024-01-18', '2025-01-18', 'Present',  None),
    ('103','IRB Approval Amendment',          'Regulatory', 'IRB Amendment Approval v2.1',       'v2.1', 'tmf_documents/site_103/irb_amendment_v2_1.pdf', '2024-12-01', None,         'Present',  None),
    ('103','ICF Current Version',             'Consent',    'Informed Consent Form v2.1',        'v2.1', 'tmf_documents/site_103/icf_v2_1.pdf',           '2024-12-01', None,         'Present',  None),
    ('103','Investigator CV',                 'Staff',      'CV — Dr. Priya Sharma',             'v2.0', 'tmf_documents/site_103/pi_cv.pdf',              '2023-06-01', '2025-06-01', 'Expiring', 'CV expires 2025-06-01 — request updated CV at IMV-3'),
    ('103','GCP Certificate PI',              'Staff',      'GCP Certificate — Dr. Priya Sharma','2024', 'tmf_documents/site_103/gcp_cert_pi.pdf',        '2024-04-10', '2026-04-10', 'Present',  None),
    ('103','GCP Certificate Coordinator',     'Staff',      'GCP Certificate — Michael Wong',    '2023', 'tmf_documents/site_103/gcp_cert_coord.pdf',     '2023-11-01', '2025-11-01', 'Present',  None),
    ('103','Lab Certification',               'Lab',        'Central Lab Accreditation',         '2024', 'tmf_documents/site_103/lab_certification.pdf',  '2024-06-01', '2025-06-01', 'Present',  None),
    ('103','Lab Normal Ranges',               'Lab',        'Lab Normal Ranges — NVX-1218.22',   'v2.0', 'tmf_documents/site_103/lab_normal_ranges.pdf', '2024-06-01', '2025-06-01', 'Present',  None),
    ('103','Drug Accountability Log',         'IP',         'Drug Accountability Log — Site 103','v1.0', 'tmf_documents/site_103/drug_accountability.pdf','2024-01-20', None,         'Present',  None),
    ('103','SAE Narrative',                   'Safety',     'SAE Narrative — Not Required',      None,   None,                                             None,         None,         'Missing',  'No SAEs at this site'),
    ('103','Previous Visit Follow-up Letter', 'Regulatory', 'Follow-up Letter — IMV-2',          None,   'tmf_documents/site_103/followup_imv2.pdf',       '2024-12-06', None,         'Present',  None),
]

# Site 104 — 12/12 present, all current → score 100%
tmf_104 = [
    ('104','Delegation Log',                  'Staff',      'Site Delegation Log v1.0',         'v1.0', 'tmf_documents/site_104/delegation_log_v1.pdf',   '2024-03-01', None,         'Present',  None),
    ('104','IRB Ethics Approval',             'Regulatory', 'IRB Initial Approval — NVX-1218.22','v1.0', 'tmf_documents/site_104/irb_approval_2024.pdf',  '2024-03-05', '2025-03-05', 'Present',  None),
    ('104','IRB Approval Amendment',          'Regulatory', 'IRB Amendment Approval v2.1',       'v2.1', 'tmf_documents/site_104/irb_amendment_v2_1.pdf', '2024-12-10', None,         'Present',  None),
    ('104','ICF Current Version',             'Consent',    'Informed Consent Form v2.1',        'v2.1', 'tmf_documents/site_104/icf_v2_1.pdf',           '2024-12-10', None,         'Present',  None),
    ('104','Investigator CV',                 'Staff',      "CV — Dr. David O'Connor",           'v3.0', 'tmf_documents/site_104/pi_cv.pdf',              '2024-05-01', '2026-05-01', 'Present',  None),
    ('104','GCP Certificate PI',              'Staff',      "GCP Certificate — Dr. David O'Connor",'2024','tmf_documents/site_104/gcp_cert_pi.pdf',       '2024-05-15', '2026-05-15', 'Present',  None),
    ('104','GCP Certificate Coordinator',     'Staff',      'GCP Certificate — Emma Thompson',   '2024', 'tmf_documents/site_104/gcp_cert_coord.pdf',     '2024-03-20', '2026-03-20', 'Present',  None),
    ('104','Lab Certification',               'Lab',        'Central Lab Accreditation',         '2024', 'tmf_documents/site_104/lab_certification.pdf',  '2024-06-01', '2025-06-01', 'Present',  None),
    ('104','Lab Normal Ranges',               'Lab',        'Lab Normal Ranges — NVX-1218.22',   'v2.0', 'tmf_documents/site_104/lab_normal_ranges.pdf', '2024-06-01', '2025-06-01', 'Present',  None),
    ('104','Drug Accountability Log',         'IP',         'Drug Accountability Log — Site 104','v1.0', 'tmf_documents/site_104/drug_accountability.pdf','2024-03-01', None,         'Present',  None),
    ('104','SAE Narrative',                   'Safety',     'SAE Narrative — Not Required',      None,   None,                                             None,         None,         'Missing',  'No SAEs at this site'),
    ('104','Previous Visit Follow-up Letter', 'Regulatory', 'Follow-up Letter — IMV-2',          None,   'tmf_documents/site_104/followup_imv2.pdf',       '2025-01-30', None,         'Present',  None),
]

# Site 105 — 8/12 present, 2 Missing, 1 Expiring, 1 Superseded → score ~67%
tmf_105 = [
    ('105','Delegation Log',                  'Staff',      'Site Delegation Log v1.0',         'v1.0', 'tmf_documents/site_105/delegation_log_v1.pdf',   '2024-04-01', None,         'Present',  None),
    ('105','IRB Ethics Approval',             'Regulatory', 'IRB Initial Approval — NVX-1218.22','v1.0', 'tmf_documents/site_105/irb_approval_2024.pdf',  '2024-04-05', '2025-04-05', 'Expiring', 'Renewal due 2025-04-05 — submit renewal application immediately'),
    ('105','IRB Approval Amendment',          'Regulatory', 'IRB Amendment Approval v2.1',       'v2.1', 'tmf_documents/site_105/irb_amendment_v2_1.pdf', '2024-12-20', None,         'Present',  None),
    ('105','ICF Current Version',             'Consent',    'Informed Consent Form v1.0',        'v1.0', 'tmf_documents/site_105/icf_v1_0.pdf',           '2024-04-01', None,         'Superseded','ICF v2.1 not filed — subjects to be re-consented'),
    ('105','Investigator CV',                 'Staff',      'CV — Dr. Wei Zhang',                'v2.0', 'tmf_documents/site_105/pi_cv.pdf',              '2024-01-15', '2026-01-15', 'Present',  None),
    ('105','GCP Certificate PI',              'Staff',      'GCP Certificate — Dr. Wei Zhang',   '2023', 'tmf_documents/site_105/gcp_cert_pi.pdf',        '2023-08-10', '2025-08-10', 'Present',  None),
    ('105','GCP Certificate Coordinator',     'Staff',      'GCP Certificate — Lisa Tan',        '2024', 'tmf_documents/site_105/gcp_cert_coord.pdf',     '2024-02-28', '2026-02-28', 'Present',  None),
    ('105','Lab Certification',               'Lab',        'Central Lab Accreditation',         None,   None,                                             None,         None,         'Missing',  'Lab certification not uploaded — required before next subject visit'),
    ('105','Lab Normal Ranges',               'Lab',        'Lab Normal Ranges — NVX-1218.22',   'v2.0', 'tmf_documents/site_105/lab_normal_ranges.pdf', '2024-06-01', '2025-06-01', 'Present',  None),
    ('105','Drug Accountability Log',         'IP',         'Drug Accountability Log — Site 105',None,   None,                                             None,         None,         'Missing',  'Drug accountability log not filed — critical gap requiring immediate action'),
    ('105','SAE Narrative',                   'Safety',     'SAE Narrative — Not Required',      None,   None,                                             None,         None,         'Missing',  'No SAEs at this site'),
    ('105','Previous Visit Follow-up Letter', 'Regulatory', 'Follow-up Letter — IMV-1',          None,   'tmf_documents/site_105/followup_imv1.pdf',       '2024-11-14', None,         'Present',  None),
]

all_tmf = tmf_101 + tmf_102 + tmf_103 + tmf_104 + tmf_105
cur.executemany("""
    INSERT INTO tmf_documents
        (site_id, document_type, category, title, version, file_path,
         document_date, expiry_date, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", all_tmf)

conn.commit()
print("✓ TMF requirements and documents seeded (5 sites, 60 document records)")

# Get statistics
print("\n5. Database Statistics:")
tables = [
    'sites', 'subjects', 'demographics', 'visits', 'vital_signs',
    'laboratory_results', 'adverse_events', 'medical_history',
    'concomitant_medications', 'tumor_assessments', 'ecg_results',
    'protocol_deviations', 'queries',
    'monitoring_visits', 'monitoring_visit_subjects', 'visit_findings', 'visit_reports',
    'tmf_requirements', 'tmf_documents'
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
