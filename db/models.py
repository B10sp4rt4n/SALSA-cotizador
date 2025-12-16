"""
Modelos SQLAlchemy - nodos del sistema
Preparados para cuando se active la persistencia
"""
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Cotizacion(Base):
    """Contenedor de líneas de cotización"""
    __tablename__ = "cotizaciones"
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=True)
    creada_en = Column(DateTime, default=datetime.utcnow)
    modificada_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    lineas = relationship("Linea", back_populates="cotizacion", cascade="all, delete-orphan")
    totales = relationship("Totales", back_populates="cotizacion", uselist=False)


class Linea(Base):
    """Línea de cotización (producto o servicio)"""
    __tablename__ = "lineas"
    
    id = Column(Integer, primary_key=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    orden = Column(Integer, default=0)
    tipo = Column(String, default="producto")  # 'producto' | 'servicio'
    
    # FUENTE_EXCEL (se preserva tal cual - JSON para no perder columnas)
    fuente = Column(JSON, nullable=True)
    
    # Datos visibles
    sku = Column(String)
    descripcion = Column(String)
    
    # COSTO_REAL
    precio_lista = Column(Float, default=0.0)
    descuento_pct = Column(Float, default=0.0)
    costo_real = Column(Float, default=0.0)
    costo_es_establecido = Column(Boolean, default=False)  # True si es costo manual
    
    # ESTRATEGIA / PRECIO
    estrategia = Column(JSON)  # {"tipo": "margen_objetivo", "valor": 10.0, ...}
    precio_venta = Column(Float, default=0.0)
    
    # RESULTADOS POR LINEA
    utilidad_linea = Column(Float, default=0.0)
    margen_linea = Column(Float, default=0.0)
    
    # Relaciones
    cotizacion = relationship("Cotizacion", back_populates="lineas")


class Totales(Base):
    """Totales agregados de la cotización"""
    __tablename__ = "totales"
    
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"), primary_key=True)
    total_costo = Column(Float, default=0.0)
    total_venta = Column(Float, default=0.0)
    utilidad_total = Column(Float, default=0.0)
    margen_total = Column(Float, default=0.0)
    
    # Relaciones
    cotizacion = relationship("Cotizacion", back_populates="totales")


# Inicialización (se llamará cuando se active persistencia)
def init_db():
    """Crea todas las tablas en la base de datos"""
    from db.base import engine
    Base.metadata.create_all(bind=engine)
