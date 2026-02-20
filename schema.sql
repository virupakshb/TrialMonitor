-- Clinical Trial Monitoring System - Database Schema
-- Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
-- Sponsor: NexaVance Therapeutics Inc.

-- ============================================================================
-- DROP EXISTING TABLES (for clean re-creation)
-- ============================================================================

DROP TABLE IF EXISTS queries CASCADE;
DROP TABLE IF EXISTS protocol_deviations CASCADE;
DROP TABLE IF EXISTS ecg_results CASCADE;
DROP TABLE IF EXISTS tumor_assessments CASCADE;
DROP TABLE IF EXISTS concomitant_medications CASCADE;
DROP TABLE IF EXISTS medical_history CASCADE;
DROP TABLE IF EXISTS adverse_events CASCADE;
DROP TABLE IF EXISTS laboratory_results CASCADE;
DROP TABLE IF EXISTS vital_signs CASCADE;
DROP TABLE IF EXISTS visits CASCADE;
DROP TABLE IF EXISTS demographics CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS sites CASCADE;
DROP TABLE IF EXISTS protocol_info CASCADE;

-- ============================================================================
-- PROTOCOL INFORMATION
-- ============================================================================

CREATE TABLE protocol_info (
    id SERIAL PRIMARY KEY,
    protocol_number VARCHAR(50) NOT NULL UNIQUE,
    protocol_name TEXT NOT NULL,
    short_title VARCHAR(255),
    sponsor_name VARCHAR(255) NOT NULL,
    sponsor_address TEXT,
    phase VARCHAR(20),
    indication VARCHAR(255),
    study_type VARCHAR(100),
    study_design TEXT,
    therapeutic_area VARCHAR(100),
    investigational_product VARCHAR(255),
    primary_objective TEXT,
    primary_endpoint TEXT,
    planned_sample_size INTEGER,
    study_start_date DATE,
    estimated_completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SITES
-- ============================================================================

CREATE TABLE sites (
    site_id VARCHAR(20) PRIMARY KEY,
    site_name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    state_province VARCHAR(100),
    principal_investigator VARCHAR(255) NOT NULL,
    site_coordinator VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    activation_date DATE,
    site_status VARCHAR(50) DEFAULT 'Active',
    planned_enrollment INTEGER,
    actual_enrollment INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SUBJECTS
-- ============================================================================

CREATE TABLE subjects (
    subject_id VARCHAR(20) PRIMARY KEY,
    site_id VARCHAR(20) REFERENCES sites(site_id),
    screening_number VARCHAR(20) UNIQUE,
    randomization_number VARCHAR(20) UNIQUE,
    initials VARCHAR(10),
    treatment_arm INTEGER CHECK (treatment_arm IN (1, 2)),
    treatment_arm_name VARCHAR(100),
    randomization_date DATE,
    screening_date DATE,
    consent_date DATE,
    study_status VARCHAR(50) DEFAULT 'Enrolled',
    discontinuation_date DATE,
    discontinuation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DEMOGRAPHICS
-- ============================================================================

CREATE TABLE demographics (
    id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    date_of_birth DATE,
    age INTEGER,
    sex VARCHAR(10) CHECK (sex IN ('Male', 'Female', 'Other')),
    race VARCHAR(100),
    ethnicity VARCHAR(100),
    weight_kg DECIMAL(5,2),
    height_cm DECIMAL(5,2),
    bmi DECIMAL(5,2),
    ecog_performance_status INTEGER CHECK (ecog_performance_status IN (0, 1, 2)),
    smoking_status VARCHAR(50),
    smoking_pack_years DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject_id)
);

-- ============================================================================
-- VISITS
-- ============================================================================

CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    visit_number INTEGER NOT NULL,
    visit_name VARCHAR(100) NOT NULL,
    scheduled_date DATE NOT NULL,
    actual_date DATE,
    visit_status VARCHAR(50) DEFAULT 'Scheduled',
    window_lower_days INTEGER,
    window_upper_days INTEGER,
    days_from_randomization INTEGER,
    visit_type VARCHAR(50),
    visit_completed BOOLEAN DEFAULT FALSE,
    missed_visit BOOLEAN DEFAULT FALSE,
    visit_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject_id, visit_number)
);

