from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import database, models, schemas, dependencies

router = APIRouter(prefix="/equipos", tags=["Gestión de Equipos"])

@router.post("/", response_model=schemas.EquipoResponse)
def crear_equipo(eq: schemas.EquipoCreate, db: Session = Depends(database.get_db), user: models.Usuario = Depends(dependencies.get_current_user)):
    db_eq = models.Equipo(**eq.dict())
    db.add(db_eq); db.commit(); db.refresh(db_eq)
    db_eq.cod_interno = f"EQ-{db_eq.id_equipo:03d}"
    return db_eq

@router.get("/", response_model=List[schemas.EquipoResponse])
def listar_equipos(db: Session = Depends(database.get_db)):
    eqs = db.query(models.Equipo).filter(models.Equipo.is_deleted == False).all()
    for e in eqs:
        e.cod_interno = f"EQ-{e.id_equipo:03d}"
    return eqs

@router.put("/{id_equipo}", response_model=schemas.EquipoResponse)
def actualizar_equipo(id_equipo: int, eq: schemas.EquipoCreate, db: Session = Depends(database.get_db), user: models.Usuario = Depends(dependencies.get_current_user)):
    db_eq = db.query(models.Equipo).filter(models.Equipo.id_equipo == id_equipo).first()
    if not db_eq: raise HTTPException(404, "No encontrado")
    
    db_eq.nombre_equipo = eq.nombre_equipo
    db_eq.numero_serie = eq.numero_serie
    db_eq.fecha_prox_calib = eq.fecha_prox_calib
    db_eq.estado_operativo = eq.estado_operativo
    db_eq.ubicacion = eq.ubicacion
    
    db.commit(); db.refresh(db_eq)
    db_eq.cod_interno = f"EQ-{db_eq.id_equipo:03d}"
    return db_eq

@router.delete("/{id_equipo}")
def eliminar_equipo(id_equipo: int, db: Session = Depends(database.get_db), user: models.Usuario = Depends(dependencies.get_current_user)):
    db_eq = db.query(models.Equipo).filter(models.Equipo.id_equipo == id_equipo).first()
    if not db_eq: raise HTTPException(404, "No encontrado")
    db_eq.is_deleted = True
    db.commit()
    return {"msg": "Equipo dado de baja"}

# --- TIPOS DE EQUIPO ---
@router.post("/tipos")
def crear_tipo_equipo(nombre: str, db: Session = Depends(database.get_db)):
    t = models.TipoEquipo(nombre_tipo=nombre)
    db.add(t); db.commit(); db.refresh(t)
    return t

@router.get("/tipos")
def listar_tipos_equipo(db: Session = Depends(database.get_db)):
    return db.query(models.TipoEquipo).all()

@router.put("/{id}/asignar_tipo")
def asignar_tipo_equipo(id: int, id_tipo: int, db: Session = Depends(database.get_db)):
    e = db.query(models.Equipo).filter(models.Equipo.id_equipo == id).first()
    if not e: raise HTTPException(404, "Equipo no encontrado")
    e.id_tipo_equipo = id_tipo
    db.commit()
    return {"msg": "Tipo asignado"}
