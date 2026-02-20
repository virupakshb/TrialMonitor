# Clinical Trial Data Dictionary
## Protocol NVX-1218.22 - NovaPlex-450 in Advanced NSCLC

---

## Table: protocol_info

Protocol-level metadata for the clinical trial.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | SERIAL | Auto-increment primary key | 1 |
| protocol_number | VARCHAR(50) | Unique protocol identifier | NVX-1218.22 |
| protocol_name | TEXT | Full protocol title | A Phase III, Randomized... |
| short_title | VARCHAR(255) | Abbreviated title | NovaPlex-450 in Advanced NSCLC |
| sponsor_name | VARCHAR(255) | Legal name of sponsor | NexaVance Therapeutics Inc. |
| sponsor_address | TEXT | Sponsor physical address | 1250 Innovation Drive... |
| phase | VARCHAR(20) | Clinical trial phase | III |
| indication | VARCHAR(255) | Disease being studied | Advanced Non-Small Cell Lung Cancer |
| study_type | VARCHAR(100) | Type of study | Interventional |
| study_design | TEXT | Study design description | Randomized, Double-Blind... |
| therapeutic_area | VARCHAR(100) | Medical specialty | Oncology |
| investigational_product | VARCHAR(255) | Drug being tested | NovaPlex-450 |
| primary_objective | TEXT | Main study objective | To evaluate PFS... |
| primary_endpoint | TEXT | Primary efficacy measure | Progression-Free Survival |
| planned_sample_size | INTEGER | Target enrollment | 400 |
| study_start_date | DATE | Study start date | 2024-03-15 |
| estimated_completion_date | DATE | Expected study end | 2026-09-15 |

---

## Table: sites

Clinical trial investigational sites.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| site_id | VARCHAR(20) | Unique site identifier | 101 |
| site_name | VARCHAR(255) | Site name | Memorial Cancer Center |
| country | VARCHAR(100) | Country | United States |
| city | VARCHAR(100) | City | Boston |
| state_province | VARCHAR(100) | State/Province | Massachusetts |
| principal_investigator | VARCHAR(255) | Lead investigator | Dr. Emily Chen |
| site_coordinator | VARCHAR(255) | Study coordinator | Jessica Martinez |
| contact_email | VARCHAR(255) | Site email | trials@memorialcancer.org |
| contact_phone | VARCHAR(50) | Site phone | +1-617-555-0101 |
| activation_date | DATE | Site activation date | 2024-03-15 |
| site_status | VARCHAR(50) | Current status | Active, Closed, On Hold |
| planned_enrollment | INTEGER | Target subjects | 30 |
| actual_enrollment | INTEGER | Enrolled subjects | 25 |

---

## Table: subjects

Study participants enrolled in the trial.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| subject_id | VARCHAR(20) | Unique subject identifier | 101-001 |
| site_id | VARCHAR(20) | Foreign key to sites | 101 |
| screening_number | VARCHAR(20) | Screening ID | SCR-001 |
| randomization_number | VARCHAR(20) | Randomization ID | RAND-001 |
| initials | VARCHAR(10) | Patient initials | JD |
| treatment_arm | INTEGER | Treatment group (1 or 2) | 1 |
| treatment_arm_name | VARCHAR(100) | Arm description | NovaPlex-450 + Chemo |
| randomization_date | DATE | Date randomized | 2024-03-25 |
| screening_date | DATE | Date screened | 2024-03-15 |
| consent_date | DATE | Date consented | 2024-03-15 |
| study_status | VARCHAR(50) | Current status | Enrolled, Completed, Discontinued |
| discontinuation_date | DATE | Date discontinued | NULL or date |
| discontinuation_reason | TEXT | Reason for discontinuation | Disease Progression, AE, etc. |

---

## Table: demographics

Patient demographic and baseline characteristics.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| date_of_birth | DATE | Date of birth | 1958-06-15 |
| age | INTEGER | Age at screening | 65 |
| sex | VARCHAR(10) | Biological sex | Male, Female |
| race | VARCHAR(100) | Race category | White, Black, Asian, Other |
| ethnicity | VARCHAR(100) | Ethnicity | Hispanic or Latino, Not Hispanic |
| weight_kg | DECIMAL(5,2) | Weight in kilograms | 78.5 |
| height_cm | DECIMAL(5,2) | Height in centimeters | 175.3 |
| bmi | DECIMAL(5,2) | Body mass index | 25.5 |
| ecog_performance_status | INTEGER | ECOG PS (0-2) | 0, 1, 2 |
| smoking_status | VARCHAR(50) | Smoking history | Current, Former, Never |
| smoking_pack_years | DECIMAL(5,2) | Pack-years of smoking | 30.5 |

