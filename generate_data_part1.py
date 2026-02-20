"""
Clinical Trial Synthetic Data Generator
Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
Sponsor: NexaVance Therapeutics Inc.

Generates realistic synthetic data for 100 subjects across 5 sites
with rich scenarios for testing AI monitoring agents.
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np
from scipy import stats

# Set random seed for reproducibility
random.seed(1218)
np.random.seed(1218)
fake = Faker()
Faker.seed(1218)

# Load protocol definition
with open('protocol_definition.json', 'r') as f:
    protocol_data = json.load(f)
    protocol = protocol_data['protocol']

# ============================================================================
# CONFIGURATION
# ============================================================================

NUM_SUBJECTS = 100
NUM_SITES = 5
STUDY_START_DATE = datetime(2024, 3, 15)

# Site distribution: 25, 22, 20, 18, 15
SITE_ENROLLMENTS = [25, 22, 20, 18, 15]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def random_date(start_date, end_date):
    """Generate random date between start and end"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def add_jitter(value, pct=0.1):
    """Add random jitter to a value"""
    jitter = value * pct * random.uniform(-1, 1)
    return value + jitter

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI"""
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)

def generate_abnormal_flag(value, lower, upper):
    """Generate abnormal flag based on normal range"""
    if value < lower:
        return 'Low'
    elif value > upper:
        return 'High'
    else:
        return 'Normal'

# ============================================================================
# GENERATE PROTOCOL INFO
# ============================================================================

protocol_info = {
    'protocol_number': protocol['protocol_number'],
    'protocol_name': protocol['protocol_name'],
    'short_title': protocol['short_title'],
    'sponsor_name': protocol['sponsor']['name'],
    'sponsor_address': protocol['sponsor']['address'],
    'phase': protocol['phase'],
    'indication': protocol['indication'],
    'study_type': protocol['study_type'],
    'study_design': protocol['design'],
    'therapeutic_area': protocol['therapeutic_area'],
    'investigational_product': protocol['study_drug']['investigational_product'],
    'primary_objective': protocol['objectives']['primary'],
    'primary_endpoint': protocol['endpoints']['primary'],
    'planned_sample_size': protocol['sample_size']['planned_total'],
    'study_start_date': protocol['sample_size']['study_start_date'],
    'estimated_completion_date': protocol['sample_size']['estimated_completion_date']
}

# ============================================================================
# GENERATE SITES
# ============================================================================

sites_data = [
    {
        'site_id': '101',
        'site_name': 'Memorial Cancer Center',
        'country': 'United States',
        'city': 'Boston',
        'state_province': 'Massachusetts',
        'principal_investigator': 'Dr. Emily Chen',
        'site_coordinator': 'Jessica Martinez',
        'contact_email': 'trials@memorialcancer.org',
        'contact_phone': '+1-617-555-0101',
        'activation_date': '2024-03-15',
        'site_status': 'Active',
        'planned_enrollment': 30,
        'actual_enrollment': 25
    },
    {
        'site_id': '102',
        'site_name': 'London Oncology Institute',
        'country': 'United Kingdom',
        'city': 'London',
        'state_province': 'England',
        'principal_investigator': 'Dr. James Harrison',
        'site_coordinator': 'Sophie Williams',
        'contact_email': 'research@londononcology.nhs.uk',
        'contact_phone': '+44-20-7946-0102',
        'activation_date': '2024-04-01',
        'site_status': 'Active',
        'planned_enrollment': 25,
        'actual_enrollment': 22
    },
    {
        'site_id': '103',
        'site_name': 'Toronto Research Hospital',
        'country': 'Canada',
        'city': 'Toronto',
        'state_province': 'Ontario',
        'principal_investigator': 'Dr. Priya Sharma',
        'site_coordinator': 'Michael Wong',
        'contact_email': 'clinical.trials@torontoresearch.ca',
        'contact_phone': '+1-416-555-0103',
        'activation_date': '2024-04-10',
        'site_status': 'Active',
        'planned_enrollment': 25,
        'actual_enrollment': 20
    },
    {
        'site_id': '104',
        'site_name': 'Sydney Cancer Center',
        'country': 'Australia',
        'city': 'Sydney',
        'state_province': 'New South Wales',
        'principal_investigator': 'Dr. David O\'Connor',
        'site_coordinator': 'Emma Thompson',
        'contact_email': 'trials@sydneycancer.org.au',
        'contact_phone': '+61-2-9555-0104',
        'activation_date': '2024-04-20',
        'site_status': 'Active',
        'planned_enrollment': 20,
        'actual_enrollment': 18
    },
    {
        'site_id': '105',
        'site_name': 'Singapore Medical Research',
        'country': 'Singapore',
        'city': 'Singapore',
        'state_province': 'Singapore',
        'principal_investigator': 'Dr. Wei Zhang',
        'site_coordinator': 'Lisa Tan',
        'contact_email': 'clinicaltrials@sgmedresearch.sg',
        'contact_phone': '+65-6555-0105',
        'activation_date': '2024-05-01',
        'site_status': 'Active',
        'planned_enrollment': 20,
        'actual_enrollment': 15
    }
]

# ============================================================================
# GENERATE SUBJECTS
# ============================================================================

subjects_data = []
demographics_data = []
subject_counter = 1

for site_idx, site in enumerate(sites_data):
    site_id = site['site_id']
    num_subjects_for_site = SITE_ENROLLMENTS[site_idx]
    
    for i in range(num_subjects_for_site):
        subject_num = f"{subject_counter:03d}"
        subject_id = f"{site_id}-{subject_num}"
        
        # Randomize treatment arm (1:1 ratio)
        treatment_arm = 1 if subject_counter % 2 == 1 else 2
        treatment_arm_name = protocol['treatment_arms'][treatment_arm - 1]['name']
        
        # Generate enrollment dates (staggered over 6 months)
        screening_date = STUDY_START_DATE + timedelta(days=random.randint(0, 180))
        consent_date = screening_date
        randomization_date = screening_date + timedelta(days=random.randint(3, 14))
        
        # Determine study status (90% ongoing, 5% completed, 5% discontinued)
        status_rand = random.random()
        if status_rand < 0.90:
            study_status = 'Enrolled'
            discontinuation_date = None
            discontinuation_reason = None
        elif status_rand < 0.95:
            study_status = 'Completed'
            discontinuation_date = randomization_date + timedelta(days=196)
            discontinuation_reason = 'Study Completed'
        else:
            study_status = 'Discontinued'
            disc_day = random.randint(30, 150)
            discontinuation_date = randomization_date + timedelta(days=disc_day)
            discontinuation_reason = random.choice([
                'Adverse Event',
                'Disease Progression',
                'Withdrawal of Consent',
                'Lost to Follow-up'
            ])
        
        subject = {
            'subject_id': subject_id,
            'site_id': site_id,
            'screening_number': f"SCR-{subject_num}",
            'randomization_number': f"RAND-{subject_num}",
            'initials': f"{fake.first_name()[0]}{fake.last_name()[0]}",
            'treatment_arm': treatment_arm,
            'treatment_arm_name': treatment_arm_name,
            'randomization_date': randomization_date.strftime('%Y-%m-%d'),
            'screening_date': screening_date.strftime('%Y-%m-%d'),
            'consent_date': consent_date.strftime('%Y-%m-%d'),
            'study_status': study_status,
            'discontinuation_date': discontinuation_date.strftime('%Y-%m-%d') if discontinuation_date else None,
            'discontinuation_reason': discontinuation_reason
        }
        subjects_data.append(subject)
        
        # Generate demographics
        sex = random.choice(['Male', 'Female'])
        age = int(np.random.normal(65, 10))  # Mean age 65, SD 10
        age = max(45, min(age, 85))  # Clamp between 45-85
        
        # Date of birth based on age
        dob = screening_date - timedelta(days=age * 365)
        
        race = random.choices(
            ['White', 'Black or African American', 'Asian', 'Other'],
            weights=[0.60, 0.15, 0.20, 0.05]
        )[0]
        
        ethnicity = random.choices(
            ['Not Hispanic or Latino', 'Hispanic or Latino'],
            weights=[0.85, 0.15]
        )[0]
        
        # Weight and height with realistic distributions
        if sex == 'Male':
            weight_kg = np.random.normal(80, 12)
            height_cm = np.random.normal(175, 8)
        else:
            weight_kg = np.random.normal(68, 10)
            height_cm = np.random.normal(163, 7)
        
        weight_kg = round(max(50, min(weight_kg, 120)), 2)
        height_cm = round(max(150, min(height_cm, 195)), 2)
        bmi = calculate_bmi(weight_kg, height_cm)
        
        ecog = random.choices([0, 1], weights=[0.60, 0.40])[0]
        
        smoking_status = random.choices(
            ['Current', 'Former', 'Never'],
            weights=[0.20, 0.65, 0.15]
        )[0]
        
        if smoking_status == 'Never':
            pack_years = 0
        elif smoking_status == 'Current':
            pack_years = round(random.uniform(10, 60), 1)
        else:  # Former
            pack_years = round(random.uniform(5, 50), 1)
        
        demographics = {
            'subject_id': subject_id,
            'date_of_birth': dob.strftime('%Y-%m-%d'),
            'age': age,
            'sex': sex,
            'race': race,
            'ethnicity': ethnicity,
            'weight_kg': weight_kg,
            'height_cm': height_cm,
            'bmi': bmi,
            'ecog_performance_status': ecog,
            'smoking_status': smoking_status,
            'smoking_pack_years': pack_years
        }
        demographics_data.append(demographics)
        
        subject_counter += 1

print(f"Generated {len(subjects_data)} subjects across {len(sites_data)} sites")

# ============================================================================
# SAVE DATA TO JSON
# ============================================================================

output_data = {
    'protocol_info': [protocol_info],
    'sites': sites_data,
    'subjects': subjects_data,
    'demographics': demographics_data
}

with open('synthetic_data_part1.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("Data generation complete - Part 1 saved!")
print(f"Protocol: {protocol_info['protocol_number']}")
print(f"Sponsor: {protocol_info['sponsor_name']}")
print(f"Sites: {len(sites_data)}")
print(f"Subjects: {len(subjects_data)}")
