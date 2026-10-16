"""Local-account authentication. Passwords and bearer session IDs are never logged."""
import hashlib
import hmac
import secrets
import time
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Response
from pydantic import Field
from sqlalchemy import Column, String, Boolean, inspect, text
from .security import Strict
from .store import Base, now, uid

COOKIE = 'agentshield_session'
ITERATIONS = 600_000

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    tour_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(String, nullable=False)
    role = Column(String, nullable=False, default='owner', server_default='owner')

class LoginSession(Base):
    __tablename__ = 'login_sessions'
    token_hash = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    csrf_token = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)

class Credentials(Strict):
    username: str = Field(min_length=3, max_length=40, pattern=r'^[a-zA-Z0-9_.-]+$')
    password: str = Field(min_length=1, max_length=128)

def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return f'pbkdf2_sha256${ITERATIONS}${salt}${digest}'

def password_matches(password, encoded):
    _, count, salt, expected = encoded.split('$')
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(count)).hex()
    return hmac.compare_digest(actual, expected)

def digest(value): return hashlib.sha256(value.encode()).hexdigest()

class Auth:
    def __init__(self, store):
        self.store = store
        Base.metadata.create_all(store.engine)
        if 'role' not in [c['name'] for c in inspect(store.engine).get_columns('users')]:
            with store.engine.begin() as connection: connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'owner'"))
        self.failures = []
        self.registrations = []
        self.dummy_hash = password_hash(secrets.token_urlsafe(24))

    def setup_required(self):
        if os.getenv('AGENTSHIELD_PUBLIC')=='1': return False
        with self.store.session() as db: return db.query(User).count() == 0

    def public_user(self, user):
        return {'id': user.id, 'username': user.username, 'tour_completed': user.tour_completed,'role':user.role}

    def create(self, credentials, registration=False):
        if len(credentials.password) < 12:
            raise HTTPException(422, 'Use a password of at least 12 characters')
        with self.store.lock, self.store.session.begin() as db:
            if registration:
                if os.getenv('AGENTSHIELD_PUBLIC_REGISTRATION')!='1': raise HTTPException(403,'Public registration is disabled')
                self.registrations=[t for t in self.registrations if t>time.monotonic()-600]
                if len(self.registrations)>=10 or db.query(User).count()>=500: raise HTTPException(429,'Registration limit reached. Please try later or contact the workspace owner.')
            elif os.getenv('AGENTSHIELD_PUBLIC')=='1': raise HTTPException(403,'Owner setup is disabled on public deployments')
            elif db.query(User).first(): raise HTTPException(409, 'Workspace account already exists. Sign in instead.')
            if db.query(User).filter(User.username==credentials.username.lower()).first(): raise HTTPException(409,'Choose another username')
            user = User(id=uid(), username=credentials.username.lower(), password_hash=password_hash(credentials.password), tour_completed=False, created_at=now(),role='operator' if registration else 'owner')
            db.add(user); db.flush()
            if registration:self.registrations.append(time.monotonic())
            return user.id

    def login(self, credentials, response):
        with self.store.lock:
            cutoff = time.monotonic() - 60
            self.failures = [t for t in self.failures if t > cutoff]
            if len(self.failures) >= 5: raise HTTPException(429, 'Too many attempts. Wait one minute and try again.')
            with self.store.session.begin() as db:
                user = db.query(User).filter(User.username == credentials.username.lower()).first()
                valid = password_matches(credentials.password, user.password_hash if user else self.dummy_hash)
                if not user or not valid:
                    self.failures.append(time.monotonic())
                    raise HTTPException(401, 'Username or password is incorrect')
                # Rotate sessions on login; one active session per local workspace user.
                db.query(LoginSession).filter(LoginSession.user_id == user.id).delete()
                token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                db.add(LoginSession(token_hash=digest(token), user_id=user.id, csrf_token=csrf,
                    expires_at=(datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()))
                result = {'user': self.public_user(user), 'token': csrf}
            response.set_cookie(COOKIE, token, httponly=True, samesite='strict', secure=os.getenv('AGENTSHIELD_PUBLIC')=='1', max_age=8*3600, path='/api')
            return result

    def session(self, request, require_csrf=False):
        token = request.cookies.get(COOKIE, '')
        with self.store.session() as db:
            session = db.get(LoginSession, digest(token)) if token else None
            if not session or session.expires_at <= now(): raise HTTPException(401, 'Sign in to your workspace')
            user = db.get(User, session.user_id)
            if not user: raise HTTPException(401, 'Sign in to your workspace')
            if require_csrf and not secrets.compare_digest(request.headers.get('x-agentshield-session', ''), session.csrf_token):
                raise HTTPException(403, 'Valid authenticated session header required')
            return {'user': self.public_user(user), 'token': session.csrf_token}

    def logout(self, request, response):
        with self.store.session.begin() as db:
            db.query(LoginSession).filter(LoginSession.token_hash == digest(request.cookies.get(COOKIE, ''))).delete()
        response.delete_cookie(COOKIE, path='/api')

    def complete_tour(self, request):
        user_id = self.session(request, require_csrf=True)['user']['id']
        with self.store.session.begin() as db:
            user = db.get(User, user_id); user.tour_completed = True
        return {'tour_completed': True}
