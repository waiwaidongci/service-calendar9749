from sqlalchemy import Column,Integer,String,JSON,Float,CheckConstraint
from src.config.database import Base
class PrivacyAccount(Base):
 __tablename__='privacy_accounts'
 id=Column(Integer,primary_key=True);draft_key=Column(String(120),unique=True);budget=Column(Float);spent=Column(Float,default=0.0)
 __table_args__=(CheckConstraint('spent<=budget'),)
class Publication(Base):
 __tablename__='dp_publications'
 id=Column(Integer,primary_key=True);run_id=Column(Integer);idempotency_key=Column(String(120),unique=True);epsilon=Column(Float);result=Column(JSON);created=Column(Float);actor=Column(String(120))
