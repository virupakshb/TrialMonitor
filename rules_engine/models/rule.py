"""
Rule data models for clinical trial monitoring
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class RuleCategory(Enum):
    """Rule categories"""
    EXCLUSION = "exclusion"
    INCLUSION = "inclusion"
    SAFETY_AE = "safety_ae"
    SAFETY_LAB = "safety_lab"
    SAFETY_VITAL = "safety_vital"
    PROTOCOL_VISIT = "protocol_visit"
    PROTOCOL_DOSE = "protocol_dose"
    DATA_QUALITY = "data_quality"
    EFFICACY = "efficacy"


class RuleComplexity(Enum):
    """Rule complexity levels"""
    SIMPLE = "simple"           # Direct tool call
    MEDIUM = "medium"           # Pattern matching
    COMPLEX = "complex"         # LLM reasoning required


class RuleSeverity(Enum):
    """Violation severity levels"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class EvaluationType(Enum):
    """How rule is evaluated"""
    DETERMINISTIC = "deterministic"
    PATTERN_MATCH = "pattern_match"
    LLM_TOOLS = "llm_with_tools"
    HYBRID = "hybrid"


@dataclass
class RuleConfig:
    """Configuration for a single rule"""
    rule_id: str
    name: str
    description: str
    category: RuleCategory
    complexity: RuleComplexity
    evaluation_type: EvaluationType
    
    # Template and logic
    template_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Applicability
    applicable_visits: List[str] = field(default_factory=list)
    applicable_phases: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    severity: RuleSeverity = RuleSeverity.MAJOR
    protocol_reference: Optional[str] = None
    status: str = "active"
    version: int = 1
    
    # For LLM-based rules
    domain_knowledge: Optional[str] = None
    tools_needed: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = "system"


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a rule"""
    rule_id: str
    subject_id: str
    visit_id: Optional[int] = None
    
    # Result
    passed: bool = True
    violated: bool = False
    
    # Details
    severity: Optional[RuleSeverity] = None
    evidence: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    # Metadata
    confidence: str = "high"  # high, medium, low
    evaluation_method: str = ""
    tools_used: List[str] = field(default_factory=list)
    
    # Actions
    action_required: Optional[str] = None
    recommendation: str = ""
    
    # Missing data
    missing_data: List[str] = field(default_factory=list)
    requires_review: bool = False
    
    # Technical
    execution_time_ms: int = 0
    evaluated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "subject_id": self.subject_id,
            "visit_id": self.visit_id,
            "passed": self.passed,
            "violated": self.violated,
            "severity": self.severity.value if self.severity else None,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evaluation_method": self.evaluation_method,
            "tools_used": self.tools_used,
            "action_required": self.action_required,
            "recommendation": self.recommendation,
            "missing_data": self.missing_data,
            "requires_review": self.requires_review,
            "execution_time_ms": self.execution_time_ms,
            "evaluated_at": self.evaluated_at.isoformat()
        }


@dataclass
class VisitContext:
    """Context about current visit"""
    visit_id: int
    visit_number: int
    visit_name: str
    visit_type: str
    scheduled_date: Optional[str] = None
    actual_date: Optional[str] = None
    study_phase: str = "screening"  # screening, baseline, treatment, follow-up
    
    def is_screening(self) -> bool:
        return self.study_phase == "screening"
    
    def is_baseline(self) -> bool:
        return self.study_phase == "baseline"
    
    def is_post_randomization(self) -> bool:
        return self.study_phase in ["treatment", "follow-up"]
