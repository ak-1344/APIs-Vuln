import atheris
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

with atheris.instrument_imports():
    from app.database import SessionLocal, engine, Base
    from app.models import Order
    from app.routes.orders import get_order

Base.metadata.create_all(bind=engine)
db_seed = SessionLocal()
if db_seed.query(Order).count() == 0:
    db_seed.add(Order(id=1, user_id=1, product="Wheel", price=299.0))
    db_seed.add(Order(id=2, user_id=2, product="Oil", price=49.0))
    db_seed.commit()
db_seed.close()

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    order_id = fdp.ConsumeInt(4)
    user_id = fdp.ConsumeInt(4)
    db = SessionLocal()
    try:
        get_order(order_id=order_id, db=db, user_id=user_id)
    except Exception:
        pass
    finally:
        db.close()

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
