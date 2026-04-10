from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
import shutil
import os
import models, schemas, database, dependencies

router = APIRouter(prefix="/reactivos", tags=["Reactivos"])

# --- TIPOS ---
@router.post("/tipos", response_model=schemas.TipoResponse)
def crear_tipo_reactivo(nombre: str, descripcion: str = None, db: Session = Depends(database.get_db)):
    t = models.TipoReactivo(nombre_tipo=nombre, descripcion=descripcion)
    db.add(t); db.commit(); db.refresh(t)
    return t

@router.get("/tipos", response_model=List[schemas.TipoResponse])
def listar_tipos_reactivo(db: Session = Depends(database.get_db)):
    return db.query(models.TipoReactivo).all()

# --- CRUD REACTIVOS ---
@router.post("/", response_model=schemas.ReactivoResponse)
def crear_reactivo(r: schemas.ReactivoCreate, db: Session = Depends(database.get_db)):
    # 1. Calcular el ID siguiente para el código visual
    last = db.query(models.Reactivo).order_by(models.Reactivo.id_reactivo.desc()).first()
    new_id = (last.id_reactivo + 1) if last else 1
    
    # 2. Limpiar datos y crear objeto
    data = r.dict(exclude_unset=True)
    if 'cod_interno' in data: del data['cod_interno'] # Lo generamos nosotros, ignoramos entrada
    
    db_item = models.Reactivo(**data)
    
    # 3. ASIGNAR CÓDIGO INTERNO (La clave)
    db_item.cod_interno = f"R-{new_id:04d}"
    
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[schemas.ReactivoResponse])
def listar_reactivos(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Reactivo).filter(models.Reactivo.is_deleted == False).offset(skip).limit(limit).all()

@router.delete("/{id_reactivo}")
def borrar_reactivo(id_reactivo: int, db: Session = Depends(database.get_db)):
    item = db.query(models.Reactivo).filter(models.Reactivo.id_reactivo == id_reactivo).first()
    if not item: raise HTTPException(404, "No encontrado")
    item.is_deleted = True
    db.commit()
    return {"msg": "Eliminado"}

@router.post("/{id_reactivo}/upload_certificado")
def upload_certificado(id_reactivo: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    item = db.query(models.Reactivo).filter(models.Reactivo.id_reactivo == id_reactivo).first()
    if not item: raise HTTPException(404, "Reactivo no encontrado")
    
    os.makedirs("uploads/certs", exist_ok=True)
    filename = f"CERT_{item.cod_interno}_{file.filename}"
    path = f"uploads/certs/{filename}"
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    item.ruta_certificado = f"certs/{filename}"
    db.commit()
    return {"filename": filename}

@router.patch("/{id_reactivo}/abrir")
def registrar_apertura(id_reactivo: int, db: Session = Depends(database.get_db), user: models.Usuario = Depends(dependencies.get_current_user)):
    item = db.query(models.Reactivo).filter(models.Reactivo.id_reactivo == id_reactivo).first()
    if not item: raise HTTPException(404, "Reactivo no encontrado")
    item.fecha_apertura = date.today()
    db.commit()
    return {"msg": "Apertura registrada"}

# --- PREPARACIÓN (COCINA) ---
@router.post("/preparar", response_model=schemas.ReactivoResponse)
def preparar_disolucion(
    prep: schemas.PreparacionCreate, 
    clasificacion: str = "Disolucion", 
    db: Session = Depends(database.get_db), 
    user: models.Usuario = Depends(dependencies.get_current_user)
):
    receta = db.query(models.PNTReceta).filter(models.PNTReceta.id_receta == prep.id_receta).first()
    if not receta: raise HTTPException(404, "Receta no encontrada")
    
    # Generar Lote D-YY-XXXX
    year_short = datetime.now().strftime('%y')
    prefix = f"D-{year_short}-"
    last = db.query(models.Reactivo).filter(models.Reactivo.numero_lote.like(f"{prefix}%")).order_by(models.Reactivo.id_reactivo.desc()).first()
    
    secuencial = 1
    if last:
        try:
            parts = last.numero_lote.split('-')
            if len(parts) == 3: secuencial = int(parts[2]) + 1
        except: pass
    
    nuevo_lote = f"{prefix}{secuencial:04d}"
    fecha_cad = date.today() + timedelta(hours=receta.caducidad_horas)
    
    # Crear el Reactivo Hijo
    hijo = models.Reactivo(
        nombre=receta.nombre_receta,
        clasificacion="Disolucion",
        proveedor="INTERNO",
        numero_lote=nuevo_lote,
        cantidad_inicial=prep.cantidad_preparada,
        unidad=receta.unidad_referencia,
        fecha_caducidad=fecha_cad,
        estado_calidad="En Uso"
    )
    db.add(hijo)
    db.commit()
    db.refresh(hijo)
    
    # ASIGNAR CÓDIGO INTERNO AL HIJO
    hijo.cod_interno = f"R-{hijo.id_reactivo:04d}"
    db.commit()
    
    # Trazabilidad (Genealogía)
    for item in prep.ids_padres:
        id_padre, cant_gastada = int(item[0]), float(item[1])
        vinculo = models.ComposicionReactivo(
            id_reactivo_hijo=hijo.id_reactivo, 
            id_reactivo_padre=id_padre,
            cantidad_gastada=cant_gastada
        )
        db.add(vinculo)
            
    db.commit()
    return hijo
