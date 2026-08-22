"""
REST API endpoints for the approval agent.
Uses dataclasses instead of Pydantic response_model for Python 3.14 compatibility.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    RuleCreate, RuleUpdate,
    ClaimCreate,
    DashboardStats
)
from app.services.rule_parser import RuleParser, RuleValidator, RuleParsingError
from app.services.rules_engine import RulesEngine, RuleRecord, ClaimRecord, EvaluationConditionTrace, MatchedRuleInfo
from app.repositories import RuleRepository, ClaimRepository, EvaluationRepository
from datetime import datetime

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ===== Rules Management =====

@router.post("/rules")
def create_rule(rule_req: RuleCreate, db: Session = Depends(get_db)):
    """
    Create a new approval rule from a natural-language description.
    
    Example:
        {
            "natural_language": "Auto-approve expenses under $500 for Sales.",
            "priority": 50
        }
    """
    try:
        # Parse the natural-language rule
        rule_name, structured_rule = RuleParser.parse(rule_req.natural_language)
        
        # Validate the structured rule
        errors = RuleValidator.validate(rule_name, structured_rule, rule_req.priority)
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"parsing_errors": errors}
            )
        
        # Create the rule
        db_rule = RuleRepository.create(
            db,
            name=rule_name,
            natural_language=rule_req.natural_language,
            structured_rule=structured_rule.to_dict(),
            decision=structured_rule.decision,
            priority=rule_req.priority
        )
        
        return {
            "id": db_rule.id,
            "name": db_rule.name,
            "natural_language": db_rule.natural_language,
            "structured_rule": db_rule.structured_rule,
            "decision": db_rule.decision,
            "priority": db_rule.priority,
            "status": db_rule.status,
            "created_at": db_rule.created_at.isoformat(),
            "updated_at": db_rule.updated_at.isoformat()
        }
    
    except RuleParsingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    """Get all configured rules."""
    rules = RuleRepository.get_all(db)
    return [
        {
            "id": r.id,
            "name": r.name,
            "natural_language": r.natural_language,
            "structured_rule": r.structured_rule,
            "decision": r.decision,
            "priority": r.priority,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat()
        }
        for r in rules
    ]


@router.get("/rules/{rule_id}")
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get a specific rule."""
    rule = RuleRepository.get_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {
        "id": rule.id,
        "name": rule.name,
        "natural_language": rule.natural_language,
        "structured_rule": rule.structured_rule,
        "decision": rule.decision,
        "priority": rule.priority,
        "status": rule.status,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat()
    }


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, update: RuleUpdate, db: Session = Depends(get_db)):
    """Update a rule's priority or status."""
    update_data = {}
    if update.priority is not None:
        update_data['priority'] = update.priority
    if update.status is not None:
        update_data['status'] = update.status
    
    rule = RuleRepository.update(db, rule_id, **update_data)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {
        "id": rule.id,
        "name": rule.name,
        "natural_language": rule.natural_language,
        "structured_rule": rule.structured_rule,
        "decision": rule.decision,
        "priority": rule.priority,
        "status": rule.status,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat()
    }


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a rule."""
    if not RuleRepository.delete(db, rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}


# ===== Claims Management =====

@router.post("/claims")
def create_claim(claim_req: ClaimCreate, db: Session = Depends(get_db)):
    """Create a new expense claim."""
    try:
        # Check if claim already exists
        existing = ClaimRepository.get_by_id(db, claim_req.id)
        if existing:
            raise HTTPException(status_code=409, detail="Claim already exists")
        
        db_claim = ClaimRepository.create(db, claim_req)
        return {
            "id": db_claim.id,
            "employee": db_claim.employee,
            "department": db_claim.department,
            "category": db_claim.category,
            "amount": db_claim.amount,
            "currency": db_claim.currency,
            "date": db_claim.date,
            "description": db_claim.description,
            "created_at": db_claim.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claims")
def list_claims(db: Session = Depends(get_db)):
    """Get all claims."""
    claims = ClaimRepository.get_all(db)
    return [
        {
            "id": c.id,
            "employee": c.employee,
            "department": c.department,
            "category": c.category,
            "amount": c.amount,
            "currency": c.currency,
            "date": c.date,
            "description": c.description,
            "created_at": c.created_at.isoformat()
        }
        for c in claims
    ]


@router.get("/claims/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Get a specific claim."""
    claim = ClaimRepository.get_by_id(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "id": claim.id,
        "employee": claim.employee,
        "department": claim.department,
        "category": claim.category,
        "amount": claim.amount,
        "currency": claim.currency,
        "date": claim.date,
        "description": claim.description,
        "created_at": claim.created_at.isoformat()
    }


