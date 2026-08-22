"""
Schemas for API requests and responses using dataclasses.
Uses dataclasses instead of Pydantic due to Python 3.14 compatibility.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Any, Dict, Optional
from datetime import datetime
import json


# Condition schema for structured rules
@dataclass
class Condition:
    field: str
    operator: str
    value: Any
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class StructuredRule:
    conditions: List[Condition]
    decision: str
    
    def to_dict(self):
        return {
            'conditions': [c.to_dict() if isinstance(c, Condition) else c for c in self.conditions],
            'decision': self.decision
        }
    
    @classmethod
    def from_dict(cls, data):
        conditions = [Condition.from_dict(c) if isinstance(c, dict) else c for c in data.get('conditions', [])]
        return cls(conditions=conditions, decision=data.get('decision', ''))


# Rule schemas
@dataclass
class RuleCreate:
    natural_language: str
    priority: int = 50


@dataclass
class RuleUpdate:
    priority: Optional[int] = None
    status: Optional[str] = None


@dataclass
class RuleResponse:
    id: int
    name: str
    natural_language: str
    structured_rule: Dict[str, Any]
    decision: str
    priority: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'natural_language': self.natural_language,
            'structured_rule': self.structured_rule,
            'decision': self.decision,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }


# Claim schemas
@dataclass
class ClaimCreate:
    id: str
    employee: str
    category: str
    amount: float
    date: str
    description: str
    department: Optional[str] = None
    currency: str = 'USD'


@dataclass
class ClaimResponse:
    id: str
    employee: str
    category: str
    amount: float
    date: str
    description: str
    created_at: datetime
    department: Optional[str] = None
    currency: str = 'USD'
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee': self.employee,
            'department': self.department,
            'category': self.category,
            'amount': self.amount,
            'currency': self.currency,
            'date': self.date,
            'description': self.description,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }


# Evaluation schemas
@dataclass
class EvaluationConditionTrace:
    condition: str
    actual_value: Any
    result: bool


@dataclass
class MatchedRuleInfo:
    rule_id: int
    rule_name: str
    decision: str
    priority: int


@dataclass
class EvaluationResponse:
    claim_id: str
    decision: str
    rationale: str
    evaluation_trace: List[EvaluationConditionTrace]
    matched_rules: List[MatchedRuleInfo]
    timestamp: datetime
    winning_rule_id: Optional[int] = None
    winning_rule_name: Optional[str] = None
    
    def to_dict(self):
        return {
            'claim_id': self.claim_id,
            'decision': self.decision,
            'winning_rule_id': self.winning_rule_id,
            'winning_rule_name': self.winning_rule_name,
            'rationale': self.rationale,
            'evaluation_trace': [asdict(t) for t in self.evaluation_trace],
            'matched_rules': [asdict(m) for m in self.matched_rules],
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
        }


# Dashboard schema
@dataclass
class DashboardStats:
    total_claims: int
    total_rules: int
    active_rules: int
    total_evaluations: int
    decision_distribution: Dict[str, int]
    recent_evaluations: List[EvaluationResponse]
    
    def to_dict(self):
        return {
            'total_claims': self.total_claims,
            'total_rules': self.total_rules,
            'active_rules': self.active_rules,
            'total_evaluations': self.total_evaluations,
            'decision_distribution': self.decision_distribution,
            'recent_evaluations': [e.to_dict() for e in self.recent_evaluations],
        }

