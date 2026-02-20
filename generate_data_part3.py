"""
Clinical Trial Synthetic Data Generator - Part 3
Generates: Adverse Events, Medical History, Concomitant Medications,
           Tumor Assessments, ECG Results, Protocol Deviations, Queries

This script depends on synthetic_data_part1.json and synthetic_data_part2.json
"""

import json
import random
from datetime import datetime, timedelta
import numpy as np

# Set random seed for reproducibility
random.seed(1218)
np.random.seed(1218)

# Load previous data
with open('protocol_definition.json', 'r') as f:
    protocol_data = json.load(f)
    protocol = protocol_data['protocol']

with open('synthetic_data_part1.json', 'r') as f:
    part1_data = json.load(f)
    subjects_data = part1_data['subjects']

with open('synthetic_data_part2.json', 'r') as f:
    part2_data = json.load(f)
    visits_data = part2_data['visits']

# ============================================================================
# ADVERSE EVENTS GENERATION
# ============================================================================

# Common AEs in oncology immunotherapy trials
ae_terms = [
    ('Fatigue', 'Mild', 1, 'Related'),
    ('Nausea', 'Mild', 1, 'Related'),
    ('Diarrhea', 'Moderate', 2, 'Related'),
    ('Rash', 'Mild', 1, 'Related'),
    ('Pruritus', 'Mild', 1, 'Related'),
    ('Decreased Appetite', 'Mild', 1, 'Related'),
    ('Headache', 'Mild', 1, 'Unrelated'),
    ('Cough', 'Mild', 1, 'Unrelated'),
    ('Arthralgia', 'Moderate', 2, 'Possibly Related'),
    ('Pyrexia', 'Moderate', 2, 'Related'),
    ('Hypothyroidism', 'Moderate', 2, 'Related'),
    ('Pneumonitis', 'Severe', 3, 'Related'),  # Serious
    ('Colitis', 'Severe', 3, 'Related'),  # Serious
    ('Hepatitis', 'Severe', 3, 'Related'),  # Serious
    ('Infusion Reaction', 'Moderate', 2, 'Related'),
    ('Anemia', 'Moderate', 2, 'Possibly Related'),
    ('Neutropenia', 'Severe', 3, 'Related'),
    ('Thrombocytopenia', 'Moderate', 2, 'Possibly Related'),
]

adverse_events_data = []
ae_counter = 1

for subject in subjects_data:
    subject_id = subject['subject_id']
    randomization_date = datetime.strptime(subject['randomization_date'], '%Y-%m-%d')
    treatment_arm = subject['treatment_arm']
    
    # Treatment arm 1 (active) has more AEs
    if treatment_arm == 1:
        num_aes = random.randint(2, 5)
    else:
        num_aes = random.randint(1, 3)
    
    # Generate AEs for this subject
    selected_aes = random.sample(ae_terms, min(num_aes, len(ae_terms)))
    
    for ae_term, severity, grade, relationship in selected_aes:
        onset_day = random.randint(7, 150)
        onset_date = randomization_date + timedelta(days=onset_day)
        
        # 80% resolved, 20% ongoing
        if random.random() < 0.80:
            duration_days = random.randint(3, 30)
            resolution_date = onset_date + timedelta(days=duration_days)
            ongoing = False
            outcome = random.choice(['Resolved', 'Resolved with sequelae', 'Recovering'])
        else:
            resolution_date = None
            ongoing = True
            outcome = 'Not Resolved'
        
        # Serious AEs (5% chance for severe events)
        if severity == 'Severe' and random.random() < 0.30:
            seriousness = 'Yes'
            serious_criteria = random.choice([
                'Medically Significant',
                'Required Hospitalization',
                'Life-Threatening'
            ])
        else:
            seriousness = 'No'
            serious_criteria = None
        
        action_taken = 'None'
        if severity == 'Severe':
            action_taken = random.choice([
                'Drug Interrupted',
                'Dose Reduced',
                'Drug Discontinued'
            ])
        elif severity == 'Moderate' and random.random() < 0.30:
            action_taken = 'Dose Not Changed'
        
        ae = {
            'subject_id': subject_id,
            'ae_term': ae_term,
            'meddra_code': f"PT{random.randint(10000000, 99999999)}",
            'meddra_preferred_term': ae_term,
            'onset_date': onset_date.strftime('%Y-%m-%d'),
            'resolution_date': resolution_date.strftime('%Y-%m-%d') if resolution_date else None,
            'ongoing': ongoing,
            'severity': severity,
            'ctcae_grade': grade,
            'seriousness': seriousness,
            'serious_criteria': serious_criteria,
            'relationship_to_study_drug': relationship,
            'action_taken': action_taken,
            'outcome': outcome,
            'ae_description': f"{ae_term} reported by patient",
            'reporter': 'Investigator'
        }
        adverse_events_data.append(ae)
        ae_counter += 1

