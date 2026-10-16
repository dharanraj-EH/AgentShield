import sys
from backend import account
from backend.auth import User, LoginSession, password_hash, password_matches
from backend.store import Store, now

def test_private_cli_reset_revokes_sessions(tmp_path, monkeypatch):
    store=Store('sqlite:///'+str(tmp_path/'recovery.db'))
    with store.session.begin() as db:
        db.add(User(id='user',username='researcher',password_hash=password_hash('Old-test-only-passphrase'),tour_completed=False,created_at=now()))
        db.add(LoginSession(token_hash='test-hash',user_id='user',csrf_token='test-csrf',expires_at='2099-01-01T00:00:00+00:00'))
    monkeypatch.setattr(account,'Store',lambda:store)
    monkeypatch.setattr(sys,'argv',['account','reset-password','--username','researcher'])
    monkeypatch.setattr(account.getpass,'getpass',lambda prompt:'New-test-only-passphrase')
    account.main()
    with store.session() as db:
        assert password_matches('New-test-only-passphrase',db.get(User,'user').password_hash)
        assert db.query(LoginSession).count()==0
