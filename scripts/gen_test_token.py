# -*- coding: utf-8 -*-
"""
開發用：建立測試 User 並產生 JWT token，方便在 /docs 測試 API。
用法：
  python scripts/gen_test_token.py              # student（預設）
  python scripts/gen_test_token.py teacher
  python scripts/gen_test_token.py admin
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db.database import SessionLocal, engine
from db.models import Base, User
from core.security import create_access_token

Base.metadata.create_all(bind=engine)

role = sys.argv[1] if len(sys.argv) > 1 else "student"
if role not in ("student", "teacher", "admin"):
    print(f"未知角色：{role}，請用 student / teacher / admin")
    sys.exit(1)

email = f"test-{role}@dev.local"
db = SessionLocal()

user = db.query(User).filter(User.email == email).first()
if not user:
    user = User(
        google_id=f"test_google_id_{role}",
        email=email,
        name=f"測試{role}帳號",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created test user: {user.email} (role={role})")
else:
    if user.role != role:
        user.role = role
        db.commit()
        print(f"Updated role: {user.email} → {role}")
    else:
        print(f"Using existing user: {user.email} (role={role})")

token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
db.close()

print(f"\nUser ID : {user.id}")
print(f"Role    : {role}")
print(f"\nTest token:")
print(token)
print(f"\n前端登入網址（貼到瀏覽器）：")
print(f"http://localhost:3000/callback?jwt={token}")
