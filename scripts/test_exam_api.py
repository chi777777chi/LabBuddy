# -*- coding: utf-8 -*-
"""直接測試 exam API（繞過 Swagger UI 的空格問題）"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import requests
from core.security import create_access_token
from db.database import SessionLocal
from db.models import User

db = SessionLocal()
user = db.query(User).filter(User.email == "test@dev.local").first()
db.close()

token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
BASE = "http://127.0.0.1:8000"

print("=== POST /exam/start ===")
resp = requests.post(f"{BASE}/exam/start", params={"token": token}, json={
    "subject_id": 1,
    "mode": "single_full",
    "question_count": 5,
    "year": 114,
    "sitting": 2,
    "shuffle_options": False,
    "timed": False,
    "instant_review": True,
    "save_to_history": True,
})
print("Status:", resp.status_code)
data = resp.json()
if resp.status_code != 200:
    print("Error:", data)
    sys.exit(1)

session_id = data["session_id"]
questions  = data["questions"]
print(f"session_id: {session_id}")
print(f"題數: {len(questions)}")
print(f"第1題: {questions[0]['content'][:40]}...")
print(f"來源: {questions[0]['source']}")

print("\n=== POST /exam/{session_id}/answer (答第1題) ===")
q1 = questions[0]
resp2 = requests.post(f"{BASE}/exam/{session_id}/answer", params={"token": token}, json={
    "question_id": q1["question_id"],
    "chosen": "A",
    "time_spent_seconds": 30,
})
print("Status:", resp2.status_code)
print(resp2.json())

print("\n=== POST /exam/{session_id}/submit ===")
resp3 = requests.post(f"{BASE}/exam/{session_id}/submit", params={"token": token})
print("Status:", resp3.status_code)
result = resp3.json()
print(f"得分: {result['score']} / {result['total']}  ({result['percentage']}%)")
print(f"各題: ", [(d['order'], d['chosen'], d['correct_answer'], d['is_correct']) for d in result['details']])
