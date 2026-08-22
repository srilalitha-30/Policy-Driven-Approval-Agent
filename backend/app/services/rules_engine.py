"""
Rules Engine: Evaluates expense claims against configured rules.

This module implements the core deterministic rule evaluation logic.
It takes validated structured rules and expense claims, then produces
decisions with complete traceability.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from app.schemas import Condition, StructuredRule, EvaluationConditionTrace, MatchedRuleInfo, EvaluationResponse


@dataclass
class RuleRecord:
    """A rule stored in the database (for evaluation context)."""
    id: int
    name: str
    structured_rule: Dict[str, Any]
    decision: str
    priority: int
    status: str


@dataclass
class ClaimRecord:
    """A claim/expense record (for evaluation context)."""
    id: str
    employee: str
    department: Optional[str]
    category: str
    amount: float
    currency: str
    date: str
    description: str


class RulesEngine:
    """Evaluates claims against a set of rules."""
    
    # Decision precedence when multiple rules match
    # Lower number = higher priority to win
    DECISION_PRECEDENCE = {
        "REJECT": 1,      # Most restrictive
        "ESCALATE": 2,
        "APPROVE": 3,     # Most permissive
    }
    
    @staticmethod
    def evaluate_claim(
        claim: ClaimRecord,
        rules: List[RuleRecord]
    ) -> Tuple[str, Optional[int], str, List[EvaluationConditionTrace], List[MatchedRuleInfo]]:
        """
        Evaluate a single claim against all rules.
        
        Args:
            claim: The expense claim to evaluate
            rules: List of rules to evaluate against
            
        Returns:
            Tuple of (decision, winning_rule_id, rationale, evaluation_trace, matched_rules)
        """
        # Filter to active rules
        active_rules = [r for r in rules if r.status == "active"]
        
        if not active_rules:
            return (
                "ESCALATE",
                None,
                "No active rules configured. Manual review required.",
                [],
                []
            )
        
        # Evaluate all rules
        matched_rules_info: List[MatchedRuleInfo] = []
        rule_evaluations: List[Tuple[RuleRecord, bool, List[EvaluationConditionTrace]]] = []
        
        for rule in active_rules:
            try:
                matched, trace = RulesEngine._evaluate_rule(claim, rule)
                rule_evaluations.append((rule, matched, trace))
                
                if matched:
                    matched_rules_info.append(MatchedRuleInfo(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        decision=rule.decision,
                        priority=rule.priority
                    ))
            except Exception as e:
                # If rule evaluation fails, skip it but log it
                continue
        
        # Filter to matched rules
        matched_rule_evals = [(r, t) for r, m, t in rule_evaluations if m]
        
        if not matched_rule_evals:
            # No matching rule - escalate for manual review
            all_traces = []
            for rule, matched, trace in rule_evaluations:
                all_traces.extend(trace)
            
            return (
                "ESCALATE",
                None,
                "No configured rule matched this claim. Manual review required.",
                all_traces if all_traces else [],
                matched_rules_info
            )
        
        # Multiple rules matched - use priority to determine winner
        winning_rule, trace = RulesEngine._resolve_winner(matched_rule_evals)
        
        rationale = RulesEngine._generate_rationale(
            claim,
            winning_rule,
            matched_rule_evals,
            trace
        )
        
        return (
            winning_rule.decision,
            winning_rule.id,
            rationale,
            trace,
            matched_rules_info
        )
    
    @staticmethod
    def _evaluate_rule(
        claim: ClaimRecord,
        rule: RuleRecord
    ) -> Tuple[bool, List[EvaluationConditionTrace]]:
        """
        Evaluate if a claim matches a specific rule.
        
        Args:
            claim: The expense claim
            rule: The rule to evaluate
            
        Returns:
            Tuple of (matched: bool, trace: List[EvaluationConditionTrace])
        """
        trace: List[EvaluationConditionTrace] = []
        
        # Handle empty conditions (should not happen after validation, but be safe)
        if not rule.structured_rule.get("conditions"):
            return True, trace
        
        # Evaluate all conditions (all must be true for rule to match - AND logic)
        all_match = True
        
        for condition_dict in rule.structured_rule["conditions"]:
            condition = Condition(**condition_dict)
            matched = RulesEngine._evaluate_condition(claim, condition)
            
            # Build trace entry
            actual_value = RulesEngine._get_claim_field(claim, condition.field)
            
            trace_entry = EvaluationConditionTrace(
                condition=RulesEngine._format_condition(condition),
                actual_value=actual_value,
                result=matched
            )
            trace.append(trace_entry)
            
            # Short-circuit: if any condition fails, rule doesn't match
            if not matched:
                all_match = False
        
        return all_match, trace
    
    @staticmethod
    def _evaluate_condition(claim: ClaimRecord, condition: Condition) -> bool:
        """Evaluate a single condition against a claim."""
        actual_value = RulesEngine._get_claim_field(claim, condition.field)
        
        # Handle missing fields
        if actual_value is None:
            # For equals/contains operators, None doesn't match
            # For not_equals, None does match
            if condition.operator == "not_equals":
                return True
            return False
        
        operator = condition.operator
        expected = condition.value
        
        if operator == "equals":
            if isinstance(actual_value, str):
                return actual_value.lower() == str(expected).lower()
            return actual_value == expected
        
        elif operator == "not_equals":
            if isinstance(actual_value, str):
                return actual_value.lower() != str(expected).lower()
            return actual_value != expected
        
        elif operator == "less_than":
            try:
                return float(actual_value) < float(expected)
            except (ValueError, TypeError):
                return False
        
        elif operator == "greater_than":
            try:
                return float(actual_value) > float(expected)
            except (ValueError, TypeError):
                return False
        
        elif operator == "less_than_or_equal":
            try:
                return float(actual_value) <= float(expected)
            except (ValueError, TypeError):
                return False
        
        elif operator == "greater_than_or_equal":
            try:
                return float(actual_value) >= float(expected)
            except (ValueError, TypeError):
                return False
        
        elif operator == "contains":
            return str(expected).lower() in str(actual_value).lower()
        
        return False
    
    @staticmethod
    def _get_claim_field(claim: ClaimRecord, field: str) -> Any:
        """Get a field value from a claim."""
        field_map = {
            "amount": claim.amount,
            "department": claim.department,
            "category": claim.category,
            "employee": claim.employee,
            "location": getattr(claim, "location", None),
            "currency": claim.currency,
            "date": claim.date,
            "employee_level": getattr(claim, "employee_level", None),
        }
        return field_map.get(field)
    
    @staticmethod
    def _format_condition(condition: Condition) -> str:
        """Format a condition as a human-readable string."""
        op_text = condition.operator.replace("_", " ")
        return f"{condition.field} {op_text} {condition.value}"
    
    @staticmethod
    def _resolve_winner(
        matched_rule_evals: List[Tuple[RuleRecord, List[EvaluationConditionTrace]]]
    ) -> Tuple[RuleRecord, List[EvaluationConditionTrace]]:
        """
        Resolve which rule wins when multiple rules match.
        
        Strategy:
        1. By decision precedence (REJECT > ESCALATE > APPROVE)
        2. By priority (higher priority wins)
        3. By rule ID (earlier rule wins)
        """
        # Sort by decision precedence first
        sorted_rules = sorted(
            matched_rule_evals,
            key=lambda x: (
                RulesEngine.DECISION_PRECEDENCE.get(x[0].decision, 999),
                -x[0].priority,  # Higher priority first
                x[0].id  # Earlier ID first
            )
        )
        
        return sorted_rules[0]
    
    @staticmethod
    def _generate_rationale(
        claim: ClaimRecord,
        winning_rule: RuleRecord,
        all_matched: List[Tuple[RuleRecord, List[EvaluationConditionTrace]]],
        winning_trace: List[EvaluationConditionTrace]
    ) -> str:
        """Generate a human-readable rationale for the decision."""
        rationale = f"Decision: {winning_rule.decision}\n\n"
        rationale += f"Winning Rule:\n\"{winning_rule.name}\"\n\n"
        
        rationale += "Rule Decision: " + winning_rule.decision + "\n"
        rationale += "Rule Priority: " + str(winning_rule.priority) + "\n\n"
        
        rationale += "Evaluated Conditions:\n"
        for trace in winning_trace:
            result_text = "✓ True" if trace.result else "✗ False"
            rationale += f"  {result_text}: {trace.condition} (value: {trace.actual_value})\n"
        
        if len(all_matched) > 1:
            other_matches = [r for r, _ in all_matched if r.id != winning_rule.id]
            if other_matches:
                rationale += f"\nOther Matched Rules (not selected):\n"
                for rule in other_matches:
                    rationale += f"  - {rule.name} (Decision: {rule.decision}, Priority: {rule.priority})\n"
        
        return rationale
