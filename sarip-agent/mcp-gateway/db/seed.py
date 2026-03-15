import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import engine, Base, AsyncSessionLocal
from db.models import PayoutTransaction
import uuid
import random
from datetime import datetime, timedelta

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def seed_db():
    async with AsyncSessionLocal() as session:
        print("Seeding database with mock transactions...")
        
        # Scenario 1: A successful transaction
        tx1 = PayoutTransaction(
            transaction_id="TX-SUCCESS-100",
            account_id="ACC-001",
            amount=50.00,
            status="SETTLED",
            service_company="Claro",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )

        # Scenario 2: A transaction that timed out at the Gateway (Debit applied but not paid to service)
        tx2 = PayoutTransaction(
            transaction_id="TX-TIMEOUT-200",
            account_id="ACC-002",
            amount=120.50,
            status="AUTHORIZED", # Money held/debited
            service_company="AguaCorp",
            created_at=datetime.utcnow() - timedelta(minutes=15)
        )

        # Scenario 3: Non-Sufficient Funds (NSF)
        tx3 = PayoutTransaction(
            transaction_id="TX-NSF-300",
            account_id="ACC-003",
            amount=5000.00,
            status="FAILED_NSF",
            service_company="Telefonica",
            created_at=datetime.utcnow() - timedelta(days=1)
        )

        session.add_all([tx1, tx2, tx3])
        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(init_models())
    asyncio.run(seed_db())
