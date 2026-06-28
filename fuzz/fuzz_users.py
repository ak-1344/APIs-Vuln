import atheris
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

with atheris.instrument_imports():
    from app.database import SessionLocal, engine, Base
    from app.models import User
    from app.routes.users import search_users

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(User).count() == 0:
    db.add(User(id=1, email="user_a@test.com", password="pass123", role="user", credit=100))
    db.commit()
db.close()

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    user_input = fdp.ConsumeUnicodeNoSurrogates(128)
    db = SessionLocal()
    try:
        result = search_users(name=user_input, db=db)
        if result and len(str(result)) > 100:
            print(f"[INTERESTING] Large result on: {repr(user_input[:80])}", flush=True)
    except Exception as e:
        err = str(e).lower()
        if any(k in err for k in ['sql', 'syntax', 'operational', 'database']):
            print(f"[SQL_ERROR] input: {repr(user_input[:60])} error: {str(e)[:80]}", flush=True)
    finally:
        db.close()

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
