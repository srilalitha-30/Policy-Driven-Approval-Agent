from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Rule(Base):
    """Approval rule stored in database."""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    natural_language = Column(Text, nullable=False)
    structured_rule = Column(JSON, nullable=False)
    decision = Column(String, nullable=False)  # APPROVE, REJECT, ESCALATE
    priority = Column(Integer, default=50)
    status = Column(String, default="active")  # active, inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Claim(Base):
    """Expense claim to be evaluated."""
    __tablename__ = "claims"
    
    id = Column(String, primary_key=True, index=True)
    employee = Column(String, nullable=False)
    department = Column(String, nullable=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    date = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Evaluation(Base):
    """Result of evaluating a claim against rules."""
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, index=True, nullable=False)
    decision = Column(String, nullable=False)  # APPROVE, REJECT, ESCALATE
    winning_rule_id = Column(Integer, nullable=True)
    winning_rule_name = Column(String, nullable=True)
    rationale = Column(Text, nullable=False)
    evaluation_trace = Column(JSON, nullable=False)
    matched_rules = Column(JSON, nullable=False)  # List of all matched rules
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
