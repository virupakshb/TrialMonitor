"""
FastAPI endpoints for Rules Engine
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rules_engine.core.executor import RuleExecutor
from rules_engine.models.rule import VisitContext

app = FastAPI(title="Clinical Trial Rules Engine API")

# Initialize executor
executor = RuleExecutor()

@app.get("/")
def root():
    """API information"""
    return {
        "api": "Clinical Trial Rules Engine",
        "version": "1.0.0",
        "total_rules": len(executor.rules),
        "endpoints": {
            "rules": "/api/rules",
            "execute": "/api/rules/execute",
            "subject_evaluation": "/api/evaluate/subject/{subject_id}"
        }
    }

@app.get("/api/rules")
def get_all_rules(category: Optional[str] = None, status: Optional[str] = None):
    """Get all configured rules"""
    rules = []
    
    for rule_id, rule in executor.rules.items():
        if category and rule.category.value != category:
            continue
        if status and rule.status != status:
            continue
        
        rules.append({
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "category": rule.category.value,
            "complexity": rule.complexity.value,
            "evaluation_type": rule.evaluation_type.value,
            "severity": rule.severity.value,
            "status": rule.status,
            "protocol_reference": rule.protocol_reference
        })
    
    return {
        "total": len(rules),
        "rules": rules
    }

@app.get("/api/rules/{rule_id}")
def get_rule(rule_id: str):
    """Get specific rule details"""
    rule = executor.rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "description": rule.description,
        "category": rule.category.value,
        "complexity": rule.complexity.value,
        "evaluation_type": rule.evaluation_type.value,
        "template_name": rule.template_name,
        "severity": rule.severity.value,
        "status": rule.status,
        "protocol_reference": rule.protocol_reference,
        "applicable_phases": rule.applicable_phases,
        "tools_needed": rule.tools_needed,
        "domain_knowledge": rule.domain_knowledge
    }

@app.post("/api/rules/execute")
def execute_rule(rule_id: str, subject_id: str):
    """Execute a single rule for a subject"""
    if rule_id not in executor.rules:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    result = executor.execute_rule(rule_id, subject_id)
    return result.to_dict()

@app.post("/api/evaluate/subject/{subject_id}")
def evaluate_subject(
    subject_id: str,
    categories: Optional[List[str]] = Query(default=None)
):
    """Evaluate all rules for a subject"""
    results = executor.execute_all_rules(
        subject_id=subject_id,
        categories=categories
    )
    return results

@app.get("/api/evaluate/summary")
def get_evaluation_summary():
    """Get summary statistics"""
    return {
        "total_rules_configured": len(executor.rules),
        "rules_by_category": {
            "exclusion": sum(1 for r in executor.rules.values() if r.category.value == "exclusion"),
            "safety_ae": sum(1 for r in executor.rules.values() if r.category.value == "safety_ae"),
        },
        "rules_by_status": {
            "active": sum(1 for r in executor.rules.values() if r.status == "active"),
            "inactive": sum(1 for r in executor.rules.values() if r.status == "inactive"),
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("Clinical Trial Rules Engine API")
    print("=" * 70)
    print(f"\nRules loaded: {len(executor.rules)}")
    for rule_id in executor.rules:
        print(f"  - {rule_id}")
    print("\nStarting server at http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8001)
