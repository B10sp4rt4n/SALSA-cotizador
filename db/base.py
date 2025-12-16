"""
Configuración base de SQLAlchemy
Preparado para migración futura a persistencia
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# SQLite local (migrable a Neon PostgreSQL sin cambiar código)
DATABASE_URL = "sqlite:///./cotizador.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # solo para SQLite
    echo=False  # cambiar a True para debug SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Session:
    """Factory de sesiones para usar cuando se active persistencia"""
    session = SessionLocal()
    try:
        return session
    finally:
        pass  # se cierra manualmente en cada uso
