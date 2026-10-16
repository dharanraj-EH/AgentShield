"""Public mode fails closed without HTTPS origin and persistent PostgreSQL."""
import os
from urllib.parse import urlsplit

def public_settings():
    public=os.getenv('AGENTSHIELD_PUBLIC')=='1'
    origin=os.getenv('AGENTSHIELD_PUBLIC_ORIGIN') or os.getenv('RENDER_EXTERNAL_URL','')
    if public:
        parsed=urlsplit(origin)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
            raise RuntimeError('Public deployment requires an explicit HTTPS origin')
        database=os.getenv('DATABASE_URL','')
        if not database.startswith(('postgres://','postgresql://','postgresql+psycopg://')):
            raise RuntimeError('Public deployment requires persistent PostgreSQL via DATABASE_URL')
        if os.getenv('AGENTSHIELD_ENABLE_REAL_MODEL')=='1':
            raise RuntimeError('Public real-model execution requires an independently reviewed inference deployment; disabled in the free pilot')
    return public,origin.rstrip('/')
