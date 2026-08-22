"""
Tests for the rules engine and evaluation logic.
"""

import pytest
from app.services.rule_parser import RuleParser, RuleValidator, RuleParsingError
from app.services.rules_engine import RulesEngine, RuleRecord, ClaimRecord
from app.schemas import Condition, StructuredRule


class TestRuleParser:
    """Tests for rule parsing."""
    
    def test_parse_basic_approval_rule(self):
        """Test parsing a basic approval rule."""
        text = "Auto-approve expenses under $500 for Sales."
        name, structured = RuleParser.parse(text)
        
        assert name == text
        assert structured.decision == "APPROVE"
        assert len(structured.conditions) >= 1
    
    def test_parse_escalation_rule(self):
        """Test parsing an escalation rule."""
        text = "Escalate expenses above $2,000."
        name, structured = RuleParser.parse(text)
        
        assert structured.decision == "ESCALATE"
    
    def test_parse_rejection_rule(self):
        """Test parsing a rejection rule."""
        text = "Reject expenses above $5,000."
        name, structured = RuleParser.parse(text)
        
        assert structured.decision == "REJECT"
    
    def test_parse_invalid_rule_no_decision(self):
        """Test parsing fails when no decision can be determined."""
        text = "Something about expenses."
        with pytest.raises(RuleParsingError):
            RuleParser.parse(text)
    
    def test_extract_amount_condition(self):
        """Test extracting amount conditions."""
        text = "amount less than 500"
        conditions = RuleParser._extract_conditions(text)
        
        amount_condition = next((c for c in conditions if c.field == "amount"), None)
        assert amount_condition is not None
        assert amount_condition.operator == "less_than"
        assert amount_condition.value == 500.0
    
    def test_extract_department_condition(self):
        """Test extracting department conditions."""
        text = "for Sales"
        conditions = RuleParser._extract_conditions(text)
        
        dept_condition = next((c for c in conditions if c.field == "department"), None)
        assert dept_condition is not None
        assert dept_condition.value == "Sales"


class TestRuleValidator:
    """Tests for rule validation."""
    
    def test_validate_valid_rule(self):
        """Test validation of a valid rule."""
        rule = StructuredRule(
            conditions=[
                Condition(field="amount", operator="less_than", value=500)
            ],
            decision="APPROVE"
        )
        
        errors = RuleValidator.validate("Test Rule", rule, 50)
        assert len(errors) == 0
    
    def test_validate_invalid_field(self):
        """Test validation fails for invalid field."""
        rule = StructuredRule(
            conditions=[
                Condition(field="invalid_field", operator="equals", value="test")
            ],
            decision="APPROVE"
        )
        
        errors = RuleValidator.validate("Test Rule", rule, 50)
        assert len(errors) > 0
        assert "invalid_field" in str(errors)
    
    def test_validate_invalid_operator(self):
        """Test validation fails for invalid operator."""
        rule = StructuredRule(
            conditions=[
                Condition(field="amount", operator="invalid_op", value=500)
            ],
            decision="APPROVE"
        )
        
        errors = RuleValidator.validate("Test Rule", rule, 50)
        assert len(errors) > 0
    
    def test_validate_negative_amount(self):
        """Test validation fails for negative amount."""
        rule = StructuredRule(
            conditions=[
                Condition(field="amount", operator="less_than", value=-500)
            ],
            decision="APPROVE"
        )
        
        errors = RuleValidator.validate("Test Rule", rule, 50)
        assert len(errors) > 0
    
    def test_validate_invalid_priority(self):
        """Test validation fails for invalid priority."""
        rule = StructuredRule(
            conditions=[
                Condition(field="amount", operator="less_than", value=500)
            ],
            decision="APPROVE"
        )
        
        errors = RuleValidator.validate("Test Rule", rule, 150)
        assert len(errors) > 0


