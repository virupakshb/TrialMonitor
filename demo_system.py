#!/usr/bin/env python3
"""
Clinical Trial Rules Engine - Interactive Demo
Showcases all features with real examples
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8001"

def print_header(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_success(msg):
    """Print success message"""
    print(f"✅ {msg}")

def print_info(msg):
    """Print info message"""
    print(f"ℹ️  {msg}")

def print_result(data):
    """Print formatted result"""
    print(json.dumps(data, indent=2))

def demo_1_system_overview():
    """Demo: System Overview"""
    print_header("DEMO 1: System Overview")
    
    print_info("Checking API status...")
    response = requests.get(f"{API_BASE}/")
    if response.status_code == 200:
        data = response.json()
        print_success("API is running!")
        print(f"   API Version: {data.get('version')}")
        print(f"   Total Rules: {data.get('total_rules')}")
        print(f"   Endpoints available: {len(data.get('endpoints', {}))}")
    
    print("\n" + "-" * 80)
    print_info("Getting system summary...")
    response = requests.get(f"{API_BASE}/api/evaluate/summary")
    if response.status_code == 200:
        data = response.json()
        print_result(data)

def demo_2_view_rules():
    """Demo: View Rules"""
    print_header("DEMO 2: View Configured Rules")
    
    print_info("Fetching all rules...")
    response = requests.get(f"{API_BASE}/api/rules")
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Found {data['total']} rules\n")
        
        for rule in data['rules']:
            severity_emoji = {
                'critical': '🔴',
                'major': '🟡',
                'minor': '🟢'
            }.get(rule['severity'], '⚪')
            
            status_emoji = '✅' if rule['status'] == 'active' else '⏸️'
            
            print(f"{severity_emoji} {status_emoji} {rule['rule_id']}: {rule['name']}")
            print(f"   Category: {rule['category']} | Complexity: {rule['complexity']}")
            print(f"   Type: {rule['evaluation_type']}")
            print(f"   Description: {rule['description']}")
            print()

def demo_3_rule_details():
    """Demo: Get Detailed Rule Information"""
    print_header("DEMO 3: Rule Details - EXCL-001")
    
    print_info("Fetching detailed information for EXCL-001...")
    response = requests.get(f"{API_BASE}/api/rules/EXCL-001")
    
    if response.status_code == 200:
        rule = response.json()
        print_success("Rule loaded successfully\n")
        
        print(f"📋 Rule ID: {rule['rule_id']}")
        print(f"📝 Name: {rule['name']}")
        print(f"📖 Description: {rule['description']}")
        print(f"🏷️  Category: {rule['category']}")
        print(f"⚙️  Complexity: {rule['complexity']}")
        print(f"🔧 Evaluation Type: {rule['evaluation_type']}")
        print(f"📄 Template: {rule['template_name']}")
        print(f"⚠️  Severity: {rule['severity']}")
        print(f"📚 Protocol Reference: {rule['protocol_reference']}")
        
        print("\n🔍 Applicable Phases:")
        print_result(rule.get('applicable_phases', {}))
        
        print("\n🛠️  Tools Needed:")
        for tool in rule.get('tools_needed', []):
            print(f"   • {tool}")

def demo_4_execute_single_rule():
    """Demo: Execute Single Rule"""
    print_header("DEMO 4: Execute Single Rule for Subject")
    
    subject_id = "101-001"
    rule_id = "EXCL-001"
    
    print_info(f"Executing rule {rule_id} for subject {subject_id}...")
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE}/api/rules/execute",
        params={"rule_id": rule_id, "subject_id": subject_id}
    )
    execution_time = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        result = response.json()
        print_success(f"Rule executed in {execution_time:.0f}ms\n")
        
        print(f"📊 Result:")
        print(f"   Rule: {result['rule_id']}")
        print(f"   Subject: {result['subject_id']}")
        print(f"   Passed: {'✅ Yes' if result['passed'] else '❌ No'}")
        print(f"   Violated: {'🚨 Yes' if result['violated'] else '✅ No'}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Method: {result['evaluation_method']}")
        
        if result.get('evidence'):
            print(f"\n   Evidence:")
            for evidence in result['evidence']:
                print(f"      • {evidence}")
        
        if result.get('reasoning'):
            print(f"\n   Reasoning:")
            print(f"      {result['reasoning']}")
        
        if result.get('recommendation'):
            print(f"\n   Recommendation:")
            print(f"      {result['recommendation']}")

def demo_5_evaluate_subject():
    """Demo: Evaluate All Rules for Subject"""
    print_header("DEMO 5: Evaluate All Rules for Subject")
    
    subject_id = "101-001"
    
    print_info(f"Evaluating all exclusion rules for subject {subject_id}...")
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE}/api/evaluate/subject/{subject_id}",
        params={"categories": ["exclusion"]}
    )
    execution_time = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        results = response.json()
        print_success(f"Evaluation completed in {execution_time:.0f}ms\n")
        
        print(f"📊 Summary:")
        print(f"   Subject: {results['subject_id']}")
        print(f"   Rules Executed: {results['total_rules_executed']}")
        print(f"   Violations Found: {results['violations_found']}")
        
        if results['violations_found'] > 0:
            print(f"\n🚨 VIOLATIONS DETECTED:")
            for violation in results['violations']:
                print(f"\n   Rule: {violation['rule_id']}")
                print(f"   Severity: {violation['severity']}")
                print(f"   Type: {violation['violation_type']}")
                print(f"   Description: {violation['violation_description']}")
                
                if violation.get('evidence'):
                    print(f"   Evidence:")
                    for evidence in violation['evidence']:
                        print(f"      • {evidence}")
        else:
            print(f"\n✅ No violations found - Subject is compliant!")

def demo_6_test_multiple_subjects():
    """Demo: Test Multiple Subjects"""
    print_header("DEMO 6: Batch Evaluation - Multiple Subjects")
    
    subjects = ["101-001", "101-002", "101-003"]
    
    print_info(f"Testing {len(subjects)} subjects...")
    print()
    
    results_summary = []
    
    for subject_id in subjects:
        response = requests.post(
            f"{API_BASE}/api/evaluate/subject/{subject_id}",
            params={"categories": ["exclusion"]}
        )
        
        if response.status_code == 200:
            result = response.json()
            violation_count = result['violations_found']
            
            status_emoji = "✅" if violation_count == 0 else "🚨"
            print(f"{status_emoji} Subject {subject_id}: {violation_count} violations")
            
            results_summary.append({
                "subject_id": subject_id,
                "violations": violation_count
            })
    
    print(f"\n📊 Batch Summary:")
    total_violations = sum(r['violations'] for r in results_summary)
    subjects_with_violations = sum(1 for r in results_summary if r['violations'] > 0)
    
    print(f"   Total Subjects: {len(subjects)}")
    print(f"   Subjects with Violations: {subjects_with_violations}")
    print(f"   Total Violations: {total_violations}")

def demo_7_mock_vs_llm():
    """Demo: Mock vs LLM Mode"""
    print_header("DEMO 7: Evaluation Modes")
    
    print_info("This system supports two modes:\n")
    
    print("1️⃣  MOCK MODE (Current):")
    print("   • Uses deterministic tools for evidence gathering")
    print("   • Fast execution (~50-100ms per rule)")
    print("   • No API key required")
    print("   • Suitable for testing and development")
    print("   • Decision logic simplified but functional")
    
    print("\n2️⃣  LLM MODE (With Claude API Key):")
    print("   • Full Claude API integration")
    print("   • Complex medical reasoning")
    print("   • Natural language understanding")
    print("   • Tool calling with Claude")
    print("   • Higher accuracy for ambiguous cases")
    print("   • ~1-3 seconds per rule")
    
    print("\n🔑 To enable LLM mode:")
    print("   export ANTHROPIC_API_KEY='your-api-key'")
    print("   python api/rules_api.py")

def main():
    """Run full demo"""
    print("\n" + "=" * 80)
    print("  🏥 CLINICAL TRIAL RULES ENGINE - INTERACTIVE DEMO")
    print("=" * 80)
    print("\nThis demo showcases all features of the Rules Engine")
    print("Make sure the API is running at http://localhost:8001")
    
    input("\nPress Enter to start the demo...")
    
    try:
        # Check API is running
        response = requests.get(f"{API_BASE}/", timeout=2)
        if response.status_code != 200:
            print("\n❌ Error: API is not responding at http://localhost:8001")
            print("   Please start the API first: python api/rules_api.py")
            return
    except requests.exceptions.RequestException:
        print("\n❌ Error: Cannot connect to API at http://localhost:8001")
        print("   Please start the API first: python api/rules_api.py")
        return
    
    # Run all demos
    demos = [
        demo_1_system_overview,
        demo_2_view_rules,
        demo_3_rule_details,
        demo_4_execute_single_rule,
        demo_5_evaluate_subject,
        demo_6_test_multiple_subjects,
        demo_7_mock_vs_llm
    ]
    
    for i, demo_func in enumerate(demos, 1):
        demo_func()
        
        if i < len(demos):
            input(f"\n{'─' * 80}\nPress Enter to continue to next demo...")
    
    # Final summary
    print_header("DEMO COMPLETE!")
    print("🎉 You've seen all major features of the Rules Engine:\n")
    print("   ✅ System Overview & Status")
    print("   ✅ Rule Library & Configuration")
    print("   ✅ Single Rule Execution")
    print("   ✅ Full Subject Evaluation")
    print("   ✅ Batch Processing")
    print("   ✅ Violation Detection & Reporting")
    print("   ✅ Mock vs LLM Modes")
    
    print("\n📚 Next Steps:")
    print("   1. Explore the React UI at http://localhost:3000")
    print("   2. Add your Claude API key for full LLM mode")
    print("   3. Configure additional rules in YAML")
    print("   4. Deploy to production!")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
