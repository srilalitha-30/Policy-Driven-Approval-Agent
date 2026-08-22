# Quick Start Guide

## Running the Application

### 1. Start the Backend

```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The API will be available at: **http://localhost:8001**

### 2. Test the API

#### Check Health
```bash
curl http://localhost:8001/health
```

#### List Rules
```bash
curl http://localhost:8001/rules | python3 -m json.tool
```

#### Create a Claim
```bash
curl -X POST http://localhost:8001/claims \
  -H "Content-Type: application/json" \
  -d '{
    "id": "DEMO-001",
    "employee": "John Smith",
    "department": "Sales",
    "category": "Travel",
    "amount": 350,
    "currency": "USD",
    "date": "2026-08-22",
    "description": "Flight to client meeting"
  }'
```

#### Evaluate a Claim
```bash
curl -X POST http://localhost:8001/evaluate/DEMO-001 | python3 -m json.tool
```

#### View Dashboard Stats
```bash
curl http://localhost:8001/dashboard | python3 -m json.tool
```

### 3. Start the Frontend (Optional)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

The dashboard will open at: **http://localhost:3000**

## Example API Responses

### Evaluation Response
```json
{
  "decision": "APPROVE",
  "winning_rule_id": 1,
  "winning_rule_name": "Sales expenses under $500",
  "rationale": "Decision: APPROVE\n\nWinning Rule:\n\"Sales expenses under $500\"\n\nRule Decision: APPROVE\nRule Priority: 50\n\nEvaluated Conditions:\n  ✓ True: department equals Sales\n  ✓ True: amount less than 500\n",
  "evaluation_trace": [
    {
      "condition": "department equals Sales",
      "actual_value": "Sales",
      "result": true
    },
    {
      "condition": "amount less than 500",
      "actual_value": 350.0,
      "result": true
    }
  ],
  "matched_rules": [
    {
      "rule_id": 1,
      "rule_name": "Sales expenses under $500",
      "decision": "APPROVE",
      "priority": 50
    }
  ]
}
```

## Sample Rules Included

1. **Sales expenses under $500** - Auto-approve Sales department expenses under $500
2. **Meals under $100** - Auto-approve meal category expenses under $100
3. **High value expenses** - Escalate any expenses above $2,000
4. **Large expenses not for Finance** - Reject expenses above $5,000 unless for Finance

## Key Features Demonstrated

✅ **Plain-English Rule Parsing** - Rules are written in natural language  
✅ **Deterministic Evaluation** - Every decision is reproducible and auditable  
✅ **Complete Traceability** - Rationale includes matched rules and condition evaluations  
✅ **Priority Resolution** - Multiple matching rules resolved by precedence and priority  

## Architecture

```
Request
  ↓
FastAPI (REST API)
  ↓
Rules Engine
  ↓
Rule Parser → Rule Validator
  ↓
SQLite Database
  ↓
Response (JSON)
```

## Troubleshooting

**Port 8001 already in use?**
```bash
# Change the port in backend/app/config.py or use environment variable:
API_PORT=8002 python main.py
```

**Database not initializing?**
```bash
# Delete the database and restart:
rm approval_agent.db
python main.py
```

**Import errors?**
```bash
# Reinstall dependencies:
pip install --force-reinstall -r requirements.txt
```
