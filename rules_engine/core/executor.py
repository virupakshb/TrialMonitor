"""
Rule Executor - Main engine for running clinical trial rules
"""

import yaml
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.rule import (
    RuleConfig, RuleEvaluationResult, VisitContext,
    RuleCategory, RuleComplexity, EvaluationType, RuleSeverity
)
from ..models.violation import Violation, ViolationType
from ..tools.clinical_tools import ClinicalTools
from ..evaluators.llm_evaluator import LLMEvaluator
from ..templates.exclusion_templates import COMPLEX_EXCLUSION_TEMPLATE, SIMPLE_THRESHOLD_TEMPLATE
from ..templates.ae_templates import AE_TEMPLATES


class RuleExecutor:
    """
    Main rule execution engine
    Routes rules to appropriate evaluators based on complexity
    """
    
    def __init__(self, config_dir: str = None, api_key: str = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / 'rule_configs'
        
        self.config_dir = Path(config_dir)
        self.tools = ClinicalTools()
        self.llm_evaluator = LLMEvaluator(api_key=api_key)
        self.rules: Dict[str, RuleConfig] = {}
        
        # Load all rule configurations
        self._load_rules()
    
    def _load_rules(self):
        """Load all rule configurations from YAML files in config_dir"""
        print("Loading rule configurations...")

        # Map of top-level YAML keys to rule lists
        # Each YAML file may use a different top-level key
        yaml_files = sorted(self.config_dir.glob('*.yaml'))

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                if not config:
                    continue

                # Find the first key that is a list (skip 'protocol' metadata block)
                rules_loaded = 0
                for key, value in config.items():
                    if key == 'protocol':
                        continue
                    if isinstance(value, list):
                        for rule_data in value:
                            if not isinstance(rule_data, dict) or 'rule_id' not in rule_data:
                                continue
                            try:
                                rule = self._parse_rule_config(rule_data)
                                self.rules[rule.rule_id] = rule
                                rules_loaded += 1
                            except Exception as e:
                                print(f"    ERROR parsing rule in {yaml_file.name}: {e}")

                if rules_loaded > 0:
                    print(f"  [{yaml_file.name}] Loaded {rules_loaded} rules")

            except Exception as e:
                print(f"  ERROR loading {yaml_file.name}: {e}")

        print(f"Total rules loaded: {len(self.rules)}")
    
    def _parse_rule_config(self, data: Dict[str, Any]) -> RuleConfig:
        """Parse rule configuration from YAML"""
        return RuleConfig(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            category=RuleCategory(data['category']),
            complexity=RuleComplexity(data['complexity']),
            evaluation_type=EvaluationType(data['evaluation_type']),
            template_name=data['template_name'],
            parameters=data.get('parameters', {}),
            applicable_visits=data.get('applicable_visits', []),
            applicable_phases=data.get('applicable_phases', {}),
            severity=RuleSeverity(data.get('severity', 'major')),
            protocol_reference=data.get('protocol_section'),
            status=data.get('status', 'active'),
            domain_knowledge=data.get('domain_knowledge'),
            tools_needed=data.get('tools_needed', [])
        )
    
    def execute_rule(
        self,
        rule_id: str,
        subject_id: str,
        visit_context: Optional[VisitContext] = None
    ) -> RuleEvaluationResult:
        """
        Execute a single rule for a subject
        
        Args:
            rule_id: Rule identifier
            subject_id: Subject ID to evaluate
            visit_context: Optional visit context
            
        Returns:
            RuleEvaluationResult
        """
        start_time = time.time()
        
        # Get rule configuration
        rule = self.rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        
        if rule.status != "active":
            return RuleEvaluationResult(
                rule_id=rule_id,
                subject_id=subject_id,
                passed=True,
                violated=False,
                reasoning=f"Rule {rule_id} is inactive",
                evaluation_method="skipped"
            )
        
        # Determine study phase
        subject = self.tools.get_subject(subject_id)
        if not subject:
            return RuleEvaluationResult(
                rule_id=rule_id,
                subject_id=subject_id,
                passed=False,
                violated=False,
                reasoning=f"Subject {subject_id} not found",
                missing_data=["subject_data"],
                requires_review=True
            )
        
        study_phase = self._determine_study_phase(subject, visit_context)
        
        # Check if rule applies to this phase
        if not self._rule_applies_to_phase(rule, study_phase):
            return RuleEvaluationResult(
                rule_id=rule_id,
                subject_id=subject_id,
                passed=True,
                violated=False,
                reasoning=f"Rule does not apply to {study_phase} phase",
                evaluation_method="not_applicable"
            )
        
        # Route to appropriate evaluator based on complexity
        try:
            if rule.evaluation_type == EvaluationType.DETERMINISTIC:
                result = self._evaluate_deterministic(rule, subject_id, subject, study_phase)
            elif rule.evaluation_type == EvaluationType.LLM_TOOLS:
                result = self._evaluate_with_llm(rule, subject_id, subject, study_phase, visit_context)
            else:
                result = self._evaluate_hybrid(rule, subject_id, subject, study_phase)
            
            # Add execution time
            execution_time = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time
            
            return result
            
        except Exception as e:
            print(f"Error executing rule {rule_id}: {str(e)}")
            return RuleEvaluationResult(
                rule_id=rule_id,
                subject_id=subject_id,
                passed=False,
                violated=False,
                reasoning=f"Error during evaluation: {str(e)}",
                requires_review=True,
                confidence="low"
            )
    
    def _determine_study_phase(self, subject: Dict, visit_context: Optional[VisitContext]) -> str:
        """Determine current study phase"""
        if visit_context:
            return visit_context.study_phase
        
        # Infer from subject status
        status = subject.get('study_status', 'Screening')
        if status == 'Screening':
            return 'screening'
        elif subject.get('randomization_date'):
            return 'post_randomization'
        else:
            return 'baseline'
    
    def _rule_applies_to_phase(self, rule: RuleConfig, phase: str) -> bool:
        """Check if rule should be evaluated in this phase"""
        if not rule.applicable_phases:
            return True  # No phase restrictions
        
        phase_config = rule.applicable_phases.get(phase, {})
        return phase_config.get('check', False)
    
    def _evaluate_deterministic(
        self,
        rule: RuleConfig,
        subject_id: str,
        subject: Dict,
        study_phase: str
    ) -> RuleEvaluationResult:
        """Evaluate using deterministic tools (no LLM)"""

        phase_config = rule.applicable_phases.get(study_phase, {})
        action = (
            phase_config.get('action_if_violated') or
            phase_config.get('action_if_discovered') or
            'SCREEN_FAILURE'
        )

        # ------------------------------------------------------------------ #
        # DEMOGRAPHIC / FIELD CHECK  (e.g. age, ECOG PS, pregnancy)
        # ------------------------------------------------------------------ #
        if 'field_name' in rule.parameters:
            return self._evaluate_field_check(rule, subject_id, subject, study_phase, action)

        # ------------------------------------------------------------------ #
        # VISIT WINDOW CHECK  (deviation rules)
        # ------------------------------------------------------------------ #
        if rule.parameters.get('check_type') == 'visit_window':
            return self._evaluate_visit_window(rule, subject_id, subject, study_phase, action)

        # ------------------------------------------------------------------ #
        # ADVERSE EVENT CHECK  (AE severity / SAE flag)
        # ------------------------------------------------------------------ #
        if rule.parameters.get('check_type') in ('ae_grade', 'sae_flag', 'ae_ongoing'):
            return self._evaluate_ae_check(rule, subject_id, subject, study_phase, action)

        # ------------------------------------------------------------------ #
        # LAB / ECG THRESHOLD CHECK  (e.g. QTcF >470, ANC >=1.5, Hgb >=9)
        # ------------------------------------------------------------------ #
        if 'test_name' in rule.parameters:
            rule_type = rule.parameters.get('rule_type', 'exclusion')
            result = self.tools.check_lab_threshold(
                subject_id=subject_id,
                test_name=rule.parameters['test_name'],
                operator=rule.parameters['operator'],
                threshold=rule.parameters['threshold'],
                timepoint=rule.parameters.get('timepoint', 'latest')
            )

            if result.get('missing_data'):
                return RuleEvaluationResult(
                    rule_id=rule.rule_id,
                    subject_id=subject_id,
                    passed=False,
                    violated=False,
                    evidence=[result.get('evidence', '')],
                    reasoning="Missing required lab data",
                    missing_data=[rule.parameters['test_name']],
                    requires_review=True,
                    evaluation_method="deterministic"
                )

            meets_criterion = result.get('meets_criterion', False)

            if rule_type == 'inclusion':
                # For inclusion: lab meets threshold = PASS; fails threshold = VIOLATION
                violated = not meets_criterion
                evidence_str = (
                    result.get('evidence', '') +
                    (' -> PASS (meets inclusion criterion)' if meets_criterion
                     else ' -> FAIL (does not meet inclusion criterion)')
                )
                recommendation = (
                    f"Subject meets lab inclusion criterion: {rule.description}" if meets_criterion
                    else f"Subject does NOT meet lab inclusion criterion: {rule.description} — {action}"
                )
            else:
                # For exclusion / safety: meets threshold = VIOLATION
                violated = meets_criterion
                evidence_str = result.get('evidence', '')
                recommendation = f"Subject {'excluded' if study_phase == 'screening' else 'flagged'} - {action}"

            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                subject_id=subject_id,
                passed=not violated,
                violated=violated,
                severity=rule.severity if violated else None,
                evidence=[evidence_str],
                reasoning=f"Laboratory check: {evidence_str}",
                confidence="high",
                evaluation_method="deterministic",
                tools_used=["check_lab_threshold"],
                action_required=action if violated else None,
                recommendation=recommendation
            )

        # Default for unrecognised check types
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=True,
            violated=False,
            reasoning="Deterministic check completed (no matching check type)",
            evaluation_method="deterministic"
        )

    # ---------------------------------------------------------------------- #
    # HELPER: Field / demographic check
    # ---------------------------------------------------------------------- #
    def _evaluate_field_check(
        self,
        rule: RuleConfig,
        subject_id: str,
        subject: Dict,
        study_phase: str,
        action: str
    ) -> RuleEvaluationResult:
        """Evaluate a simple demographic/field value check"""
        field_name = rule.parameters['field_name']
        operator   = rule.parameters['operator']
        threshold  = rule.parameters['threshold']
        # inclusion rules: violated means criterion NOT met
        # exclusion rules: violated means criterion IS met
        rule_type  = rule.parameters.get('rule_type', 'exclusion')  # 'inclusion' or 'exclusion'

        value = subject.get(field_name)

        if value is None:
            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                subject_id=subject_id,
                passed=False,
                violated=False,
                reasoning=f"Field '{field_name}' not found for subject",
                missing_data=[field_name],
                requires_review=True,
                evaluation_method="deterministic"
            )

        # Special handling for null/None threshold comparisons (e.g. consent_date != null)
        if threshold is None:
            if operator == "!=":
                meets = value is not None and str(value).strip() != ''
            elif operator == "==":
                meets = value is None or str(value).strip() == ''
            else:
                meets = False
        else:
            ops = {
                ">=": lambda a, b: float(a) >= float(b),
                ">":  lambda a, b: float(a) > float(b),
                "<=": lambda a, b: float(a) <= float(b),
                "<":  lambda a, b: float(a) < float(b),
                "==": lambda a, b: str(a).lower() == str(b).lower(),
                "!=": lambda a, b: str(a).lower() != str(b).lower(),
                "in": lambda a, b: str(a).lower() in [str(x).lower() for x in b] if isinstance(b, list) else str(a).lower() == str(b).lower(),
            }
            try:
                meets = ops.get(operator, lambda a, b: False)(value, threshold)
            except (TypeError, ValueError):
                meets = False

        if rule_type == 'inclusion':
            # For inclusion: criterion met = PASS, not met = VIOLATION
            violated = not meets
            evidence_str = f"{field_name}: {value} (required {operator} {threshold}) -> {'PASS' if meets else 'FAIL - criterion not met'}"
        else:
            # For exclusion: criterion met = VIOLATION
            violated = meets
            evidence_str = f"{field_name}: {value} {operator} {threshold} -> {'VIOLATION' if meets else 'PASS'}"

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=not violated,
            violated=violated,
            severity=rule.severity if violated else None,
            evidence=[evidence_str],
            reasoning=f"Field check on '{field_name}': {evidence_str}",
            confidence="high",
            evaluation_method="deterministic",
            tools_used=["check_demographics"],
            action_required=action if violated else None,
            recommendation=f"Subject {'does not meet inclusion criterion' if rule_type=='inclusion' else 'meets exclusion criterion'}: {rule.description}"
        )

    # ---------------------------------------------------------------------- #
    # HELPER: Visit window check
    # ---------------------------------------------------------------------- #
    def _evaluate_visit_window(
        self,
        rule: RuleConfig,
        subject_id: str,
        subject: Dict,
        study_phase: str,
        action: str
    ) -> RuleEvaluationResult:
        """Check if any visits are outside the protocol window"""
        result = self.tools.check_visit_windows(subject_id)
        violations = result.get('out_of_window', [])
        violated = len(violations) > 0
        evidence = [v['description'] for v in violations]

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=not violated,
            violated=violated,
            severity=rule.severity if violated else None,
            evidence=evidence,
            reasoning=f"Visit window check: {len(violations)} visit(s) outside protocol window",
            confidence="high",
            evaluation_method="deterministic",
            tools_used=["check_visit_windows"],
            action_required=action if violated else None,
            recommendation=f"{'Protocol deviation: ' + str(len(violations)) + ' visit(s) outside window' if violated else 'All visits within protocol window'}"
        )

    # ---------------------------------------------------------------------- #
    # HELPER: AE check
    # ---------------------------------------------------------------------- #
    def _evaluate_ae_check(
        self,
        rule: RuleConfig,
        subject_id: str,
        subject: Dict,
        study_phase: str,
        action: str
    ) -> RuleEvaluationResult:
        """Check adverse events for safety signals"""
        check_type   = rule.parameters.get('check_type')
        min_grade    = rule.parameters.get('min_grade', 3)
        seriousness  = rule.parameters.get('seriousness')

        aes = self.tools.get_adverse_events(
            subject_id=subject_id,
            seriousness=seriousness,
            ongoing=None
        )

        if check_type == 'ae_grade':
            matching = [ae for ae in aes if (ae.get('ctcae_grade') or 0) >= min_grade]
        elif check_type == 'sae_flag':
            matching = [ae for ae in aes if ae.get('seriousness') == 'Yes']
        else:
            matching = [ae for ae in aes if ae.get('ongoing')]

        violated = len(matching) > 0
        evidence = [
            f"{ae.get('ae_term')} - Grade {ae.get('ctcae_grade')} "
            f"({ae.get('severity')}, SAE={ae.get('seriousness')}, onset={ae.get('onset_date')})"
            for ae in matching
        ]

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=not violated,
            violated=violated,
            severity=rule.severity if violated else None,
            evidence=evidence,
            reasoning=f"AE check ({check_type}): {len(matching)} matching event(s) found",
            confidence="high",
            evaluation_method="deterministic",
            tools_used=["get_adverse_events"],
            action_required=action if violated else None,
            recommendation=f"{'Safety signal: review AEs immediately' if violated else 'No qualifying AEs found'}"
        )
    
    def _evaluate_with_llm(
        self,
        rule: RuleConfig,
        subject_id: str,
        subject: Dict,
        study_phase: str,
        visit_context: Optional[VisitContext]
    ) -> RuleEvaluationResult:
        """Evaluate using LLM reasoning with tools"""
        
        # Build context for LLM
        context = self._build_llm_context(rule, subject_id, subject, study_phase, visit_context)
        
        # Use LLM evaluator
        result = self.llm_evaluator.evaluate(rule, subject_id, context)
        
        # Override action based on phase if needed
        if result.violated:
            phase_config = rule.applicable_phases.get(study_phase, {})
            # action_if_violated is used at screening/baseline;
            # action_if_discovered is used post-randomization
            action = (
                phase_config.get('action_if_violated') or
                phase_config.get('action_if_discovered') or
                'REQUIRES_REVIEW'
            )
            result.action_required = action
            
            # Update recommendation
            if study_phase == 'screening':
                result.recommendation = f"SCREEN FAILURE - {result.recommendation}"
            elif study_phase == 'post_randomization':
                result.recommendation = f"PROTOCOL DEVIATION - {result.recommendation}"
        
        return result
    
    def _evaluate_hybrid(self, rule: RuleConfig, subject_id: str, subject: Dict, study_phase: str) -> RuleEvaluationResult:
        """Evaluate using hybrid approach"""
        # Placeholder for hybrid evaluation
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=True,
            violated=False,
            reasoning="Hybrid evaluation not yet implemented",
            evaluation_method="hybrid"
        )
    
    def _build_llm_context(
        self,
        rule: RuleConfig,
        subject_id: str,
        subject: Dict,
        study_phase: str,
        visit_context: Optional[VisitContext]
    ) -> str:
        """Build context string for LLM evaluation"""

        # Get all medical history (wildcard search returns everything)
        history = self.tools.check_medical_history(subject_id, [""], status_filter="any")
        history_summary = "\n".join(history['evidence'][:10]) if history['evidence'] else "None documented"

        # Get all current medications (no filter = all ongoing meds)
        conmeds = self.tools.check_conmeds(subject_id)
        meds_summary = "\n".join(conmeds['evidence'][:10]) if conmeds['evidence'] else "None documented"

        # Include tumor assessment summary so LLM can see progression/new lesion data
        assessments = self.tools.get_tumor_assessments(subject_id)
        if assessments:
            tumor_lines = []
            for a in assessments:
                line = (
                    f"{a.get('assessment_date')}: {a.get('overall_response')} "
                    f"(new_lesions={a.get('new_lesions')}, progression={a.get('progression')})"
                )
                tumor_lines.append(line)
            tumor_summary = "\n".join(tumor_lines[-5:])  # last 5 assessments
        else:
            tumor_summary = "No tumor assessments on record"

        # Build search-terms hint so LLM knows exactly what to look for
        search_cfg = rule.parameters.get('search_terms', {})
        hint_parts = []
        for key, vals in search_cfg.items():
            if vals:
                hint_parts.append(f"{key}: {', '.join(vals)}")
        search_hint = "\n".join(hint_parts) if hint_parts else "See domain knowledge above"

        # Evaluation criteria from YAML (may be empty for some rules)
        eval_criteria = rule.parameters.get('evaluation_criteria', '')

        # Fill template — domain_knowledge is read from YAML with utf-8 so
        # special characters are preserved correctly
        domain_knowledge = (rule.domain_knowledge or "See protocol").encode(
            'ascii', errors='replace'
        ).decode('ascii')

        template = COMPLEX_EXCLUSION_TEMPLATE

        return template.format(
            subject_id=subject_id,
            protocol_number="NVX-1218.22",
            protocol_name="NovaPlex-450 in Advanced NSCLC",
            criterion_id=rule.rule_id,
            criterion_description=rule.description,
            protocol_section=rule.protocol_reference or "Not specified",
            study_phase=study_phase,
            domain_knowledge=domain_knowledge,
            evaluation_criteria=(
                eval_criteria if eval_criteria else
                f"Search for the following in patient data:\n{search_hint}"
            ),
            age=subject.get('age', 'Unknown'),
            sex=subject.get('sex', 'Unknown'),
            primary_diagnosis=subject.get('primary_diagnosis', 'NSCLC Stage IV'),
            study_status=subject.get('study_status', 'Unknown'),
            recent_medical_history=history_summary,
            current_medications=meds_summary,
            visit_context=(
                f"Visit: {visit_context.visit_name}" if visit_context
                else f"Study phase: {study_phase}\nTumor Assessments:\n{tumor_summary}"
            )
        )
    
    def execute_all_rules(
        self,
        subject_id: str,
        categories: List[str] = None,
        visit_context: Optional[VisitContext] = None
    ) -> Dict[str, Any]:
        """
        Execute all active rules for a subject
        
        Args:
            subject_id: Subject to evaluate
            categories: Optional list of categories to filter
            visit_context: Optional visit context
            
        Returns:
            Summary of results
        """
        results = []
        violations = []
        
        for rule_id, rule in self.rules.items():
            if categories and rule.category.value not in categories:
                continue
            
            result = self.execute_rule(rule_id, subject_id, visit_context)
            results.append(result)
            
            if result.violated:
                # Create violation
                violation = Violation.from_evaluation_result(
                    result,
                    ViolationType.ELIGIBILITY
                )
                violations.append(violation)
        
        return {
            "subject_id": subject_id,
            "total_rules_executed": len(results),
            "violations_found": len(violations),
            "results": [r.to_dict() for r in results],
            "violations": [v.to_dict() for v in violations]
        }
