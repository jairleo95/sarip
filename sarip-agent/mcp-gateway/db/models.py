from sqlalchemy import Column, Integer, String, Float, DateTime
from db.database import Base
from datetime import datetime

class PayoutTransaction(Base):
    """
    Mock table representing a transaction in the core banking system.
    """
    __tablename__ = "payout_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    account_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(String, nullable=False) # e.g. AUTHORIZED, SETTLED, FAILED_NSF, TIMEOUT
    service_company = Column(String, nullable=False) # e.g. Claro, AguaCorp
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
