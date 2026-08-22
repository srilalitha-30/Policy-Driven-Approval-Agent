"""
Repository layer for data access.
"""

from sqlalchemy.orm import Session
from app.database import Rule, Claim, Evaluation
from app.schemas import RuleCreate, ClaimCreate


class RuleRepository:
    """Data access for rules."""
    
    @staticmethod
    def create(db: Session, name: str, natural_language: str, structured_rule: dict, decision: str, priority: int) -> Rule:
        """Create a new rule."""
        db_rule = Rule(
            name=name,
            natural_language=natural_language,
            structured_rule=structured_rule,
            decision=decision,
            priority=priority,
            status="active"
        )
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    
    @staticmethod
    def get_all(db: Session) -> list:
        """Get all rules."""
        return db.query(Rule).all()
    
    @staticmethod
    def get_by_id(db: Session, rule_id: int) -> Rule:
        """Get a rule by ID."""
        return db.query(Rule).filter(Rule.id == rule_id).first()
    
    @staticmethod
    def update(db: Session, rule_id: int, priority: int = None, status: str = None) -> Rule:
        """Update a rule."""
        db_rule = RuleRepository.get_by_id(db, rule_id)
        if not db_rule:
            return None
        
        if priority is not None:
            db_rule.priority = priority
        if status is not None:
            db_rule.status = status
        
        db.commit()
        db.refresh(db_rule)
        return db_rule
    
    @staticmethod
    def delete(db: Session, rule_id: int) -> bool:
        """Delete a rule."""
        db_rule = RuleRepository.get_by_id(db, rule_id)
        if not db_rule:
            return False
        
        db.delete(db_rule)
        db.commit()
        return True


class ClaimRepository:
    """Data access for claims."""
    
    @staticmethod
    def create(db: Session, claim: ClaimCreate) -> Claim:
        """Create a new claim."""
        db_claim = Claim(
            id=claim.id,
            employee=claim.employee,
            department=claim.department,
            category=claim.category,
            amount=claim.amount,
            currency=claim.currency,
            date=claim.date,
            description=claim.description
        )
        db.add(db_claim)
        db.commit()
        db.refresh(db_claim)
        return db_claim
    
    @staticmethod
    def get_all(db: Session) -> list:
        """Get all claims."""
        return db.query(Claim).all()
    
    @staticmethod
    def get_by_id(db: Session, claim_id: str) -> Claim:
        """Get a claim by ID."""
        return db.query(Claim).filter(Claim.id == claim_id).first()


class EvaluationRepository:
    """Data access for evaluations."""
    
    @staticmethod
    def create(db: Session, claim_id: str, decision: str, winning_rule_id: int, 
               winning_rule_name: str, rationale: str, evaluation_trace: list, matched_rules: list) -> Evaluation:
        """Create a new evaluation."""
        db_eval = Evaluation(
            claim_id=claim_id,
            decision=decision,
            winning_rule_id=winning_rule_id,
            winning_rule_name=winning_rule_name,
            rationale=rationale,
            evaluation_trace=evaluation_trace,
            matched_rules=matched_rules
        )
        db.add(db_eval)
        db.commit()
        db.refresh(db_eval)
        return db_eval
    
    @staticmethod
    def get_by_claim_id(db: Session, claim_id: str) -> Evaluation:
        """Get evaluation for a claim."""
        return db.query(Evaluation).filter(Evaluation.claim_id == claim_id).first()
    
    @staticmethod
    def get_all(db: Session) -> list:
        """Get all evaluations."""
        return db.query(Evaluation).all()
    
    @staticmethod
    def get_summary(db: Session) -> dict:
        """Get evaluation summary statistics."""
        evals = EvaluationRepository.get_all(db)
        summary = {"APPROVE": 0, "REJECT": 0, "ESCALATE": 0}
        for eval in evals:
            summary[eval.decision] = summary.get(eval.decision, 0) + 1
        return summary