print(f"Generated {len(adverse_events_data)} adverse events")

# ============================================================================
# MEDICAL HISTORY GENERATION
# ============================================================================

# Common comorbidities in NSCLC patients
medical_conditions = [
    'Hypertension',
    'Type 2 Diabetes Mellitus',
    'Chronic Obstructive Pulmonary Disease',
    'Coronary Artery Disease',
    'Atrial Fibrillation',
    'Hyperlipidemia',
    'Osteoarthritis',
    'Gastroesophageal Reflux Disease',
    'Anxiety Disorder',
    'Depression',
]

medical_history_data = []

for subject in subjects_data:
    subject_id = subject['subject_id']
    screening_date = datetime.strptime(subject['screening_date'], '%Y-%m-%d')
    
    # Cancer diagnosis (all patients)
    cancer_dx_date = screening_date - timedelta(days=random.randint(90, 730))
    med_hist = {
        'subject_id': subject_id,
        'condition': 'Non-Small Cell Lung Cancer',
        'meddra_code': 'PT10029533',
        'diagnosis_date': cancer_dx_date.strftime('%Y-%m-%d'),
        'ongoing': True,
        'resolution_date': None,
        'condition_category': 'Primary Diagnosis',
        'condition_notes': 'Stage IV adenocarcinoma'
    }
    medical_history_data.append(med_hist)
    
    # Other comorbidities (2-4 per patient)
    num_comorbidities = random.randint(2, 4)
    selected_conditions = random.sample(medical_conditions, num_comorbidities)
    
    for condition in selected_conditions:
        dx_date = screening_date - timedelta(days=random.randint(365, 3650))
        ongoing = random.random() < 0.80
        
        med_hist = {
            'subject_id': subject_id,
            'condition': condition,
            'meddra_code': f"PT{random.randint(10000000, 99999999)}",
            'diagnosis_date': dx_date.strftime('%Y-%m-%d'),
            'ongoing': ongoing,
            'resolution_date': None if ongoing else (dx_date + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
            'condition_category': 'Comorbidity',
            'condition_notes': None
        }
        medical_history_data.append(med_hist)

print(f"Generated {len(medical_history_data)} medical history records")

# ============================================================================
# CONCOMITANT MEDICATIONS GENERATION
# ============================================================================

# Common medications for cancer patients
medications = [
    ('Lisinopril', 'Hypertension', '10 mg', 'QD', 'Oral'),
    ('Metformin', 'Diabetes', '500 mg', 'BID', 'Oral'),
    ('Atorvastatin', 'Hyperlipidemia', '20 mg', 'QHS', 'Oral'),
    ('Omeprazole', 'GERD', '20 mg', 'QD', 'Oral'),
    ('Albuterol', 'COPD', '90 mcg', 'PRN', 'Inhalation'),
    ('Acetaminophen', 'Pain', '500 mg', 'PRN', 'Oral'),
    ('Ondansetron', 'Nausea', '8 mg', 'PRN', 'Oral'),
    ('Dexamethasone', 'Inflammation', '4 mg', 'QD', 'Oral'),
    ('Lorazepam', 'Anxiety', '0.5 mg', 'PRN', 'Oral'),
    ('Morphine', 'Pain', '15 mg', 'Q4H PRN', 'Oral'),
]

conmed_data = []

for subject in subjects_data:
    subject_id = subject['subject_id']
    randomization_date = datetime.strptime(subject['randomization_date'], '%Y-%m-%d')
    
    # 3-6 concomitant meds per patient
    num_meds = random.randint(3, 6)
    selected_meds = random.sample(medications, num_meds)
    
    for med_name, indication, dose, frequency, route in selected_meds:
        # Started before randomization
        start_date = randomization_date - timedelta(days=random.randint(30, 730))
        
        # 70% ongoing, 30% stopped
        if random.random() < 0.70:
            ongoing = True
            end_date = None
        else:
            ongoing = False
            end_date = randomization_date + timedelta(days=random.randint(7, 100))
        
        conmed = {
            'subject_id': subject_id,
            'medication_name': med_name,
            'who_drug_code': f"WHO{random.randint(1000, 9999)}",
            'indication': indication,
            'dose': dose,
            'dose_unit': dose.split()[1] if len(dose.split()) > 1 else 'mg',
            'frequency': frequency,
            'route': route,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'ongoing': ongoing,
            'medication_class': 'Concomitant'
        }
        conmed_data.append(conmed)

print(f"Generated {len(conmed_data)} concomitant medication records")

# ============================================================================
# TUMOR ASSESSMENTS GENERATION
# ============================================================================

tumor_assessments_data = []

for subject in subjects_data:
    subject_id = subject['subject_id']
    
    # Tumor assessments at baseline and every 9 weeks
    subject_visits = [v for v in visits_data if v['subject_id'] == subject_id and v['visit_completed']]
    
    # Assessment at visits 1, 5, 8, 10 (screening, week 9, week 18, week 24)
    assessment_visits = [v for v in subject_visits if v['visit_number'] in [1, 5, 8, 10]]
    
    baseline_sum = round(np.random.uniform(50, 120), 2)
    
    for idx, visit in enumerate(assessment_visits):
        assessment_date = datetime.strptime(visit['actual_date'], '%Y-%m-%d')
        
        if idx == 0:  # Baseline
            target_sum = baseline_sum
            overall_response = 'Not Applicable'
            new_lesions = False
            progression = False
        else:
            # Simulate response over time
            # 40% partial response, 40% stable, 15% progression, 5% complete response
            response_rand = random.random()
            
            if response_rand < 0.05:  # Complete Response
                target_sum = 0
                overall_response = 'Complete Response'
                new_lesions = False
                progression = False
            elif response_rand < 0.45:  # Partial Response
                reduction_pct = random.uniform(0.30, 0.70)
                target_sum = round(baseline_sum * (1 - reduction_pct), 2)
                overall_response = 'Partial Response'
                new_lesions = False
                progression = False
            elif response_rand < 0.85:  # Stable Disease
                change_pct = random.uniform(-0.25, 0.15)
                target_sum = round(baseline_sum * (1 + change_pct), 2)
                overall_response = 'Stable Disease'
                new_lesions = False
                progression = False
            else:  # Progressive Disease
                increase_pct = random.uniform(0.25, 0.50)
                target_sum = round(baseline_sum * (1 + increase_pct), 2)
                overall_response = 'Progressive Disease'
                new_lesions = random.random() < 0.60
                progression = True
        
        tumor = {
            'subject_id': subject_id,
            'assessment_date': assessment_date.strftime('%Y-%m-%d'),
            'assessment_method': 'CT Scan',
            'overall_response': overall_response,
            'target_lesion_sum': target_sum,
            'new_lesions': new_lesions,
            'progression': progression,
            'assessment_notes': 'Per RECIST 1.1',
            'radiologist': 'Central Reader'
        }
        tumor_assessments_data.append(tumor)

print(f"Generated {len(tumor_assessments_data)} tumor assessments")

# ============================================================================
# ECG RESULTS GENERATION
# ============================================================================

ecg_data = []

for subject in subjects_data:
    subject_id = subject['subject_id']
    
    # ECG at visits 1, 5, 8, 10
    subject_visits = [v for v in visits_data if v['subject_id'] == subject_id and v['visit_completed']]
    ecg_visits = [v for v in subject_visits if v['visit_number'] in [1, 5, 8, 10]]
    
    for visit in ecg_visits:
        ecg_date = datetime.strptime(visit['actual_date'], '%Y-%m-%d')
        
        # Normal ECG parameters
        heart_rate = int(np.random.normal(75, 12))
        pr_interval = int(np.random.normal(160, 20))
        qrs_duration = int(np.random.normal(95, 10))
        qt_interval = int(np.random.normal(400, 30))
        qtc_interval = int(np.random.normal(420, 25))
        qtcf_interval = int(np.random.normal(418, 25))
        
        # 10% with prolonged QTc (safety signal)
        if random.random() < 0.10:
            qtcf_interval = int(np.random.uniform(470, 520))
        
        abnormal = qtcf_interval > 450
        clin_sig = qtcf_interval > 470
        
        interpretation = 'Normal Sinus Rhythm'
        if abnormal:
            interpretation = 'Prolonged QTcF interval'
        
        ecg = {
            'subject_id': subject_id,
            'ecg_date': ecg_date.strftime('%Y-%m-%d'),
            'ecg_time': '11:00:00',
            'heart_rate': heart_rate,
            'pr_interval': pr_interval,
            'qrs_duration': qrs_duration,
            'qt_interval': qt_interval,
            'qtc_interval': qtc_interval,
            'qtcf_interval': qtcf_interval,
            'interpretation': interpretation,
            'abnormal': abnormal,
            'clinically_significant': clin_sig,
            'reader': 'Central ECG Laboratory'
        }
        ecg_data.append(ecg)

print(f"Generated {len(ecg_data)} ECG records")

# ============================================================================
# PROTOCOL DEVIATIONS GENERATION
# ============================================================================

deviations_data = []

# Create specific protocol deviation scenarios
deviation_scenarios = []

# Scenario 1: Visit window violations (already in visits data)
visit_window_violations = [
    v for v in visits_data
    if v['visit_completed'] and v['actual_date'] and v['visit_number'] > 1
]

for visit in visit_window_violations[:15]:  # First 15
    subject_id = visit['subject_id']
    scheduled = datetime.strptime(visit['scheduled_date'], '%Y-%m-%d')
    actual = datetime.strptime(visit['actual_date'], '%Y-%m-%d')
    days_diff = abs((actual - scheduled).days)
    window_upper = abs(visit['window_upper_days'] or 0)
    
    if days_diff > window_upper:
        deviation = {
            'subject_id': subject_id,
            'deviation_type': 'Visit Window Violation',
            'deviation_category': 'Protocol Compliance',
            'description': f"Visit {visit['visit_number']} conducted {days_diff} days outside window",
            'deviation_date': visit['actual_date'],
            'reported_date': (actual + timedelta(days=2)).strftime('%Y-%m-%d'),
            'severity': 'Minor' if days_diff < 7 else 'Major',
            'impact_on_data': False,
            'impact_on_safety': False,
            'corrective_action': 'Site counseled on visit scheduling',
            'preventive_action': 'Enhanced visit reminder system',
            'status': 'Closed',
            'resolution_date': (actual + timedelta(days=7)).strftime('%Y-%m-%d')
        }
        deviations_data.append(deviation)

# Scenario 2: Missed assessments
for i in range(5):
    subject = random.choice(subjects_data)
    deviation_date = datetime.strptime(subject['randomization_date'], '%Y-%m-%d') + timedelta(days=random.randint(30, 100))
    
    deviation = {
        'subject_id': subject['subject_id'],
        'deviation_type': 'Missed Assessment',
        'deviation_category': 'Protocol Compliance',
        'description': 'Required laboratory assessment not performed',
        'deviation_date': deviation_date.strftime('%Y-%m-%d'),
        'reported_date': (deviation_date + timedelta(days=1)).strftime('%Y-%m-%d'),
        'severity': 'Minor',
        'impact_on_data': True,
        'impact_on_safety': False,
        'corrective_action': 'Assessment performed at next visit',
        'preventive_action': 'Site staff training on visit procedures',
        'status': 'Closed',
        'resolution_date': (deviation_date + timedelta(days=21)).strftime('%Y-%m-%d')
    }
    deviations_data.append(deviation)

print(f"Generated {len(deviations_data)} protocol deviations")

# ============================================================================
# QUERIES GENERATION
# ============================================================================

queries_data = []

# Generate queries for various data issues
query_types = [
    ('Missing Data', 'Required field not completed'),
    ('Data Inconsistency', 'Dates not in chronological order'),
    ('Out of Range Value', 'Vital sign value outside expected range'),
    ('AE Clarification', 'Relationship to study drug requires clarification'),
    ('Protocol Deviation', 'Explain reason for protocol deviation'),
]

for i in range(25):
    subject = random.choice(subjects_data)
    subject_id = subject['subject_id']
    query_type, query_text = random.choice(query_types)
    
    query_date = datetime.strptime(subject['randomization_date'], '%Y-%m-%d') + timedelta(days=random.randint(14, 120))
    
    # 70% resolved, 30% open
    if random.random() < 0.70:
        query_status = 'Closed'
        response_date = query_date + timedelta(days=random.randint(1, 10))
        resolution_date = response_date
        response_text = 'Query resolved with site clarification'
    else:
        query_status = 'Open'
        response_date = None
        resolution_date = None
        response_text = None
    
    priority = random.choice(['Low', 'Medium', 'High'])
    
    query = {
        'subject_id': subject_id,
        'query_type': query_type,
        'query_category': 'Data Quality',
        'query_text': query_text,
        'query_date': query_date.strftime('%Y-%m-%d'),
        'query_status': query_status,
        'assigned_to': 'Site Coordinator',
        'priority': priority,
        'response_text': response_text,
        'response_date': response_date.strftime('%Y-%m-%d') if response_date else None,
        'resolution_date': resolution_date.strftime('%Y-%m-%d') if resolution_date else None
    }
    queries_data.append(query)

print(f"Generated {len(queries_data)} queries")

# ============================================================================
# SAVE DATA TO JSON
# ============================================================================

output_data = {
    'adverse_events': adverse_events_data,
    'medical_history': medical_history_data,
    'concomitant_medications': conmed_data,
    'tumor_assessments': tumor_assessments_data,
    'ecg_results': ecg_data,
    'protocol_deviations': deviations_data,
    'queries': queries_data
}

with open('synthetic_data_part3.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("\nData generation complete - Part 3 saved!")
print(f"Adverse Events: {len(adverse_events_data)}")
print(f"Medical History: {len(medical_history_data)}")
print(f"Concomitant Meds: {len(conmed_data)}")
print(f"Tumor Assessments: {len(tumor_assessments_data)}")
print(f"ECG Results: {len(ecg_data)}")
print(f"Protocol Deviations: {len(deviations_data)}")
print(f"Queries: {len(queries_data)}")
