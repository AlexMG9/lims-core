from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

SQLALCHEMY_DATABASE_URL = (
    f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@db_lims/{os.getenv('MYSQL_DATABASE')}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True, # Verifica que la conexión está viva antes de usarla
    pool_recycle=3600   # Recicla conexiones cada hora para evitar timeouts
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()