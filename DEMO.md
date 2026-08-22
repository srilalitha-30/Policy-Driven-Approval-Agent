# 5-Minute Demo Walkthrough

## Overview

This document guides you through a complete 5-minute demonstration of the Policy-Driven Approval Agent.

## Prerequisites

- Backend running on http://localhost:8000
- Optional: Frontend running on http://localhost:3000

## Demo Script (5 Minutes)

### Segment 1: System Overview (0:00-0:45)

**Talking Points:**
- Enterprise expense approval is manual, error-prone, and inconsistent
- Rules are hardcoded, making changes slow
- We built a system that automates this using plain-English rules

**Show:**
```bash
# Check system health
curl http://localhost:8000/health
# Shows: {"status":"healthy"}
```

**UI (if available):**
Navigate to http://localhost:3000/dashboard
- Show the dashboard with stats
- Display total claims, rules, active rules
- Mention that we have 4 pre-configured rules

### Segment 2: View Rules (0:45-1:30)

**Talking Points:**
- Rules are written in plain English, not code
- The system automatically parses them into structured rules
- Rules have priorities and can be toggled active/inactive

**Demo:**
```bash
# List all rules
curl http://localhost:8000/rules | python3 -m json.tool | head -80
```

**Show these rules:**
1. "Auto-approve expenses under $500 for Sales" - Priority 50
2. "Auto-approve meals under $100" - Priority 40
3. "Escalate expenses above $2,000" - Priority 30
4. "Reject large expenses not for Finance" - Priority 20

**Key Point:** Notice the structured conditions:
- Department equals "Sales"
- Amount less than 500
- Category equals "Meals"

### Segment 3: Create and Evaluate a Claim (1:30-3:00)

**Talking Points:**
- Let's create a real expense claim
- The system will automatically match it against rules
- You'll see which rule won, why it won, and a full audit trail

**Demo 1: Approval Case**
```bash
# Create a claim: Sales employee, $300 travel expense
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "id": "DEMO-APPROVE-001",
    "employee": "Alice Johnson",
    "department": "Sales",
    "category": "Travel",
    "amount": 300,
    "currency": "USD",
    "date": "2026-08-22",
    "description": "Flight to client meeting in New York"
  }'

# Evaluate the claim
curl -X POST http://localhost:8000/evaluate/DEMO-APPROVE-001 | python3 -m json.tool
```

**Show in response:**
- `"decision": "APPROVE"`
- `"winning_rule_name": "Sales expenses under $500"`
- Rationale explaining the decision
- Evaluation trace showing both conditions matched:
  - ✓ department equals Sales (value: Sales)
  - ✓ amount less than 500 (value: 300.0)

**Demo 2: Escalation Case**
```bash
# Create a claim: Large expense requiring escalation
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "id": "DEMO-ESCALATE-001",
    "employee": "Bob Smith",
    "department": "Marketing",
    "category": "Conference",
    "amount": 2500,
    "currency": "USD",
    "date": "2026-08-22",
    "description": "Annual marketing conference registration"
  }'

# Evaluate
curl -X POST http://localhost:8000/evaluate/DEMO-ESCALATE-001 | python3 -m json.tool
```

**Show in response:**
- `"decision": "ESCALATE"`
- `"winning_rule_name": "High value expenses"`
- Rationale: "Amount exceeds $2,000 - requires management approval"

**Demo 3: Rejection Case (Optional)**
```bash
# Create a very large expense for non-Finance department
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "id": "DEMO-REJECT-001",
    "employee": "Carol White",
    "department": "Sales",
    "category": "Other",
    "amount": 6000,
    "currency": "USD",
    "date": "2026-08-22",
    "description": "Office equipment"
  }'

# Evaluate
curl -X POST http://localhost:8000/evaluate/DEMO-REJECT-001 | python3 -m json.tool
```

**Show in response:**
- `"decision": "REJECT"`
- `"winning_rule_name": "Large expenses not for Finance"`
- Rationale explaining rejection

### Segment 4: Key Features (3:00-4:30)

**Talking Points:** (While showing dashboard or API)

**1. Deterministic Evaluation**
- Same claim, same rules = same decision
- Reproducible and auditable

**2. Complete Traceability**
- Every decision has a rationale
- Can see which rule "won" among multiple matches
- Condition-by-condition evaluation trace

**3. Priority Resolution**
- Multiple rules can match the same claim
- Precedence: REJECT > ESCALATE > APPROVE
- Then sorted by priority number

**4. Configurable Without Code**
- Add rules via plain English
- Change priorities dynamically
- Activate/deactivate rules

**Show Dashboard:**
```bash
curl http://localhost:8000/dashboard | python3 -m json.tool
```

Display:
- Total claims: 3 (from demos)
- Total rules: 4 (pre-configured)
- Active rules: 4
- Total evaluations: 3
- Decision distribution: 1 APPROVE, 1 ESCALATE, 1 REJECT

### Segment 5: Architecture & Conclusion (4:30-5:00)

**Talking Points:**

**Architecture:**
- React Frontend (UI for non-technical users)
- FastAPI (REST API for programmatic access)
- Rule Parser (Natural language → Structured rules)
- Rules Engine (Deterministic evaluation)
- SQLite Database (Persistent storage)

**Benefits:**
- ✅ Reduces approval time from days to seconds
- ✅ Eliminates manual errors
- ✅ Provides full audit trail for compliance
- ✅ Configurable without developer intervention
- ✅ Scales to thousands of claims

**Conclusion:**
"This system transforms expense approval from a bottleneck into an automated, auditable process."

## Alternative: UI Walkthrough (If Running Frontend)

If you have the React frontend running, navigate to:
- http://localhost:3000/dashboard
- http://localhost:3000/rules
- http://localhost:3000/claims

Show the same demo claims being created and evaluated through the UI:
1. Create a claim in the form
2. See it appear in the claims list
3. Click evaluate
4. See the full decision details

## Key Points to Emphasize

1. **Plain English Rules** - No coding required
2. **Instant Decisions** - From hours to milliseconds
3. **Full Audit Trail** - Compliance ready
4. **Non-Technical UI** - Business users can manage rules
5. **Scalable** - Can evaluate thousands of claims

## Handling Questions

**Q: What if I want different rules?**
A: You can add or modify rules via the API using plain English. Rules are not hardcoded.

**Q: How does it handle edge cases?**
A: It gracefully handles missing fields (escalates), boundary values (properly compared), and conflicting rules (uses precedence and priority).

**Q: Can it integrate with our existing system?**
A: Yes, it's a REST API. Any system can call it via HTTP requests.

**Q: What about performance?**
A: Evaluations are instant (milliseconds) and the system is designed to scale to enterprise volumes.

**Q: Is it open source?**
A: Yes, the complete source code is available on GitHub.

## Files for Reference

- **README.md** - Full documentation
- **QUICK_START.md** - Setup instructions
- **DEPLOYMENT.md** - Production deployment guide
- **API Endpoints** - Documented at http://localhost:8000/docs (auto-generated)

---

**Total Demo Time: ~5 minutes**  
**Key Takeaway:** The Policy-Driven Approval Agent automates enterprise expense approval with full traceability and configurability.
