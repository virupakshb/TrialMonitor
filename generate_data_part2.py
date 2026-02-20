"""
Clinical Trial Synthetic Data Generator - Part 2
Generates: Visits, Vital Signs, Laboratory Results

This script depends on synthetic_data_part1.json
"""

import json
import random
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

# Set random seed for reproducibility
random.seed(1218)
np.random.seed(1218)

# Load protocol and part 1 data
with open('protocol_definition.json', 'r') as f:
    protocol_data = json.load(f)
    protocol = protocol_data['protocol']

with open('synthetic_data_part1.json', 'r') as f:
    part1_data = json.load(f)
    subjects_data = part1_data['subjects']
    demographics_data = part1_data['demographics']

# ============================================================================
# VISIT GENERATION
# ============================================================================

visits_data = []
visit_schedule = protocol['visit_schedule']

for subject in subjects_data:
    subject_id = subject['subject_id']
    randomization_date = datetime.strptime(subject['randomization_date'], '%Y-%m-%d')
    study_status = subject['study_status']
    
    # Determine which visits to generate based on status
    if study_status == 'Completed':
        visits_to_generate = len(visit_schedule)  # All visits
    elif study_status == 'Discontinued':
        # Random number of visits (3-8)
        visits_to_generate = random.randint(3, 8)
    else:  # Enrolled/Ongoing
        # Random ongoing point (5-10 visits completed)
        visits_to_generate = random.randint(5, 10)
    
    for visit_idx, visit_def in enumerate(visit_schedule[:visits_to_generate]):
        visit_number = visit_def['visit_number']
        visit_name = visit_def['visit_name']
        
        # Calculate scheduled and actual dates
        if visit_number == 1:  # Screening
            scheduled_date = randomization_date + timedelta(days=visit_def['day'])
            # 95% came on time, 5% protocol deviation
            if random.random() < 0.95:
                actual_date = scheduled_date + timedelta(days=random.randint(-3, 3))
            else:
                # Protocol deviation: came outside window
                actual_date = scheduled_date + timedelta(days=random.choice([-15, -10, 10, 15]))
        else:
            scheduled_date = randomization_date + timedelta(days=visit_def['day'])
            window_lower = visit_def.get('window_lower', 0)
            window_upper = visit_def.get('window_upper', 0)
            
            # 90% within window, 10% outside (protocol deviation scenario)
            if random.random() < 0.90:
                actual_date = scheduled_date + timedelta(
                    days=random.randint(window_lower, window_upper)
                )
            else:
                # Outside window for AI agent to catch
                deviation_days = random.choice([-10, -7, -5, 5, 7, 10, 12, 15])
                actual_date = scheduled_date + timedelta(days=deviation_days)
        
        # 98% of visits completed, 2% missed
        if random.random() < 0.98:
            visit_completed = True
            visit_status = 'Completed'
            missed_visit = False
        else:
            visit_completed = False
            visit_status = 'Missed'
            missed_visit = True
            actual_date = None
        
        days_from_rand = (actual_date - randomization_date).days if actual_date else None
        
        visit = {
            'subject_id': subject_id,
            'visit_number': visit_number,
            'visit_name': visit_name,
            'scheduled_date': scheduled_date.strftime('%Y-%m-%d'),
            'actual_date': actual_date.strftime('%Y-%m-%d') if actual_date else None,
            'visit_status': visit_status,
            'window_lower_days': visit_def.get('window_lower'),
            'window_upper_days': visit_def.get('window_upper'),
            'days_from_randomization': days_from_rand,
            'visit_type': 'Scheduled',
            'visit_completed': visit_completed,
            'missed_visit': missed_visit,
            'visit_notes': None
        }
        visits_data.append(visit)

print(f"Generated {len(visits_data)} visits")

# ============================================================================
# VITAL SIGNS GENERATION
# ============================================================================

vitals_data = []

for visit in visits_data:
    if not visit['visit_completed']:
        continue
    
    subject_id = visit['subject_id']
    actual_date = datetime.strptime(visit['actual_date'], '%Y-%m-%d')
    
    # Get subject demographics for baseline
    demo = next(d for d in demographics_data if d['subject_id'] == subject_id)
    weight_baseline = demo['weight_kg']
    
    # Simulate weight change over time (cancer patients may lose weight)
    visit_num = visit['visit_number']
    if visit_num == 1:  # Screening
        weight_change = 0
    else:
        # Gradual weight loss for some patients
        if random.random() < 0.30:  # 30% lose weight
            weight_change = -0.5 * (visit_num - 1) + np.random.normal(0, 1)
        else:
            weight_change = np.random.normal(0, 1.5)
    
    weight_kg = round(max(45, weight_baseline + weight_change), 2)
    
    # Blood pressure (normal range with some variations)
    systolic_bp = int(np.random.normal(125, 15))
    diastolic_bp = int(np.random.normal(80, 10))
    
    # Some patients with hypertension (10%)
    if random.random() < 0.10:
        systolic_bp += random.randint(20, 40)
        diastolic_bp += random.randint(10, 20)
    
    systolic_bp = max(90, min(systolic_bp, 180))
    diastolic_bp = max(60, min(diastolic_bp, 110))
    
    # Heart rate
    heart_rate = int(np.random.normal(75, 12))
    heart_rate = max(55, min(heart_rate, 120))
    
    # Temperature (mostly normal with occasional fever)
    if random.random() < 0.95:
        temperature = round(np.random.normal(36.8, 0.3), 2)
    else:
        # Fever (infection or adverse event)
        temperature = round(np.random.uniform(37.5, 38.5), 2)
    
    temperature = round(max(36.0, min(temperature, 39.5)), 2)
    
    # Respiratory rate
    resp_rate = int(np.random.normal(16, 3))
    resp_rate = max(12, min(resp_rate, 24))
    
    # Oxygen saturation
    o2_sat = int(np.random.normal(97, 2))
    # Some patients with lower O2 due to lung cancer
    if random.random() < 0.15:
        o2_sat = int(np.random.normal(92, 3))
    o2_sat = max(88, min(o2_sat, 100))
    
    vitals = {
        'subject_id': subject_id,
        'assessment_date': actual_date.strftime('%Y-%m-%d'),
        'assessment_time': '10:30:00',
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'heart_rate': heart_rate,
        'temperature_celsius': temperature,
        'respiratory_rate': resp_rate,
        'weight_kg': weight_kg,
        'oxygen_saturation': o2_sat,
        'position': 'Sitting',
        'notes': None
    }
    vitals_data.append(vitals)