---

## Table: visits

Study visit schedule and tracking.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| visit_id | SERIAL | Auto-increment primary key | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| visit_number | INTEGER | Sequential visit number | 1, 2, 3... |
| visit_name | VARCHAR(100) | Visit name | Screening, Baseline, Week 3 |
| scheduled_date | DATE | Planned visit date | 2024-03-15 |
| actual_date | DATE | Actual visit date | 2024-03-17 |
| visit_status | VARCHAR(50) | Status | Scheduled, Completed, Missed |
| window_lower_days | INTEGER | Lower window bound | -3 |
| window_upper_days | INTEGER | Upper window bound | 3 |
| days_from_randomization | INTEGER | Days since randomization | 21 |
| visit_type | VARCHAR(50) | Type of visit | Scheduled, Unscheduled |
| visit_completed | BOOLEAN | Completion flag | true, false |
| missed_visit | BOOLEAN | Missed flag | false, true |
| visit_notes | TEXT | Additional notes | NULL or text |

---

## Table: vital_signs

Vital signs measurements.

| Field | Type | Description | Example | Normal Range |
|-------|------|-------------|---------|--------------|
| id | SERIAL | Primary key | 1 | - |
| visit_id | INTEGER | Foreign key to visits | 1 | - |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 | - |
| assessment_date | DATE | Measurement date | 2024-03-15 | - |
| assessment_time | TIME | Measurement time | 10:30:00 | - |
| systolic_bp | INTEGER | Systolic BP (mmHg) | 125 | 90-140 |
| diastolic_bp | INTEGER | Diastolic BP (mmHg) | 80 | 60-90 |
| heart_rate | INTEGER | Heart rate (bpm) | 75 | 60-100 |
| temperature_celsius | DECIMAL(4,2) | Body temp (°C) | 36.8 | 36.5-37.5 |
| respiratory_rate | INTEGER | Resp rate (breaths/min) | 16 | 12-20 |
| weight_kg | DECIMAL(5,2) | Weight (kg) | 78.5 | - |
| oxygen_saturation | INTEGER | O2 sat (%) | 97 | 95-100 |
| position | VARCHAR(50) | Patient position | Sitting, Standing | - |
| notes | TEXT | Additional notes | NULL or text | - |

---

## Table: laboratory_results

Laboratory test results (Hematology, Chemistry, Coagulation).

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| visit_id | INTEGER | Foreign key to visits | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| collection_date | DATE | Sample collection date | 2024-03-15 |
| collection_time | TIME | Collection time | 08:00:00 |
| lab_category | VARCHAR(50) | Test category | Hematology, Chemistry, Coagulation |
| test_name | VARCHAR(100) | Test name | WBC, ALT, Hemoglobin |
| test_value | DECIMAL(12,4) | Test result value | 5.5 |
| test_unit | VARCHAR(50) | Unit of measurement | 10^9/L, U/L, g/dL |
| normal_range_lower | DECIMAL(12,4) | Lower limit of normal | 4.5 |
| normal_range_upper | DECIMAL(12,4) | Upper limit of normal | 11.0 |
| abnormal_flag | VARCHAR(10) | Abnormality flag | Normal, Low, High |
| clinically_significant | BOOLEAN | Clinical significance | true, false |
| lab_comments | TEXT | Lab comments | NULL or text |

### Common Lab Tests

**Hematology:**
- WBC (4.5-11.0 × 10^9/L)
- RBC (4.0-5.5 × 10^12/L)
- Hemoglobin (12.0-16.0 g/dL)
- Platelets (150-400 × 10^9/L)
- Neutrophils (2.0-7.5 × 10^9/L)
- Lymphocytes (1.0-4.0 × 10^9/L)

**Chemistry:**
- ALT (7-56 U/L)
- AST (10-40 U/L)
- Bilirubin (0.3-1.2 mg/dL)
- Creatinine (0.6-1.2 mg/dL)
- Glucose (70-100 mg/dL)
- Albumin (3.5-5.0 g/dL)

**Coagulation:**
- PT (11.0-13.5 seconds)
- PTT (25-35 seconds)
- INR (0.9-1.1 ratio)

---

## Table: adverse_events