class TestRulesEngine:
    """Tests for the rules engine evaluation logic."""
    
    def test_evaluate_claim_single_matching_rule(self):
        """Test evaluating a claim with a single matching rule."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department="Sales",
            category="Travel",
            amount=350,
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule = RuleRecord(
            id=1,
            name="Sales under $500",
            structured_rule={
                "conditions": [
                    {"field": "department", "operator": "equals", "value": "Sales"},
                    {"field": "amount", "operator": "less_than", "value": 500}
                ],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=50,
            status="active"
        )
        
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule])
        
        assert decision == "APPROVE"
        assert winning_id == 1
        assert len(trace) == 2  # Two conditions checked
        assert all(t.result for t in trace)  # All should pass
    
    def test_evaluate_claim_no_matching_rules(self):
        """Test evaluating a claim with no matching rules."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department="Unknown",
            category="Travel",
            amount=350,
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule = RuleRecord(
            id=1,
            name="Sales under $500",
            structured_rule={
                "conditions": [
                    {"field": "department", "operator": "equals", "value": "Sales"},
                    {"field": "amount", "operator": "less_than", "value": 500}
                ],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=50,
            status="active"
        )
        
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule])
        
        assert decision == "ESCALATE"  # Escalate when no rule matches
        assert winning_id is None
    
    def test_evaluate_claim_missing_required_field(self):
        """Test evaluating a claim with missing department."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department=None,  # Missing
            category="Travel",
            amount=350,
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule = RuleRecord(
            id=1,
            name="Sales under $500",
            structured_rule={
                "conditions": [
                    {"field": "department", "operator": "equals", "value": "Sales"},
                    {"field": "amount", "operator": "less_than", "value": 500}
                ],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=50,
            status="active"
        )
        
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule])
        
        assert decision == "ESCALATE"  # Escalate when required field is missing
    
    def test_evaluate_claim_boundary_value_less_than(self):
        """Test boundary value with less_than operator."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department="Sales",
            category="Travel",
            amount=500,  # Exactly at boundary
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule = RuleRecord(
            id=1,
            name="Sales under $500",
            structured_rule={
                "conditions": [
                    {"field": "amount", "operator": "less_than", "value": 500}
                ],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=50,
            status="active"
        )
        
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule])
        
        # amount=500 is NOT less than 500, so should not match
        assert decision == "ESCALATE"
        assert trace[0].result == False
    
    def test_evaluate_claim_multiple_matching_rules_priority(self):
        """Test rule priority when multiple rules match."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department="Sales",
            category="Travel",
            amount=350,
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule1 = RuleRecord(
            id=1,
            name="Sales under $500",
            structured_rule={
                "conditions": [{"field": "amount", "operator": "less_than", "value": 500}],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=30,
            status="active"
        )
        
        rule2 = RuleRecord(
            id=2,
            name="Escalate all",
            structured_rule={
                "conditions": [{"field": "amount", "operator": "greater_than", "value": 0}],
                "decision": "ESCALATE"
            },
            decision="ESCALATE",
            priority=80,
            status="active"
        )
        
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule1, rule2])
        
        # ESCALATE decision should win over APPROVE due to decision precedence
        assert decision == "ESCALATE"
        assert winning_id == 2
    
    def test_evaluate_claim_negative_amount(self):
        """Test handling of invalid negative amount."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department="Sales",
            category="Travel",
            amount=-100,  # Invalid
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule = RuleRecord(
            id=1,
            name="Sales",
            structured_rule={
                "conditions": [{"field": "amount", "operator": "less_than", "value": 500}],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=50,
            status="active"
        )
        
        # Should still evaluate
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule])
        
        # Negative amounts technically match "less than 500"
        assert decision == "APPROVE"
    
    def test_inactive_rules_not_evaluated(self):
        """Test that inactive rules are not evaluated."""
        claim = ClaimRecord(
            id="EXP-001",
            employee="Alice",
            department="Sales",
            category="Travel",
            amount=350,
            currency="USD",
            date="2026-08-20",
            description="Test"
        )
        
        rule = RuleRecord(
            id=1,
            name="Sales under $500",
            structured_rule={
                "conditions": [
                    {"field": "department", "operator": "equals", "value": "Sales"},
                    {"field": "amount", "operator": "less_than", "value": 500}
                ],
                "decision": "APPROVE"
            },
            decision="APPROVE",
            priority=50,
            status="inactive"  # Inactive
        )
        
        decision, winning_id, rationale, trace, matched = RulesEngine.evaluate_claim(claim, [rule])
        
        # Should escalate because no active rules
        assert decision == "ESCALATE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
