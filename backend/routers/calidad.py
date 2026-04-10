from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import sys, os

# Ajuste de path para importar módulos hermanos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db
import schemas

router = APIRouter(
    prefix="/calidad",
    tags=["calidad"]
)

@router.get("/pendientes", response_model=List[schemas.CalidadOrdenView])
def get_ordenes_pendientes_revision(db: Session = Depends(get_db)):
    """
    Obtiene todas las OTs en estado 'Finalizada' esperando revisión de Calidad.
    Lee directamente de la vista SQL 'view_calidad_pendiente'.
    """
    try:
        # Usamos SQL directo porque es una Vista, no una Tabla mapeada en el ORM
        result = db.execute(text("SELECT * FROM view_calidad_pendiente"))
        # Convertimos las filas de SQL a diccionarios para Pydantic
        ordenes = result.mappings().all()
        return ordenes
    except Exception as e:
        print(f"Error consultando vista calidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))