print(f"Generated {len(vitals_data)} vital signs records")

# ============================================================================
# LABORATORY RESULTS GENERATION
# ============================================================================

labs_data = []

# Lab test definitions with normal ranges
lab_tests = {
    'Hematology': [
        ('WBC', 4.5, 11.0, '10^9/L'),
        ('RBC', 4.0, 5.5, '10^12/L'),
        ('Hemoglobin', 12.0, 16.0, 'g/dL'),
        ('Hematocrit', 36.0, 48.0, '%'),
        ('Platelets', 150, 400, '10^9/L'),
        ('Neutrophils', 2.0, 7.5, '10^9/L'),
        ('Lymphocytes', 1.0, 4.0, '10^9/L'),
    ],
    'Chemistry': [
        ('ALT', 7, 56, 'U/L'),
        ('AST', 10, 40, 'U/L'),
        ('Total Bilirubin', 0.3, 1.2, 'mg/dL'),
        ('Creatinine', 0.6, 1.2, 'mg/dL'),
        ('BUN', 7, 20, 'mg/dL'),
        ('Glucose', 70, 100, 'mg/dL'),
        ('Albumin', 3.5, 5.0, 'g/dL'),
        ('Alkaline Phosphatase', 30, 120, 'U/L'),
    ],
    'Coagulation': [
        ('PT', 11.0, 13.5, 'seconds'),
        ('PTT', 25, 35, 'seconds'),
        ('INR', 0.9, 1.1, 'ratio'),
    ]
}

for visit in visits_data:
    if not visit['visit_completed']:
        continue
    
    # Labs collected at most visits
    if visit['visit_number'] == 1 or visit['visit_number'] >= 2:
        subject_id = visit['subject_id']
        collection_date = datetime.strptime(visit['actual_date'], '%Y-%m-%d')
        visit_num = visit['visit_number']
        
        # Generate all lab tests
        for lab_category, tests in lab_tests.items():
            for test_name, normal_lower, normal_upper, unit in tests:
                
                # Most values normal, some abnormal
                if random.random() < 0.80:
                    # Normal range
                    test_value = np.random.uniform(normal_lower, normal_upper)
                else:
                    # Abnormal value
                    if random.random() < 0.50:
                        # Low
                        test_value = np.random.uniform(normal_lower * 0.6, normal_lower * 0.95)
                    else:
                        # High
                        test_value = np.random.uniform(normal_upper * 1.05, normal_upper * 1.5)
                
                # Specific scenarios for AI agents to detect
                # Scenario 1: Hepatotoxicity (elevated liver enzymes)
                if random.random() < 0.05 and test_name in ['ALT', 'AST']:
                    test_value = np.random.uniform(normal_upper * 3, normal_upper * 8)
                
                # Scenario 2: Bone marrow suppression (low counts)
                if random.random() < 0.08 and test_name in ['WBC', 'Neutrophils', 'Platelets']:
                    test_value = np.random.uniform(normal_lower * 0.3, normal_lower * 0.7)
                
                # Scenario 3: Anemia worsening over time
                if visit_num > 5 and test_name == 'Hemoglobin':
                    if random.random() < 0.15:
                        test_value = np.random.uniform(8.0, 10.0)
                
                test_value = round(test_value, 2)
                
                abnormal_flag = 'Normal'
                if test_value < normal_lower:
                    abnormal_flag = 'Low'
                elif test_value > normal_upper:
                    abnormal_flag = 'High'
                
                # Clinically significant if very abnormal
                clin_sig = False
                if test_name in ['ALT', 'AST'] and test_value > normal_upper * 3:
                    clin_sig = True
                elif test_name in ['WBC', 'Neutrophils'] and test_value < normal_lower * 0.5:
                    clin_sig = True
                elif test_name == 'Platelets' and test_value < 50:
                    clin_sig = True
                
                lab = {
                    'subject_id': subject_id,
                    'collection_date': collection_date.strftime('%Y-%m-%d'),
                    'collection_time': '08:00:00',
                    'lab_category': lab_category,
                    'test_name': test_name,
                    'test_value': test_value,
                    'test_unit': unit,
                    'normal_range_lower': normal_lower,
                    'normal_range_upper': normal_upper,
                    'abnormal_flag': abnormal_flag,
                    'clinically_significant': clin_sig,
                    'lab_comments': 'Grade 3 toxicity - notify investigator' if clin_sig else None
                }
                labs_data.append(lab)

print(f"Generated {len(labs_data)} laboratory results")

# ============================================================================
# SAVE DATA TO JSON
# ============================================================================

output_data = {
    'visits': visits_data,
    'vital_signs': vitals_data,
    'laboratory_results': labs_data
}

with open('synthetic_data_part2.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("Data generation complete - Part 2 saved!")
print(f"Visits: {len(visits_data)}")
print(f"Vital Signs: {len(vitals_data)}")
print(f"Lab Results: {len(labs_data)}")
