"""
Rule Parser: Converts plain-English rules into structured rules.

This module is responsible for interpreting natural-language rules
and converting them into a structured format that can be validated
and executed by the rules engine.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from app.schemas import Condition, StructuredRule


# Mapping of plain-English operators to structured operators
OPERATOR_MAPPING = {
    # Comparison operators
    "less than": "less_than",
    "<": "less_than",
    "greater than": "greater_than",
    ">": "greater_than",
    "equals": "equals",
    "equal to": "equals",
    "=": "equals",
    "not equal": "not_equals",
    "not equals": "not_equals",
    "!=": "not_equals",
    "less than or equal": "less_than_or_equal",
    "<=": "less_than_or_equal",
    "greater than or equal": "greater_than_or_equal",
    ">=": "greater_than_or_equal",
    # String operators
    "contains": "contains",
    "includes": "contains",
    "is": "equals",
    "is not": "not_equals",
}

# Mapping of plain-English field names to structured field names
FIELD_MAPPING = {
    "amount": "amount",
    "expense": "amount",
    "department": "department",
    "category": "category",
    "employee": "employee",
    "employee level": "employee_level",
    "level": "employee_level",
    "location": "location",
    "currency": "currency",
    "date": "date",
    "type": "category",
    "expense type": "category",
}

# Valid decisions
VALID_DECISIONS = {"APPROVE", "REJECT", "ESCALATE"}


class RuleParsingError(Exception):
    """Raised when a rule cannot be parsed."""
    pass


class RuleParser:
    """Parses plain-English rules into structured rules."""

    @staticmethod
    def parse(natural_language: str) -> Tuple[str, StructuredRule]:
        """
        Parse a natural-language rule.
        
        Args:
            natural_language: Plain-English rule description
            
        Returns:
            Tuple of (rule_name, structured_rule)
            
        Raises:
            RuleParsingError: If the rule cannot be parsed
        """
        rule_name = natural_language.strip()
        
        # Determine the decision
        decision = RuleParser._extract_decision(natural_language)
        if not decision:
            raise RuleParsingError(
                "Could not determine decision (APPROVE, REJECT, or ESCALATE) from rule"
            )
        
        # Extract conditions
        conditions = RuleParser._extract_conditions(natural_language)
        if not conditions and decision != "ESCALATE":
            raise RuleParsingError(
                "Could not extract any measurable conditions from rule"
            )
        
        structured = StructuredRule(
            conditions=conditions,
            decision=decision
        )
        
        return rule_name, structured

    @staticmethod
    def _extract_decision(text: str) -> Optional[str]:
        """Extract the decision (APPROVE, REJECT, ESCALATE) from text."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["auto-approve", "auto approve", "automatically approve", "approve"]):
            return "APPROVE"
        if any(w in text_lower for w in ["reject", "denied", "deny", "decline"]):
            return "REJECT"
        if any(w in text_lower for w in ["escalate", "escalated", "review", "manual review"]):
            return "ESCALATE"
        
        return None

    @staticmethod
    def _extract_conditions(text: str) -> List[Condition]:
        """Extract conditions from the rule text."""
        conditions = []
        
        # Pattern 1: "field operator value" (e.g., "amount less than 500")
        # Pattern 2: "field is value" (e.g., "department is Sales")
        
        # Handle specific patterns
        # Amount conditions
        amount_patterns = [
            (r"amount\s+(?:less than|<)\s+\$?([\d,]+)", "amount", "less_than"),
            (r"amount\s+(?:greater than|>)\s+\$?([\d,]+)", "amount", "greater_than"),
            (r"amount\s+(?:under|below)\s+\$?([\d,]+)", "amount", "less_than"),
            (r"amount\s+(?:over|above)\s+\$?([\d,]+)", "amount", "greater_than"),
            (r"amount\s+(?:equals?|is)\s+\$?([\d,]+)", "amount", "equals"),
        ]
        
        for pattern, field, operator in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(",", ""))
                conditions.append(Condition(field=field, operator=operator, value=value))
        
        # Department conditions
        dept_patterns = [
            r"(?:department|departments?)\s+(?:is|are|equals?|for)\s+([A-Za-z]+)",
            r"for\s+(?:the\s+)?([A-Za-z]+)\s+(?:department|team)",
            r"(?:department|departments?)\s+(?:is not|is not|!=|≠)\s+([A-Za-z]+)",
        ]
        
        for pattern in dept_patterns[:2]:  # Include positive matches
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                department = match.group(1).strip()
                # Check if it's an exclusion
                if "is not" in text[max(0, match.start()-10):match.end()]:
                    conditions.append(Condition(field="department", operator="not_equals", value=department))
                else:
                    conditions.append(Condition(field="department", operator="equals", value=department))
                break
        
        # Category conditions
        category_patterns = [
            r"(?:category|type|expense type)\s+(?:is|are|equals?)\s+([A-Za-z]+)",
            r"([A-Za-z]+)\s+(?:expenses?|meals)",
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                category = match.group(1).strip()
                conditions.append(Condition(field="category", operator="equals", value=category))
                break
        
        return conditions


class RuleValidator:
    """Validates structured rules."""
    
    # Supported fields
    SUPPORTED_FIELDS = {
        "amount", "department", "category", "employee", 
        "employee_level", "location", "currency", "date"
    }
    
    # Supported operators
    SUPPORTED_OPERATORS = {
        "equals", "not_equals", "less_than", "greater_than",
        "less_than_or_equal", "greater_than_or_equal", "contains"
    }
    
    # Supported decisions
    SUPPORTED_DECISIONS = {"APPROVE", "REJECT", "ESCALATE"}
    
    @staticmethod
    def validate(rule_name: str, structured_rule: StructuredRule, priority: int) -> List[str]:
        """
        Validate a structured rule.
        
        Args:
            rule_name: Human-readable rule name
            structured_rule: The structured rule to validate
            priority: Rule priority (0-100)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check decision
        if structured_rule.decision not in RuleValidator.SUPPORTED_DECISIONS:
            errors.append(
                f"Invalid decision '{structured_rule.decision}'. "
                f"Must be one of: {', '.join(RuleValidator.SUPPORTED_DECISIONS)}"
            )
        
        # Check priority
        if not isinstance(priority, int) or priority < 0 or priority > 100:
            errors.append("Priority must be an integer between 0 and 100")
        
        # Check conditions
        if not structured_rule.conditions and structured_rule.decision != "ESCALATE":
            errors.append("Rule must have at least one condition (unless decision is ESCALATE)")
        
        for i, condition in enumerate(structured_rule.conditions):
            field_errors = RuleValidator._validate_condition(condition, i)
            errors.extend(field_errors)
        
        return errors
    
    @staticmethod
    def _validate_condition(condition: Condition, index: int) -> List[str]:
        """Validate a single condition."""
        errors = []
        prefix = f"Condition {index + 1}: "
        
        if not condition.field:
            errors.append(f"{prefix}Field is required")
        elif condition.field not in RuleValidator.SUPPORTED_FIELDS:
            errors.append(
                f"{prefix}Field '{condition.field}' is not supported. "
                f"Supported fields: {', '.join(sorted(RuleValidator.SUPPORTED_FIELDS))}"
            )
        
        if not condition.operator:
            errors.append(f"{prefix}Operator is required")
        elif condition.operator not in RuleValidator.SUPPORTED_OPERATORS:
            errors.append(
                f"{prefix}Operator '{condition.operator}' is not supported. "
                f"Supported operators: {', '.join(sorted(RuleValidator.SUPPORTED_OPERATORS))}"
            )
        
        if condition.value is None:
            errors.append(f"{prefix}Value is required")
        
        # Type-specific validation
        if condition.field == "amount":
            if not isinstance(condition.value, (int, float)):
                errors.append(f"{prefix}Amount must be a number")
            elif condition.value < 0:
                errors.append(f"{prefix}Amount cannot be negative")
        
        return errors
