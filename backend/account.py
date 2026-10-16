"""Local owner recovery. Run in a terminal; passwords never become CLI arguments."""
import argparse
import getpass
from .auth import User, LoginSession, password_hash
from .store import Store

def main():
    parser = argparse.ArgumentParser(description='AgentShield local account recovery')
    parser.add_argument('action', choices=['reset-password'])
    parser.add_argument('--username', required=True)
    args = parser.parse_args()
    first = getpass.getpass('New password (at least 12 characters): ')
    second = getpass.getpass('Confirm new password: ')
    if len(first) < 12 or len(first) > 128 or first != second:
        raise SystemExit('Passwords must match and contain 12–128 characters. No change made.')
    store = Store()
    with store.session.begin() as db:
        user = db.query(User).filter(User.username == args.username.lower()).first()
        if not user: raise SystemExit('Account not found. No change made.')
        user.password_hash = password_hash(first)
        db.query(LoginSession).filter(LoginSession.user_id == user.id).delete()
    print('Password updated. Existing sessions were signed out.')
if __name__ == '__main__': main()
