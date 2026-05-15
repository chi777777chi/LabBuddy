# -*- coding: utf-8 -*-
"""
開發用：建立測試 User 並產生 JWT token，方便在 /docs 測試 exam API。
用法：python scripts/gen_test_token.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db.database import SessionLocal, engine
from db.models import Base, User
from core.security import create_access_token

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 找或建立測試帳號
user = db.query(User).filter(User.email == "test@dev.local").first()
if not user:
    user = User(
        google_id="test_google_id_dev",
        email="test@dev.local",
        name="測試用戶",
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created test user: {user.email}")
else:
    print(f"Using existing user: {user.email}")

token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
db.close()

print(f"\nUser ID : {user.id}")
print(f"\nTest token (貼到 /docs 的 token 欄位):")
print(token)
