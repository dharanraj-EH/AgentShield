import json
import os
import threading
from contextvars import ContextVar
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, Column, String, Text, Integer, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .security import redact

Base = declarative_base()
current_owner = ContextVar('agentshield_owner', default=None)
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return str(uuid4())

class Event(Base):
    __tablename__ = 'events'
    sequence = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String, unique=True)
    run_id = Column(String, index=True)
    timestamp = Column(String)
    kind = Column(String)
    data = Column(Text)
    owner_id = Column(String, index=True, default=lambda: current_owner.get())

class Run(Base):
    __tablename__ = 'runs'
    id = Column(String, primary_key=True)
    scenario = Column(String)
    mode = Column(String)
    provider = Column(String)
    timestamp = Column(String)
    result = Column(Text)
    owner_id = Column(String, index=True, default=lambda: current_owner.get())

class Approval(Base):
    __tablename__ = 'approvals'
    id = Column(String, primary_key=True)
    run_id = Column(String)
    action = Column(Text)
    status = Column(String)
    timestamp = Column(String)
    owner_id = Column(String, index=True, default=lambda: current_owner.get())

class WorkspacePolicy(Base):
    __tablename__ = 'workspace_policies'
    owner_id = Column(String, primary_key=True)
    data = Column(Text, nullable=False)

def owned(query, model):
    owner=current_owner.get()
    if owner:
        if os.getenv('AGENTSHIELD_PUBLIC')=='1': return query.filter(model.owner_id==owner)
        return query.filter((model.owner_id==owner)|(model.owner_id.is_(None)))
    if os.getenv('AGENTSHIELD_PUBLIC')=='1': return query.filter(model.owner_id=='__no_authenticated_owner__')
    return query

class Store:
    def __init__(self, url=None):
        database_url=url or os.getenv('DATABASE_URL') or os.getenv('AGENTSHIELD_DB','sqlite:///agentshield.db')
        if database_url.startswith('postgres://'): database_url=database_url.replace('postgres://','postgresql+psycopg://',1)
        elif database_url.startswith('postgresql://'): database_url=database_url.replace('postgresql://','postgresql+psycopg://',1)
        self.engine=create_engine(database_url,connect_args={'check_same_thread':False} if database_url.startswith('sqlite:') else {},pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        # Additive migration: preserve existing local experiment records.
        for table_name in ['events','runs','approvals']:
            if 'owner_id' not in [column['name'] for column in inspect(self.engine).get_columns(table_name)]:
                with self.engine.begin() as connection: connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN owner_id VARCHAR'))
        self.session = sessionmaker(self.engine)
        self.lock = threading.RLock()
    def event(self, run_id, kind, data):
        with self.session.begin() as db:
            db.add(Event(id=uid(), run_id=run_id, timestamp=now(), kind=kind, data=json.dumps(redact(data))))
    def events(self):
        with self.session() as db:
            return [{**json.loads(e.data), 'id': e.id, 'run_id': e.run_id, 'timestamp': e.timestamp, 'kind': e.kind} for e in owned(db.query(Event),Event).order_by(Event.sequence.desc()).limit(1000)]
    def runs(self):
        with self.session() as db:
            return [{**json.loads(r.result),'id':r.id,'scenario':r.scenario,'mode':r.mode,'provider':r.provider,'timestamp':r.timestamp} for r in owned(db.query(Run),Run).order_by(Run.timestamp.desc()).limit(1000)]
    def approvals(self):
        with self.session() as db:
            return [dict(id=a.id, run_id=a.run_id, status=a.status, timestamp=a.timestamp, action=redact(json.loads(a.action))) for a in owned(db.query(Approval),Approval).all()]

    def policy_for_owner(self):
        from .security import Policy
        with self.session() as db:
            row=db.get(WorkspacePolicy,current_owner.get()) if current_owner.get() else None
            return Policy.model_validate_json(row.data) if row else Policy()

    def save_policy(self, policy):
        owner=current_owner.get()
        if not owner: raise ValueError('Authenticated owner required')
        with self.session.begin() as db: db.merge(WorkspacePolicy(owner_id=owner,data=policy.model_dump_json()))