Adverse events and serious adverse events.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| ae_id | SERIAL | Primary key | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| ae_term | VARCHAR(255) | AE description | Fatigue, Nausea, Pneumonitis |
| meddra_code | VARCHAR(20) | MedDRA code | PT10029533 |
| meddra_preferred_term | VARCHAR(255) | MedDRA PT | Fatigue |
| onset_date | DATE | AE start date | 2024-04-01 |
| resolution_date | DATE | AE end date | 2024-04-15 or NULL |
| ongoing | BOOLEAN | Still ongoing? | true, false |
| severity | VARCHAR(20) | Severity grade | Mild, Moderate, Severe |
| ctcae_grade | INTEGER | CTCAE grade (1-5) | 1, 2, 3, 4, 5 |
| seriousness | VARCHAR(10) | Is serious? | Yes, No |
| serious_criteria | TEXT | SAE criteria | Hospitalization, Life-threatening |
| relationship_to_study_drug | VARCHAR(50) | Causality | Related, Possibly Related, Unrelated |
| action_taken | VARCHAR(100) | Action | None, Interrupted, Discontinued |
| outcome | VARCHAR(100) | Final outcome | Resolved, Not Resolved, Fatal |
| ae_description | TEXT | Detailed description | Full AE narrative |
| reporter | VARCHAR(100) | Who reported | Investigator, Patient |

**Severity Grades:**
- Mild (Grade 1): No intervention needed
- Moderate (Grade 2): Minimal intervention needed
- Severe (Grade 3): Medically significant
- Life-threatening (Grade 4): Urgent intervention needed
- Death (Grade 5): Death related to AE

---

## Table: medical_history

Patient medical history and comorbidities.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| condition | VARCHAR(255) | Medical condition | Hypertension, COPD, Diabetes |
| meddra_code | VARCHAR(20) | MedDRA code | PT10019133 |
| diagnosis_date | DATE | Date diagnosed | 2020-01-15 |
| ongoing | BOOLEAN | Still present? | true, false |
| resolution_date | DATE | Date resolved | NULL or date |
| condition_category | VARCHAR(100) | Category | Comorbidity, Primary Diagnosis |
| condition_notes | TEXT | Additional notes | NULL or text |

---

## Table: concomitant_medications

Medications taken during the study.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| medication_name | VARCHAR(255) | Drug name | Lisinopril, Metformin |
| who_drug_code | VARCHAR(50) | WHO drug code | WHO1234 |
| indication | VARCHAR(255) | Reason for use | Hypertension, Diabetes |
| dose | VARCHAR(100) | Dose amount | 10 mg, 500 mg |
| dose_unit | VARCHAR(50) | Dose unit | mg, mcg |
| frequency | VARCHAR(100) | Dosing frequency | QD, BID, PRN |
| route | VARCHAR(50) | Route of admin | Oral, IV, Subcutaneous |
| start_date | DATE | Start date | 2023-01-01 |
| end_date | DATE | End date | NULL or date |
| ongoing | BOOLEAN | Still taking? | true, false |
| medication_class | VARCHAR(100) | Drug class | Concomitant, Prior |

**Common Frequencies:**
- QD: Once daily
- BID: Twice daily
- TID: Three times daily
- QID: Four times daily
- Q3W: Every 3 weeks
- PRN: As needed
- QHS: At bedtime

---

## Table: tumor_assessments

Tumor response assessments per RECIST 1.1.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| visit_id | INTEGER | Foreign key to visits | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| assessment_date | DATE | Scan date | 2024-03-15 |
| assessment_method | VARCHAR(50) | Imaging type | CT Scan, MRI |
| overall_response | VARCHAR(50) | RECIST response | CR, PR, SD, PD |
| target_lesion_sum | DECIMAL(6,2) | Sum of diameters (mm) | 85.5 |
| new_lesions | BOOLEAN | New lesions present? | true, false |
| progression | BOOLEAN | Disease progression? | true, false |
| assessment_notes | TEXT | Additional notes | Per RECIST 1.1 |
| radiologist | VARCHAR(255) | Reader | Central Reader, Site |

**RECIST 1.1 Responses:**
- CR (Complete Response): Disappearance of all lesions
- PR (Partial Response): ≥30% decrease in sum
- SD (Stable Disease): Neither PR nor PD
- PD (Progressive Disease): ≥20% increase or new lesions

---

## Table: ecg_results

12-lead ECG results and QTc monitoring.

