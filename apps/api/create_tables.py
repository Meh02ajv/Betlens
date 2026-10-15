import os, sys
os.environ["DATABASE_URL"] = "postgresql+psycopg2://betlens:betlens@127.0.0.1:5433/betlens"
os.environ["SECRET_KEY"] = "dev-secret-key"
os.environ["APP_ENV"] = "development"
os.environ["FOOTBALL_PROVIDER"] = "mock"
os.environ["NBA_PROVIDER"] = "mock"
os.environ["ODDS_PROVIDER"] = "mock"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

sys.path.insert(0, ".")
from sqlalchemy import create_engine
from app.db.base import Base
from app.db import models

engine = create_engine("postgresql+psycopg2://betlens:betlens@127.0.0.1:5433/betlens", echo=False)
Base.metadata.create_all(engine)
engine.dispose()
print("All tables created!")