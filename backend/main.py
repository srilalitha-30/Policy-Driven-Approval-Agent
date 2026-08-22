"""
Main FastAPI application for the Policy-Driven Approval Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.api import router as api_router

app = FastAPI(
    title="Policy-Driven Approval Agent",
    description="An intelligent system for evaluating expense claims against configurable business rules",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include API routes
app.include_router(api_router)

# Sample data initialization
def init_sample_data():
    """Initialize sample rules and claims for demonstration."""
    from app.database import SessionLocal
    from app.repositories import RuleRepository, ClaimRepository
    
    db = SessionLocal()
    
    try:
        # Check if we already have rules
        existing_rules = RuleRepository.get_all(db)
        if existing_rules:
            return
        
        # Create sample rules
        rules_data = [
            {
                "name": "Sales expenses under $500",
                "natural_language": "Auto-approve expenses under $500 for Sales.",
                "structured_rule": {
                    "conditions": [
                        {"field": "department", "operator": "equals", "value": "Sales"},
                        {"field": "amount", "operator": "less_than", "value": 500}
                    ],
                    "decision": "APPROVE"
                },
                "decision": "APPROVE",
                "priority": 50
            },
            {
                "name": "Meals under $100",
                "natural_language": "Auto-approve meals under $100 for any department.",
                "structured_rule": {
                    "conditions": [
                        {"field": "category", "operator": "equals", "value": "Meals"},
                        {"field": "amount", "operator": "less_than", "value": 100}
                    ],
                    "decision": "APPROVE"
                },
                "decision": "APPROVE",
                "priority": 40
            },
            {
                "name": "High value expenses",
                "natural_language": "Escalate expenses above $2,000.",
                "structured_rule": {
                    "conditions": [
                        {"field": "amount", "operator": "greater_than", "value": 2000}
                    ],
                    "decision": "ESCALATE"
                },
                "decision": "ESCALATE",
                "priority": 80
            },
            {
                "name": "Very high value expenses",
                "natural_language": "Reject expenses above $5,000 unless the department is Finance.",
                "structured_rule": {
                    "conditions": [
                        {"field": "amount", "operator": "greater_than", "value": 5000},
                        {"field": "department", "operator": "not_equals", "value": "Finance"}
                    ],
                    "decision": "REJECT"
                },
                "decision": "REJECT",
                "priority": 100
            }
        ]
        
        for rule_data in rules_data:
            RuleRepository.create(
                db,
                name=rule_data["name"],
                natural_language=rule_data["natural_language"],
                structured_rule=rule_data["structured_rule"],
                decision=rule_data["decision"],
                priority=rule_data["priority"]
            )
        
        # Create sample claims
        claims_data = [
            {
                "id": "EXP-001",
                "employee": "Alice Johnson",
                "department": "Sales",
                "category": "Travel",
                "amount": 350.00,
                "currency": "USD",
                "date": "2026-08-20",
                "description": "Client meeting travel"
            },
            {
                "id": "EXP-002",
                "employee": "Bob Smith",
                "department": "Engineering",
                "category": "Software",
                "amount": 2500.00,
                "currency": "USD",
                "date": "2026-08-21",
                "description": "Software licenses"
            },
            {
                "id": "EXP-003",
                "employee": "Charlie Brown",
                "department": "Marketing",
                "category": "Equipment",
                "amount": 6000.00,
                "currency": "USD",
                "date": "2026-08-22",
                "description": "New workstation equipment"
            },
            {
                "id": "EXP-004",
                "employee": "Diana Prince",
                "department": "Finance",
                "category": "Equipment",
                "amount": 6500.00,
                "currency": "USD",
                "date": "2026-08-23",
                "description": "Server equipment"
            },
            {
                "id": "EXP-005",
                "employee": "Edward Wilson",
                "department": "Sales",
                "category": "Travel",
                "amount": 500.00,
                "currency": "USD",
                "date": "2026-08-24",
                "description": "Boundary value test"
            },
            {
                "id": "EXP-006",
                "employee": "Fiona Green",
                "department": "Engineering",
                "category": "Meals",
                "amount": 75.00,
                "currency": "USD",
                "date": "2026-08-25",
                "description": "Team lunch"
            },
            {
                "id": "EXP-007",
                "employee": "George Miller",
                "department": None,
                "category": "Travel",
                "amount": 300.00,
                "currency": "USD",
                "date": "2026-08-26",
                "description": "Missing department test"
            }
        ]
        
        for claim_data in claims_data:
            from app.schemas import ClaimCreate
            ClaimRepository.create(db, ClaimCreate(**claim_data))
        
        print("✓ Sample data initialized")
    
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    init_sample_data()
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )
