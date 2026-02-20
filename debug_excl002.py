import sqlite3, sys, os
sys.path.insert(0, r"C:\Users\Sandya\Downloads\ProjectsAI\clinical-trial-data-layer")
os.chdir(r"C:\Users\Sandya\Downloads\ProjectsAI\clinical-trial-data-layer")

from rules_engine.tools.clinical_tools import ClinicalTools
tools = ClinicalTools()

subject_id = "101-001"

# 1. What does check_conmeds return with no filter (as called in _build_llm_context)?
print("=== check_conmeds (no filter, ongoing=1 only) ===")
result = tools.check_conmeds(subject_id)
print(f"found: {result['found']}")
print(f"medications count: {len(result['medications'])}")
for m in result['medications']:
    print(f"  {m['medication_name']} {m.get('dose','')} {m.get('dose_unit','')} {m.get('frequency','')} ongoing={m.get('ongoing')} indication={m.get('indication')}")

# 2. What does check_conmeds return when searching for dexamethasone specifically?
print("\n=== check_conmeds (search dexamethasone) ===")
result2 = tools.check_conmeds(subject_id, medication_names=["dexamethasone"])
print(f"found: {result2['found']}")
for m in result2.get('medications', []):
    print(f"  {m}")

# 3. What does check_medical_history return for this subject?
print("\n=== check_medical_history (all conditions) ===")
result3 = tools.check_medical_history(subject_id, [""], status_filter="any")
print(f"found: {result3['found']}")
print(f"evidence: {result3['evidence']}")

# 4. What does get_tumor_assessments return?
print("\n=== get_tumor_assessments ===")
result4 = tools.get_tumor_assessments(subject_id)
for t in result4:
    print(f"  {t.get('assessment_date')} {t.get('overall_response')} new_lesions={t.get('new_lesions')} progression={t.get('progression')}")

# 5. Check the raw DB: what is the ongoing value for dexamethasone for 101-001?
print("\n=== Raw DB check for 101-001 dexamethasone ===")
conn = sqlite3.connect(r"C:\Users\Sandya\Downloads\ProjectsAI\clinical-trial-data-layer\clinical_trial.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT medication_name, dose, indication, ongoing, start_date, end_date FROM concomitant_medications WHERE subject_id=? AND LOWER(medication_name) LIKE '%dex%'", (subject_id,))
rows = cur.fetchall()
for r in rows:
    print(dict(r))
conn.close()

# 6. Check what rules/tools the EXCL-002 rule has
print("\n=== Loading EXCL-002 rule config ===")
import yaml
with open(r"C:\Users\Sandya\Downloads\ProjectsAI\clinical-trial-data-layer\rule_configs\exclusion_criteria.yaml") as f:
    config = yaml.safe_load(f)
for rule in config['exclusion_criteria']:
    if rule['rule_id'] == 'EXCL-002':
        print(f"tools_needed: {rule.get('tools_needed')}")
        print(f"parameters search_terms medications: {rule.get('parameters',{}).get('search_terms',{}).get('medications')}")
