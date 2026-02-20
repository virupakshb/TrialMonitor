#!/usr/bin/env python
"""
Test the Clinical Trial API
"""

import time
import urllib.request
import json
import sys

def test_endpoint(url, description):
    """Test a single endpoint"""
    try:
        response = urllib.request.urlopen(url, timeout=5)
        data = json.loads(response.read())
        print(f"✓ {description}")
        return data
    except Exception as e:
        print(f"✗ {description}: {e}")
        return None

def main():
    base_url = "http://localhost:8000"
    
    print("=" * 70)
    print("🧪 Testing Clinical Trial API")
    print("=" * 70)
    print()
    
    # Test root endpoint
    print("1. Testing root endpoint...")
    data = test_endpoint(base_url, "Root endpoint")
    if data:
        print(f"   Protocol: {data.get('protocol')}")
        print(f"   Sponsor: {data.get('sponsor')}")
        print()
    
    # Test statistics
    print("2. Testing statistics endpoint...")
    stats = test_endpoint(f"{base_url}/api/statistics", "Statistics")
    if stats:
        print(f"   Subjects: {stats.get('subjects', 0):,}")
        print(f"   Visits: {stats.get('visits', 0):,}")
        print(f"   Lab Results: {stats.get('laboratory_results', 0):,}")
        print(f"   Adverse Events: {stats.get('adverse_events', 0):,}")
        print(f"   Serious AEs: {stats.get('serious_adverse_events', 0):,}")
        print()
    
    # Test sites
    print("3. Testing sites endpoint...")
    sites = test_endpoint(f"{base_url}/api/sites", "Sites list")
    if sites:
        print(f"   Found {len(sites)} sites")
        for site in sites[:3]:
            print(f"   - {site['site_name']} ({site['country']})")
        print()
    
    # Test subjects
    print("4. Testing subjects endpoint...")
    subjects = test_endpoint(f"{base_url}/api/subjects?limit=5", "Subjects list")
    if subjects:
        print(f"   Found {len(subjects)} subjects (limited to 5)")
        print()
    
    # Test specific subject
    print("5. Testing specific subject endpoint...")
    subject = test_endpoint(f"{base_url}/api/subjects/101-001", "Subject 101-001")
    if subject:
        print(f"   Subject ID: {subject.get('subject_id')}")
        print(f"   Treatment Arm: {subject.get('treatment_arm_name')}")
        print(f"   Status: {subject.get('study_status')}")
        print()
    
    # Test adverse events
    print("6. Testing adverse events endpoint...")
    aes = test_endpoint(f"{base_url}/api/adverse-events?seriousness=Yes", "Serious AEs")
    if aes:
        print(f"   Found {len(aes)} serious adverse events")
        if len(aes) > 0:
            print(f"   First SAE: {aes[0]['ae_term']} (Grade {aes[0]['ctcae_grade']})")
        print()
    
    # Test protocol deviations
    print("7. Testing protocol deviations endpoint...")
    devs = test_endpoint(f"{base_url}/api/deviations", "Protocol deviations")
    if devs:
        print(f"   Found {len(devs)} protocol deviations")
        print()
    
    # Test queries
    print("8. Testing queries endpoint...")
    queries = test_endpoint(f"{base_url}/api/queries?query_status=Open", "Open queries")
    if queries:
        print(f"   Found {len(queries)} open queries")
        print()
    
    print("=" * 70)
    print("✅ API Testing Complete!")
    print("=" * 70)
    print()
    print("API is ready to use at:", base_url)
    print("Documentation available at:", f"{base_url}/docs")

if __name__ == "__main__":
    main()