| Field | Type | Description | Example | Normal Range |
|-------|------|-------------|---------|--------------|
| id | SERIAL | Primary key | 1 | - |
| visit_id | INTEGER | Foreign key to visits | 1 | - |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 | - |
| ecg_date | DATE | ECG date | 2024-03-15 | - |
| ecg_time | TIME | ECG time | 11:00:00 | - |
| heart_rate | INTEGER | Heart rate (bpm) | 75 | 60-100 |
| pr_interval | INTEGER | PR interval (ms) | 160 | 120-200 |
| qrs_duration | INTEGER | QRS duration (ms) | 95 | 80-120 |
| qt_interval | INTEGER | QT interval (ms) | 400 | 350-450 |
| qtc_interval | INTEGER | QTc (Bazett) (ms) | 420 | <450 (M), <470 (F) |
| qtcf_interval | INTEGER | QTcF (Fridericia) (ms) | 418 | <450 (M), <470 (F) |
| interpretation | VARCHAR(255) | ECG interpretation | Normal Sinus Rhythm |  - |
| abnormal | BOOLEAN | Abnormal? | true, false | - |
| clinically_significant | BOOLEAN | Clinically significant? | true, false | - |
| reader | VARCHAR(255) | Who read | Central ECG Laboratory | - |

**QTc Prolongation Grades:**
- Normal: <450 ms (male), <470 ms (female)
- Borderline: 450-470 ms (male), 470-480 ms (female)
- Prolonged: >470 ms (male), >480 ms (female)
- Severe: >500 ms

---

## Table: protocol_deviations

Protocol violations and deviations.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| deviation_id | SERIAL | Primary key | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| deviation_type | VARCHAR(100) | Type of deviation | Visit Window Violation |
| deviation_category | VARCHAR(100) | Category | Protocol Compliance, Safety |
| description | TEXT | Full description | Visit 3 conducted 8 days late |
| deviation_date | DATE | Date of deviation | 2024-04-01 |
| reported_date | DATE | Date reported | 2024-04-03 |
| severity | VARCHAR(20) | Severity | Minor, Major, Critical |
| impact_on_data | BOOLEAN | Impacts data? | true, false |
| impact_on_safety | BOOLEAN | Impacts safety? | true, false |
| corrective_action | TEXT | Corrective action | Site counseled |
| preventive_action | TEXT | Preventive action | Enhanced reminders |
| status | VARCHAR(50) | Current status | Open, Closed |
| resolution_date | DATE | Date resolved | 2024-04-10 or NULL |

**Deviation Types:**
- Visit Window Violation
- Missed Assessment
- Eligibility Violation
- Incorrect Dosing
- Consent Violation
- Protocol Procedure Not Followed

---

## Table: queries

Data queries for resolution.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| query_id | SERIAL | Primary key | 1 |
| subject_id | VARCHAR(20) | Foreign key to subjects | 101-001 |
| visit_id | INTEGER | Foreign key to visits | 1 |
| query_type | VARCHAR(100) | Type of query | Missing Data, Inconsistency |
| query_category | VARCHAR(100) | Category | Data Quality, Safety |
| query_text | TEXT | Query description | Required field not completed |
| query_date | DATE | Date query raised | 2024-04-01 |
| query_status | VARCHAR(50) | Current status | Open, Closed, Answered |
| assigned_to | VARCHAR(255) | Assignee | Site Coordinator, CRA |
| priority | VARCHAR(20) | Priority level | Low, Medium, High, Critical |
| response_text | TEXT | Site response | Query resolved... |
| response_date | DATE | Date responded | 2024-04-05 or NULL |
| resolution_date | DATE | Date resolved | 2024-04-05 or NULL |

**Query Types:**
- Missing Data: Required field blank
- Data Inconsistency: Contradictory data
- Out of Range Value: Impossible or unlikely value
- AE Clarification: Need more AE details
- Protocol Deviation: Explain deviation
- Safety Concern: Safety-related clarification

---

## Appendix: Common Value Sets

### Study Status
- Enrolled: Currently participating
- Completed: Finished all protocol activities
- Discontinued: Early termination
- Screen Failed: Did not meet eligibility

### Discontinuation Reasons
- Adverse Event
- Disease Progression
- Withdrawal of Consent
- Lost to Follow-up
- Protocol Violation
- Physician Decision
- Death

### Treatment Arms
- Arm 1: NovaPlex-450 + Chemotherapy
- Arm 2: Placebo + Chemotherapy

### ECOG Performance Status
- 0: Fully active
- 1: Restricted in physically strenuous activity
- 2: Ambulatory, capable of self-care

### Site Status
- Active: Enrolling subjects
- Closed: No longer enrolling
- On Hold: Temporarily paused

---

**Document Version:** 1.0  
**Last Updated:** 2025-02-17  
**Protocol:** NVX-1218.22  
**Sponsor:** NexaVance Therapeutics Inc.