# ===== Evaluation =====

@router.post("/evaluate/{claim_id}")
def evaluate_claim(claim_id: str, db: Session = Depends(get_db)):
    """
    Evaluate a single claim against all active rules.
    
    Returns:
        - decision: APPROVE, REJECT, or ESCALATE
        - winning_rule_id: The ID of the rule that determined the decision
        - rationale: Explanation of why this decision was made
        - evaluation_trace: Detailed trace of condition evaluations
    """
    try:
        # Get the claim
        db_claim = ClaimRepository.get_by_id(db, claim_id)
        if not db_claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Convert to ClaimRecord
        claim = ClaimRecord(
            id=db_claim.id,
            employee=db_claim.employee,
            department=db_claim.department,
            category=db_claim.category,
            amount=db_claim.amount,
            currency=db_claim.currency,
            date=db_claim.date,
            description=db_claim.description
        )
        
        # Get all active rules
        db_rules = RuleRepository.get_all(db)
        rules = [
            RuleRecord(
                id=r.id,
                name=r.name,
                structured_rule=r.structured_rule,
                decision=r.decision,
                priority=r.priority,
                status=r.status
            )
            for r in db_rules if r.status == "active"
        ]
        
        # Evaluate
        decision, winning_rule_id, rationale, trace, matched_rules = RulesEngine.evaluate_claim(claim, rules)
        
        # Save evaluation
        trace_data = [{"condition": t.condition, "actual_value": t.actual_value, "result": t.result} for t in trace]
        matched_data = [{"rule_id": m.rule_id, "rule_name": m.rule_name, "decision": m.decision, "priority": m.priority} for m in matched_rules]
        
        db_eval = EvaluationRepository.create(
            db,
            claim_id=claim_id,
            decision=decision,
            winning_rule_id=winning_rule_id,
            winning_rule_name=next((r.name for r in rules if r.id == winning_rule_id), None) if winning_rule_id else None,
            rationale=rationale,
            evaluation_trace=trace_data,
            matched_rules=matched_data
        )
        
        return {
            "id": db_eval.id,
            "claim_id": db_eval.claim_id,
            "decision": db_eval.decision,
            "winning_rule_id": db_eval.winning_rule_id,
            "winning_rule_name": db_eval.winning_rule_name,
            "rationale": db_eval.rationale,
            "evaluation_trace": db_eval.evaluation_trace,
            "matched_rules": db_eval.matched_rules,
            "timestamp": db_eval.timestamp.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations/{claim_id}")
def get_evaluation(claim_id: str, db: Session = Depends(get_db)):
    """Get the evaluation result for a claim."""
    evaluation = EvaluationRepository.get_by_claim_id(db, claim_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found for this claim")
    return {
        "id": evaluation.id,
        "claim_id": evaluation.claim_id,
        "decision": evaluation.decision,
        "winning_rule_id": evaluation.winning_rule_id,
        "winning_rule_name": evaluation.winning_rule_name,
        "rationale": evaluation.rationale,
        "evaluation_trace": evaluation.evaluation_trace,
        "matched_rules": evaluation.matched_rules,
        "timestamp": evaluation.timestamp.isoformat()
    }


@router.get("/evaluations")
def list_evaluations(db: Session = Depends(get_db)):
    """Get all evaluations."""
    evals = EvaluationRepository.get_all(db)
    return evals


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    rules = RuleRepository.get_all(db)
    claims = ClaimRepository.get_all(db)
    evals = EvaluationRepository.get_all(db)
    
    summary = {"APPROVE": 0, "REJECT": 0, "ESCALATE": 0}
    for eval in evals:
        summary[eval.decision] = summary.get(eval.decision, 0) + 1
    
    active_rules = len([r for r in rules if r.status == "active"])
    recent_evals = sorted(evals, key=lambda e: e.timestamp, reverse=True)[:5]
    
    return {
        "total_claims": len(claims),
        "total_rules": len(rules),
        "active_rules": active_rules,
        "total_evaluations": len(evals),
        "decision_distribution": summary,
        "recent_evaluations": [
            {
                "id": e.id,
                "claim_id": e.claim_id,
                "decision": e.decision,
                "winning_rule_id": e.winning_rule_id,
                "winning_rule_name": e.winning_rule_name,
                "rationale": e.rationale,
                "evaluation_trace": e.evaluation_trace,
                "matched_rules": e.matched_rules,
                "timestamp": e.timestamp.isoformat()
            }
            for e in recent_evals
        ]
    }
