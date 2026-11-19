import logging
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from src.config.settings import DATABASE_URL
class Base(DeclarativeBase): pass
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
Session=sessionmaker(bind=engine,expire_on_commit=False)
def database():
 with Session() as db: yield db
def ensure_schema():
 Base.metadata.create_all(engine)
 try:
  with engine.begin() as c: c.execute(text('ALTER TABLE sla_runs ADD COLUMN IF NOT EXISTS draft_keys JSON'))
 except Exception: logging.exception('sla_runs.draft_keys 迁移失败，请按 backend/migrations/002_privacy.md 手动执行')
