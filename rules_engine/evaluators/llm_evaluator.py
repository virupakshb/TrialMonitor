"""
LLM Evaluator using Claude API (Anthropic)
Handles complex rule evaluation requiring medical reasoning
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic

from ..models.rule import RuleConfig, RuleEvaluationResult, RuleSeverity
from ..tools.clinical_tools import ClinicalTools
from ..templates.exclusion_templates import COMPLEX_EXCLUSION_TEMPLATE
from ..templates.ae_templates import AE_TEMPLATES


# Global token usage tracker (accumulated across all evaluations in this session)
_usage_tracker = {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_api_calls": 0,
    "llm_rule_evaluations": 0,
    # Pricing: claude-sonnet-4 = $3/M input, $15/M output (approximate)
    "input_cost_per_million": 3.00,
    "output_cost_per_million": 15.00,
}


def get_usage_stats():
    """Return current token usage and estimated cost"""
    input_cost = (_usage_tracker["total_input_tokens"] / 1_000_000) * _usage_tracker["input_cost_per_million"]
    output_cost = (_usage_tracker["total_output_tokens"] / 1_000_000) * _usage_tracker["output_cost_per_million"]
    return {
        **_usage_tracker,
        "total_tokens": _usage_tracker["total_input_tokens"] + _usage_tracker["total_output_tokens"],
        "estimated_cost_usd": round(input_cost + output_cost, 6),
        "estimated_cost_display": f"${input_cost + output_cost:.4f}",
    }


def reset_usage_stats():
    """Reset usage tracker"""
    _usage_tracker["total_input_tokens"] = 0
    _usage_tracker["total_output_tokens"] = 0
    _usage_tracker["total_api_calls"] = 0
    _usage_tracker["llm_rule_evaluations"] = 0


class LLMEvaluator:
    """
    Evaluates complex rules using Claude API with tool calling
    """

    def __init__(self, api_key: str = None):
        """
        Initialize LLM evaluator
        
        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        
        # For demo/testing without API key, use mock mode
        self.mock_mode = not self.api_key
        
        if not self.mock_mode:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            print("WARNING: Running in MOCK mode - no actual LLM calls")
        
        self.tools_client = ClinicalTools()
        self.tool_definitions = self._build_tool_definitions()
    
    def _build_tool_definitions(self) -> List[Dict[str, Any]]:
        """Build tool definitions for Claude function calling"""
        return [
            {
                "name": "check_medical_history",
                "description": "Search patient medical history for conditions, diagnoses, or treatments",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {
                            "type": "string",
                            "description": "Subject ID to search"
                        },
                        "search_terms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of conditions, diagnoses, or treatments to search for"
                        },
                        "status_filter": {
                            "type": "string",
                            "enum": ["ongoing", "resolved", "any"],
                            "description": "Filter by condition status"
                        }
                    },
                    "required": ["subject_id", "search_terms"]
                }
            },
            {
                "name": "check_conmeds",
                "description": "Check patient's concomitant medications",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {
                            "type": "string",
                            "description": "Subject ID"
                        },
                        "medication_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Medication names to search for"
                        },
                        "medication_classes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Medication classes to search for"
                        }
                    },
                    "required": ["subject_id"]
                }
            },
            {
                "name": "check_lab_threshold",
                "description": "Check if a laboratory value meets a threshold criterion",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"},
                        "test_name": {"type": "string"},
                        "operator": {
                            "type": "string",
                            "enum": [">=", ">", "<=", "<", "=="]
                        },
                        "threshold": {"type": "number"},
                        "timepoint": {
                            "type": "string",
                            "enum": ["latest", "screening", "baseline"]
                        }
                    },
                    "required": ["subject_id", "test_name", "operator", "threshold"]
                }
            },
            {
                "name": "get_ecg_results",
                "description": "Get ECG results for a subject",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"}
                    },
                    "required": ["subject_id"]
                }
            },
            {
                "name": "get_tumor_assessments",
                "description": "Get tumor assessment results for a subject, including RECIST responses, new lesions, and progression status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"}
                    },
                    "required": ["subject_id"]
                }
            },
            {
                "name": "get_adverse_events",
                "description": "Get adverse events for a subject, optionally filtered by seriousness or ongoing status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {
                            "type": "string",
                            "description": "Subject ID to look up"
                        },
                        "seriousness": {
                            "type": "string",
                            "enum": ["Yes", "No"],
                            "description": "Filter by seriousness: 'Yes' for SAEs, 'No' for non-serious AEs"
                        },
                        "ongoing": {
                            "type": "boolean",
                            "description": "If true, return only ongoing AEs; if false, only resolved AEs"
                        }
                    },
                    "required": ["subject_id"]
                }
            },
            {
                "name": "get_labs",
                "description": "Get laboratory results for a subject, optionally filtered by test names",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {
                            "type": "string",
                            "description": "Subject ID"
                        },
                        "test_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lab test names to retrieve (e.g. ['ALT', 'AST', 'Creatinine'])"
                        },
                        "timeframe_days": {
                            "type": "integer",
                            "description": "Look back this many days for results"
                        }
                    },
                    "required": ["subject_id"]
                }
            },
            {
                "name": "get_visits",
                "description": "Get all study visits for a subject with scheduled and actual dates and visit window info",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"}
                    },
                    "required": ["subject_id"]
                }
            }
        ]
    
    def evaluate(
        self,
        rule: RuleConfig,
        subject_id: str,
        context: str
    ) -> RuleEvaluationResult:
        """
        Evaluate a rule using LLM reasoning with tools
        
        Args:
            rule: Rule configuration
            subject_id: Subject to evaluate
            context: Pre-built context string for LLM
            
        Returns:
            RuleEvaluationResult
        """
        
        if self.mock_mode:
            return self._mock_evaluation(rule, subject_id, context)
        
        try:
            # Multi-turn tool calling loop (up to 5 rounds)
            messages = [{"role": "user", "content": context}]
            tools_used = []
            max_rounds = 5

            for round_num in range(max_rounds):
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    tools=self.tool_definitions,
                    messages=messages
                )

                # Track token usage
                if hasattr(response, 'usage') and response.usage:
                    _usage_tracker["total_input_tokens"] += response.usage.input_tokens
                    _usage_tracker["total_output_tokens"] += response.usage.output_tokens
                    _usage_tracker["total_api_calls"] += 1

                # Collect tool calls from this round
                tool_calls_this_round = [b for b in response.content if b.type == "tool_use"]

                if not tool_calls_this_round or response.stop_reason == "end_turn":
                    # No more tool calls — this is the final response
                    _usage_tracker["llm_rule_evaluations"] += 1
                    return self._parse_llm_response(response, rule, subject_id, tools_used)

                # Execute all tool calls in this round
                tool_results_this_round = []
                for block in tool_calls_this_round:
                    tool_result = self._execute_tool(block.name, block.input)
                    tools_used.append(block.name)
                    tool_results_this_round.append(tool_result)

                # Append assistant turn + tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                tool_result_idx = 0
                for block in response.content:
                    if block.type == "tool_use":
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(tool_results_this_round[tool_result_idx])
                            }]
                        })
                        tool_result_idx += 1

            # Fallback if max rounds exceeded — get final answer
            final_response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                tools=self.tool_definitions,
                messages=messages
            )
            if hasattr(final_response, 'usage') and final_response.usage:
                _usage_tracker["total_input_tokens"] += final_response.usage.input_tokens
                _usage_tracker["total_output_tokens"] += final_response.usage.output_tokens
                _usage_tracker["total_api_calls"] += 1
            _usage_tracker["llm_rule_evaluations"] += 1
            return self._parse_llm_response(final_response, rule, subject_id, tools_used)
                
        except Exception as e:
            print(f"LLM evaluation error: {str(e)}")
            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                subject_id=subject_id,
                passed=False,
                violated=False,
                reasoning=f"LLM evaluation error: {str(e)}",
                confidence="low",
                requires_review=True,
                evaluation_method="llm_with_tools"
            )
    
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results"""
        
        tool_map = {
            "check_medical_history": self.tools_client.check_medical_history,
            "check_conmeds": self.tools_client.check_conmeds,
            "check_lab_threshold": self.tools_client.check_lab_threshold,
            "get_ecg_results": self.tools_client.get_ecg_results,
            "get_tumor_assessments": self.tools_client.get_tumor_assessments,
            "get_adverse_events": self.tools_client.get_adverse_events,
            "get_labs": self.tools_client.get_labs_for_subject,
            "get_visits": self.tools_client.get_visits_for_subject,
        }
        
        tool_func = tool_map.get(tool_name)
        if not tool_func:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            result = tool_func(**tool_input)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_llm_response(
        self,
        response,
        rule: RuleConfig,
        subject_id: str,
        tools_used: List[str]
    ) -> RuleEvaluationResult:
        """Parse LLM response into RuleEvaluationResult"""
        
        # Extract text content
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text
        
        # Try to parse JSON from response
        try:
            # Look for JSON in the response
            if "{" in text_content and "}" in text_content:
                # Extract JSON portion
                start = text_content.find("{")
                end = text_content.rfind("}") + 1
                json_str = text_content[start:end]
                
                # Clean up common formatting issues
                json_str = json_str.replace("```json", "").replace("```", "").strip()
                
                data = json.loads(json_str)
                
                return RuleEvaluationResult(
                    rule_id=rule.rule_id,
                    subject_id=subject_id,
                    passed=not data.get("excluded", False),
                    violated=data.get("excluded", False),
                    severity=rule.severity if data.get("excluded") else None,
                    evidence=data.get("evidence", []),
                    reasoning=data.get("reasoning", text_content),
                    confidence=data.get("confidence", "medium"),
                    evaluation_method="llm_with_tools",
                    tools_used=tools_used,
                    action_required=data.get("action_required"),
                    recommendation=data.get("recommendation", ""),
                    missing_data=data.get("missing_data", []),
                    requires_review=data.get("requires_review", False)
                )
        except json.JSONDecodeError:
            pass
        
        # Fallback: parse from text
        violated = any(word in text_content.lower() for word in ["excluded", "violation", "violated"])
        
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=not violated,
            violated=violated,
            severity=rule.severity if violated else None,
            evidence=[],
            reasoning=text_content[:500],
            confidence="medium",
            evaluation_method="llm_with_tools",
            tools_used=tools_used,
            requires_review=True
        )
    
    def _mock_evaluation(
        self,
        rule: RuleConfig,
        subject_id: str,
        context: str
    ) -> RuleEvaluationResult:
        """
        Mock evaluation for testing without API key.
        Uses actual tools to gather evidence based on the rule's category and tools_needed.
        Supports: exclusion, inclusion, safety_ae, safety_lab, efficacy, protocol_visit rules.
        """

        tools_used = []
        evidence = []
        search_terms_cfg = rule.parameters.get('search_terms', {})
        category = rule.category.value  # e.g. 'exclusion', 'inclusion', 'safety_ae', 'efficacy'

        # ------------------------------------------------------------------ #
        # MEDICAL HISTORY SEARCH
        # ------------------------------------------------------------------ #
        if "check_medical_history" in rule.tools_needed:
            history_terms = (
                search_terms_cfg.get('conditions', []) or
                search_terms_cfg.get('drug_names', [])
            )
            if history_terms:
                result = self.tools_client.check_medical_history(
                    subject_id=subject_id,
                    search_terms=history_terms[:10],
                    status_filter="any"
                )
                tools_used.append('check_medical_history')
                if result['found']:
                    evidence.extend(result['evidence'])

        # ------------------------------------------------------------------ #
        # CONCOMITANT MEDICATIONS SEARCH
        # ------------------------------------------------------------------ #
        if "check_conmeds" in rule.tools_needed:
            med_names = (
                search_terms_cfg.get('medications', []) or
                search_terms_cfg.get('drug_names', [])
            )
            med_classes = search_terms_cfg.get('drug_classes', [])
            if med_names or med_classes:
                result = self.tools_client.check_conmeds(
                    subject_id=subject_id,
                    medication_names=med_names[:10] if med_names else None,
                    medication_classes=med_classes[:5] if med_classes else None
                )
                tools_used.append('check_conmeds')
                if result['found']:
                    evidence.extend(result['evidence'])

        # ------------------------------------------------------------------ #
        # TUMOR ASSESSMENTS
        # ------------------------------------------------------------------ #
        if "get_tumor_assessments" in rule.tools_needed:
            assessments = self.tools_client.get_tumor_assessments(subject_id=subject_id)
            tools_used.append('get_tumor_assessments')
            for a in assessments:
                if a.get('progression') or a.get('new_lesions'):
                    evidence.append(
                        f"Tumor assessment {a.get('assessment_date')}: "
                        f"{a.get('overall_response')} — "
                        f"new_lesions={a.get('new_lesions')}, progression={a.get('progression')}"
                    )

        # ------------------------------------------------------------------ #
        # ADVERSE EVENTS
        # ------------------------------------------------------------------ #
        if "get_adverse_events" in rule.tools_needed:
            aes = self.tools_client.get_adverse_events(subject_id=subject_id)
            tools_used.append('get_adverse_events')
            min_grade = rule.parameters.get('min_grade', 3)
            for ae in aes:
                grade = ae.get('ctcae_grade') or 0
                serious = ae.get('seriousness') == 'Yes'
                if serious or grade >= min_grade:
                    evidence.append(
                        f"AE: {ae.get('ae_term')} - Grade {grade} "
                        f"(SAE={ae.get('seriousness')}, onset={ae.get('onset_date')})"
                    )

        # ------------------------------------------------------------------ #
        # LAB RESULTS (for LLM rules referencing labs)
        # ------------------------------------------------------------------ #
        if "check_labs" in rule.tools_needed:
            test_names = search_terms_cfg.get('lab_tests', [])
            labs = self.tools_client.get_labs_for_subject(
                subject_id=subject_id,
                test_names=test_names if test_names else None
            )
            tools_used.append('check_labs')
            for lab in labs[:10]:
                if lab.get('abnormal_flag') in ('H', 'L', 'A'):
                    evidence.append(
                        f"Lab {lab.get('test_name')}: {lab.get('test_value')} {lab.get('test_unit')} "
                        f"[{lab.get('abnormal_flag')}] on {lab.get('collection_date')}"
                    )

        # ------------------------------------------------------------------ #
        # DECISION: inclusion rules need inverted logic
        # ------------------------------------------------------------------ #
        if category == 'inclusion':
            # For inclusion: evidence of the criterion = PASS; no evidence = could be a gap
            # But in mock mode we only have LLM rules for inclusion that need specific findings
            # Conservative: if no evidence found, flag as needing review (not auto-fail)
            violated = False  # Don't auto-fail inclusion in mock — requires manual review
            requires_review = True
            reasoning = (
                f"Mock evaluation (inclusion rule): Evidence collected. "
                f"Manual review required to confirm criterion is met. Tools used: {tools_used}"
            )
            action = None
            recommendation = "Manual review required: Verify inclusion criterion is satisfied"
        elif category in ('safety_ae', 'safety_lab'):
            violated = len(evidence) > 0
            requires_review = violated
            reasoning = (
                f"Mock evaluation (safety rule): "
                f"{'Found safety signal(s)' if violated else 'No safety signals detected'}. "
                f"Tools used: {tools_used}"
            )
            action = "SAFETY_REVIEW_REQUIRED" if violated else None
            recommendation = (
                "Immediate safety review required" if violated
                else "No qualifying safety events found"
            )
        elif category == 'efficacy':
            violated = len(evidence) > 0
            requires_review = True
            reasoning = (
                f"Mock evaluation (efficacy rule): "
                f"{'Efficacy event detected' if violated else 'No efficacy events detected'}. "
                f"Tools used: {tools_used}"
            )
            action = "EFFICACY_REVIEW" if violated else None
            recommendation = "Efficacy event review required" if violated else "No qualifying events"
        else:
            # Default: exclusion / deviation rules
            violated = len(evidence) > 0
            requires_review = True
            reasoning = (
                f"Mock evaluation: {'Found' if violated else 'Did not find'} evidence. "
                f"Tools used: {tools_used}"
            )
            action = "SCREEN_FAILURE" if violated else None
            recommendation = (
                "Subject should be reviewed for exclusion" if violated
                else "No exclusionary evidence found"
            )

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            subject_id=subject_id,
            passed=not violated,
            violated=violated,
            severity=rule.severity if violated else None,
            evidence=evidence,
            reasoning=reasoning,
            confidence="high" if evidence else "medium",
            evaluation_method="llm_with_tools_mock",
            tools_used=tools_used,
            requires_review=requires_review,
            action_required=action,
            recommendation=recommendation
        )