-- ============================================================================
-- VITAL SIGNS
-- ============================================================================

CREATE TABLE vital_signs (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(visit_id),
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    assessment_date DATE NOT NULL,
    assessment_time TIME,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature_celsius DECIMAL(4,2),
    respiratory_rate INTEGER,
    weight_kg DECIMAL(5,2),
    oxygen_saturation INTEGER,
    position VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LABORATORY RESULTS
-- ============================================================================

CREATE TABLE laboratory_results (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(visit_id),
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    collection_date DATE NOT NULL,
    collection_time TIME,
    lab_category VARCHAR(50) NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    test_value DECIMAL(12,4),
    test_unit VARCHAR(50),
    normal_range_lower DECIMAL(12,4),
    normal_range_upper DECIMAL(12,4),
    abnormal_flag VARCHAR(10),
    clinically_significant BOOLEAN DEFAULT FALSE,
    lab_comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ADVERSE EVENTS
-- ============================================================================

CREATE TABLE adverse_events (
    ae_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    ae_term VARCHAR(255) NOT NULL,
    meddra_code VARCHAR(20),
    meddra_preferred_term VARCHAR(255),
    onset_date DATE NOT NULL,
    resolution_date DATE,
    ongoing BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20) CHECK (severity IN ('Mild', 'Moderate', 'Severe', 'Life-threatening', 'Death')),
    ctcae_grade INTEGER CHECK (ctcae_grade IN (1, 2, 3, 4, 5)),
    seriousness VARCHAR(10) CHECK (seriousness IN ('Yes', 'No')),
    serious_criteria TEXT,
    relationship_to_study_drug VARCHAR(50),
    action_taken VARCHAR(100),
    outcome VARCHAR(100),
    ae_description TEXT,
    reporter VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MEDICAL HISTORY
-- ============================================================================

CREATE TABLE medical_history (
    id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    condition VARCHAR(255) NOT NULL,
    meddra_code VARCHAR(20),
    diagnosis_date DATE,
    ongoing BOOLEAN DEFAULT FALSE,
    resolution_date DATE,
    condition_category VARCHAR(100),
    condition_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONCOMITANT MEDICATIONS
-- ============================================================================

CREATE TABLE concomitant_medications (
    id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    medication_name VARCHAR(255) NOT NULL,
    who_drug_code VARCHAR(50),
    indication VARCHAR(255),
    dose VARCHAR(100),
    dose_unit VARCHAR(50),
    frequency VARCHAR(100),
    route VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    ongoing BOOLEAN DEFAULT TRUE,
    medication_class VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TUMOR ASSESSMENTS
-- ============================================================================

CREATE TABLE tumor_assessments (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(visit_id),
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    assessment_date DATE NOT NULL,
    assessment_method VARCHAR(50),
    overall_response VARCHAR(50),
    target_lesion_sum DECIMAL(6,2),
    new_lesions BOOLEAN DEFAULT FALSE,
    progression BOOLEAN DEFAULT FALSE,
    assessment_notes TEXT,
    radiologist VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ECG RESULTS
-- ============================================================================

CREATE TABLE ecg_results (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(visit_id),
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    ecg_date DATE NOT NULL,
    ecg_time TIME,
    heart_rate INTEGER,
    pr_interval INTEGER,
    qrs_duration INTEGER,
    qt_interval INTEGER,
    qtc_interval INTEGER,
    qtcf_interval INTEGER,
    interpretation VARCHAR(255),
    abnormal BOOLEAN DEFAULT FALSE,
    clinically_significant BOOLEAN DEFAULT FALSE,
    reader VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PROTOCOL DEVIATIONS
-- ============================================================================

CREATE TABLE protocol_deviations (
    deviation_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    deviation_type VARCHAR(100) NOT NULL,
    deviation_category VARCHAR(100),
    description TEXT NOT NULL,
    deviation_date DATE NOT NULL,
    reported_date DATE,
    severity VARCHAR(20) CHECK (severity IN ('Minor', 'Major', 'Critical')),
    impact_on_data BOOLEAN DEFAULT FALSE,
    impact_on_safety BOOLEAN DEFAULT FALSE,
    corrective_action TEXT,
    preventive_action TEXT,
    status VARCHAR(50) DEFAULT 'Open',
    resolution_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUERIES
-- ============================================================================

CREATE TABLE queries (
    query_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(20) REFERENCES subjects(subject_id),
    visit_id INTEGER REFERENCES visits(visit_id),
    query_type VARCHAR(100) NOT NULL,
    query_category VARCHAR(100),
    query_text TEXT NOT NULL,
    query_date DATE NOT NULL,
    query_status VARCHAR(50) DEFAULT 'Open',
    assigned_to VARCHAR(255),
    priority VARCHAR(20) CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    response_text TEXT,
    response_date DATE,
    resolution_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_subjects_site ON subjects(site_id);
CREATE INDEX idx_subjects_status ON subjects(study_status);
CREATE INDEX idx_subjects_treatment_arm ON subjects(treatment_arm);

CREATE INDEX idx_visits_subject ON visits(subject_id);
CREATE INDEX idx_visits_date ON visits(actual_date);
CREATE INDEX idx_visits_status ON visits(visit_status);

CREATE INDEX idx_vitals_subject ON vital_signs(subject_id);
CREATE INDEX idx_vitals_visit ON vital_signs(visit_id);

CREATE INDEX idx_labs_subject ON laboratory_results(subject_id);
CREATE INDEX idx_labs_visit ON laboratory_results(visit_id);
CREATE INDEX idx_labs_category ON laboratory_results(lab_category);
CREATE INDEX idx_labs_abnormal ON laboratory_results(abnormal_flag);

CREATE INDEX idx_ae_subject ON adverse_events(subject_id);
CREATE INDEX idx_ae_severity ON adverse_events(severity);
CREATE INDEX idx_ae_seriousness ON adverse_events(seriousness);
CREATE INDEX idx_ae_ongoing ON adverse_events(ongoing);

CREATE INDEX idx_queries_subject ON queries(subject_id);
CREATE INDEX idx_queries_status ON queries(query_status);
CREATE INDEX idx_queries_priority ON queries(priority);

CREATE INDEX idx_deviations_subject ON protocol_deviations(subject_id);
CREATE INDEX idx_deviations_type ON protocol_deviations(deviation_type);
CREATE INDEX idx_deviations_status ON protocol_deviations(status);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE protocol_info IS 'Stores protocol-level information for NVX-1218.22';
COMMENT ON TABLE sites IS 'Clinical trial investigational sites';
COMMENT ON TABLE subjects IS 'Study subjects/patients enrolled in the trial';
COMMENT ON TABLE demographics IS 'Patient demographic and baseline characteristics';
COMMENT ON TABLE visits IS 'Study visit schedule and completion tracking';
COMMENT ON TABLE vital_signs IS 'Vital signs measurements captured during visits';
COMMENT ON TABLE laboratory_results IS 'Laboratory test results (Hematology, Chemistry, Coagulation)';
COMMENT ON TABLE adverse_events IS 'Adverse events and serious adverse events';
COMMENT ON TABLE medical_history IS 'Patient medical history and comorbidities';
COMMENT ON TABLE concomitant_medications IS 'Medications taken during the study';
COMMENT ON TABLE tumor_assessments IS 'Tumor response assessments per RECIST 1.1';
COMMENT ON TABLE ecg_results IS '12-lead ECG results including QTc monitoring';
COMMENT ON TABLE protocol_deviations IS 'Protocol violations and deviations';
COMMENT ON TABLE queries IS 'Data queries raised by monitors and CRAs';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
