"""
Load synthetic clinical trial data into PostgreSQL database
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os

# Database connection parameters
# You can set these via environment variables or change directly
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'clinical_trial'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def load_json_file(filename):
    """Load JSON data from file"""
    with open(filename, 'r') as f:
        return json.load(f)

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"Database '{DB_CONFIG['database']}' created successfully")
        else:
            print(f"Database '{DB_CONFIG['database']}' already exists")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def execute_schema(conn):
    """Execute schema SQL file"""
    try:
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        cur.close()
        print("Schema created successfully")
    except Exception as e:
        print(f"Error executing schema: {e}")
        conn.rollback()

def insert_data(conn, table_name, data, columns):
    """Insert data into table using execute_values for efficiency"""
    if not data:
        print(f"No data to insert for {table_name}")
        return
    
    try:
        cur = conn.cursor()
        
        # Prepare values
        values = []
        for record in data:
            row = []
            for col in columns:
                val = record.get(col)
                # Convert None to NULL
                if val is None:
                    row.append(None)
                elif isinstance(val, bool):
                    row.append(val)
                elif isinstance(val, (int, float)):
                    row.append(val)
                else:
                    row.append(str(val))
            values.append(tuple(row))
        
        # Build INSERT query
        cols_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
        
        # Execute batch insert
        cur.executemany(query, values)
        conn.commit()
        cur.close()
        
        print(f"Inserted {len(data)} records into {table_name}")
    except Exception as e:
        print(f"Error inserting data into {table_name}: {e}")
        conn.rollback()

def main():
    print("=" * 70)
    print("Clinical Trial Data Loading Script")
    print("Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)")
    print("Sponsor: NexaVance Therapeutics Inc.")
    print("=" * 70)
    
    # Create database if needed
    print("\n1. Creating database (if not exists)...")
    create_database_if_not_exists()
    
    # Connect to database
    print("\n2. Connecting to database...")
    conn = connect_db()
    if not conn:
        print("Failed to connect to database. Exiting.")
        return
    
    # Execute schema
    print("\n3. Creating schema...")
    execute_schema(conn)
    
    # Load JSON data
    print("\n4. Loading JSON data files...")
    part1_data = load_json_file('synthetic_data_part1.json')
    part2_data = load_json_file('synthetic_data_part2.json')
    part3_data = load_json_file('synthetic_data_part3.json')
    
    # Insert protocol info
    print("\n5. Inserting protocol information...")
    insert_data(conn, 'protocol_info', part1_data['protocol_info'], [
        'protocol_number', 'protocol_name', 'short_title', 'sponsor_name',
        'sponsor_address', 'phase', 'indication', 'study_type', 'study_design',
        'therapeutic_area', 'investigational_product', 'primary_objective',
        'primary_endpoint', 'planned_sample_size', 'study_start_date',
        'estimated_completion_date'
    ])
    
    # Insert sites
    print("\n6. Inserting sites...")
    insert_data(conn, 'sites', part1_data['sites'], [
        'site_id', 'site_name', 'country', 'city', 'state_province',
        'principal_investigator', 'site_coordinator', 'contact_email',
        'contact_phone', 'activation_date', 'site_status',
        'planned_enrollment', 'actual_enrollment'
    ])
    
    # Insert subjects
    print("\n7. Inserting subjects...")
    insert_data(conn, 'subjects', part1_data['subjects'], [
        'subject_id', 'site_id', 'screening_number', 'randomization_number',
        'initials', 'treatment_arm', 'treatment_arm_name', 'randomization_date',
        'screening_date', 'consent_date', 'study_status', 'discontinuation_date',
        'discontinuation_reason'
    ])
    
    # Insert demographics
    print("\n8. Inserting demographics...")
    insert_data(conn, 'demographics', part1_data['demographics'], [
        'subject_id', 'date_of_birth', 'age', 'sex', 'race', 'ethnicity',
        'weight_kg', 'height_cm', 'bmi', 'ecog_performance_status',
        'smoking_status', 'smoking_pack_years'
    ])
    
    # Insert visits
    print("\n9. Inserting visits...")
    insert_data(conn, 'visits', part2_data['visits'], [
        'subject_id', 'visit_number', 'visit_name', 'scheduled_date',
        'actual_date', 'visit_status', 'window_lower_days', 'window_upper_days',
        'days_from_randomization', 'visit_type', 'visit_completed',
        'missed_visit', 'visit_notes'
    ])
    
    # Insert vital signs
    print("\n10. Inserting vital signs...")
    insert_data(conn, 'vital_signs', part2_data['vital_signs'], [
        'subject_id', 'assessment_date', 'assessment_time', 'systolic_bp',
        'diastolic_bp', 'heart_rate', 'temperature_celsius', 'respiratory_rate',
        'weight_kg', 'oxygen_saturation', 'position', 'notes'
    ])
    
    # Insert laboratory results
    print("\n11. Inserting laboratory results...")
    insert_data(conn, 'laboratory_results', part2_data['laboratory_results'], [
        'subject_id', 'collection_date', 'collection_time', 'lab_category',
        'test_name', 'test_value', 'test_unit', 'normal_range_lower',
        'normal_range_upper', 'abnormal_flag', 'clinically_significant',
        'lab_comments'
    ])
    
    # Insert adverse events
    print("\n12. Inserting adverse events...")
    insert_data(conn, 'adverse_events', part3_data['adverse_events'], [
        'subject_id', 'ae_term', 'meddra_code', 'meddra_preferred_term',
        'onset_date', 'resolution_date', 'ongoing', 'severity', 'ctcae_grade',
        'seriousness', 'serious_criteria', 'relationship_to_study_drug',
        'action_taken', 'outcome', 'ae_description', 'reporter'
    ])
    
    # Insert medical history
    print("\n13. Inserting medical history...")
    insert_data(conn, 'medical_history', part3_data['medical_history'], [
        'subject_id', 'condition', 'meddra_code', 'diagnosis_date',
        'ongoing', 'resolution_date', 'condition_category', 'condition_notes'
    ])
    
    # Insert concomitant medications
    print("\n14. Inserting concomitant medications...")
    insert_data(conn, 'concomitant_medications', part3_data['concomitant_medications'], [
        'subject_id', 'medication_name', 'who_drug_code', 'indication',
        'dose', 'dose_unit', 'frequency', 'route', 'start_date',
        'end_date', 'ongoing', 'medication_class'
    ])
    
    # Insert tumor assessments
    print("\n15. Inserting tumor assessments...")
    insert_data(conn, 'tumor_assessments', part3_data['tumor_assessments'], [
        'subject_id', 'assessment_date', 'assessment_method',
        'overall_response', 'target_lesion_sum', 'new_lesions',
        'progression', 'assessment_notes', 'radiologist'
    ])
    
    # Insert ECG results
    print("\n16. Inserting ECG results...")
    insert_data(conn, 'ecg_results', part3_data['ecg_results'], [
        'subject_id', 'ecg_date', 'ecg_time', 'heart_rate', 'pr_interval',
        'qrs_duration', 'qt_interval', 'qtc_interval', 'qtcf_interval',
        'interpretation', 'abnormal', 'clinically_significant', 'reader'
    ])
    
    # Insert protocol deviations
    print("\n17. Inserting protocol deviations...")
    insert_data(conn, 'protocol_deviations', part3_data['protocol_deviations'], [
        'subject_id', 'deviation_type', 'deviation_category', 'description',
        'deviation_date', 'reported_date', 'severity', 'impact_on_data',
        'impact_on_safety', 'corrective_action', 'preventive_action',
        'status', 'resolution_date'
    ])
    
    # Insert queries
    print("\n18. Inserting queries...")
    insert_data(conn, 'queries', part3_data['queries'], [
        'subject_id', 'query_type', 'query_category', 'query_text',
        'query_date', 'query_status', 'assigned_to', 'priority',
        'response_text', 'response_date', 'resolution_date'
    ])
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 70)
    print("DATA LOADING COMPLETE!")
    print("=" * 70)
    print("\nDatabase Statistics:")
    
    # Reconnect to get counts
    conn = connect_db()
    cur = conn.cursor()
    
    tables = [
        'sites', 'subjects', 'demographics', 'visits', 'vital_signs',
        'laboratory_results', 'adverse_events', 'medical_history',
        'concomitant_medications', 'tumor_assessments', 'ecg_results',
        'protocol_deviations', 'queries'
    ]
    
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table:30s}: {count:6d} records")
    
    cur.close()
    conn.close()
    
    print("\nDatabase ready for AI agent testing!")

if __name__ == '__main__':
    main()
