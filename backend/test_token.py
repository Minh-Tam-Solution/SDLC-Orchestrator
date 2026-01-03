import sys
sys.path.insert(0, "/app")
import os
os.chdir("/app")

from app.db.session import SessionLocal
from app.models.user import PasswordResetToken
from datetime import datetime, timezone

db = SessionLocal()
tokens = db.query(PasswordResetToken).order_by(PasswordResetToken.created_at.desc()).limit(3).all()
for t in tokens:
    print(f"Token ID: {t.id}")
    print(f"  Created: {t.created_at}")
    print(f"  Expires: {t.expires_at}")
    now_utc = datetime.now(timezone.utc)
    now_naive = datetime.utcnow()
    print(f"  Now (UTC aware): {now_utc}")
    print(f"  Now (naive): {now_naive}")
    print(f"  is_expired: {t.is_expired}")
    print("---")
db.close()
