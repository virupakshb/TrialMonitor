"""
Violation data model
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ViolationStatus(Enum):
    """Violation status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class ViolationType(Enum):
    """Type of violation"""
    ELIGIBILITY = "eligibility_violation"
    SAFETY_SIGNAL = "safety_signal"
    PROTOCOL_DEVIATION = "protocol_deviation"
    DATA_QUALITY = "data_quality_issue"
    REGULATORY = "regulatory_concern"


@dataclass
class Violation:
    """Represents a rule violation"""
    violation_id: Optional[int] = None
    rule_id: str = ""
    subject_id: str = ""
    visit_id: Optional[int] = None
    
    # Violation details
    violation_type: ViolationType = ViolationType.PROTOCOL_DEVIATION
    severity: str = "major"  # critical, major, minor
    status: ViolationStatus = ViolationStatus.OPEN
    
    # Description
    violation_description: str = ""
    evidence: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    # Actions
    action_required: Optional[str] = None
    recommendation: str = ""
    
    # Data
    violation_data: Dict[str, Any] = field(default_factory=dict)
    
    # Workflow
    assigned_to: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Timestamps
    violation_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "violation_id": self.violation_id,
            "rule_id": self.rule_id,
            "subject_id": self.subject_id,
            "visit_id": self.visit_id,
            "violation_type": self.violation_type.value,
            "severity": self.severity,
            "status": self.status.value,
            "violation_description": self.violation_description,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "action_required": self.action_required,
            "recommendation": self.recommendation,
            "violation_data": self.violation_data,
            "assigned_to": self.assigned_to,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "violation_date": self.violation_date.isoformat() if self.violation_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_evaluation_result(cls, result, violation_type: ViolationType):
        """Create violation from evaluation result"""
        return cls(
            rule_id=result.rule_id,
            subject_id=result.subject_id,
            visit_id=result.visit_id,
            violation_type=violation_type,
            severity=result.severity.value if result.severity else "major",
            violation_description=result.reasoning[:500] if result.reasoning else "",
            evidence=result.evidence,
            reasoning=result.reasoning,
            action_required=result.action_required,
            recommendation=result.recommendation,
            violation_data={
                "confidence": result.confidence,
                "evaluation_method": result.evaluation_method,
                "tools_used": result.tools_used,
                "missing_data": result.missing_data
            },
            violation_date=result.evaluated_at
        )
