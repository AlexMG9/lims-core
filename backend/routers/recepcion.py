from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import List
from datetime import datetime
import database, models, schemas, dependencies

router = APIRouter(prefix="/recepcion", tags=["Recepción"])

# Clientes
@router.post("/clientes", response_model=schemas.ClienteResponse)
def crear_cliente(c: schemas.ClienteCreate, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    obj = models.Cliente(**c.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("/clientes", response_model=List[schemas.ClienteResponse])
def listar_clientes(db: Session = Depends(database.get_db)):
    return db.query(models.Cliente).all()

@router.put("/clientes/{id}", response_model=schemas.ClienteResponse)
def update_cliente(id: int, c: schemas.ClienteCreate, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    obj = db.query(models.Cliente).filter(models.Cliente.id_cliente == id).first()
    if not obj: raise HTTPException(404, "No existe")
    obj.nombre_fiscal = c.nombre_fiscal
    obj.email_contacto = c.email_contacto
    db.commit(); db.refresh(obj)
    return obj

@router.delete("/clientes/{id}")
def delete_cliente(id: int, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    obj = db.query(models.Cliente).filter(models.Cliente.id_cliente == id).first()
    if not obj: raise HTTPException(404, "No existe")
    try: db.delete(obj); db.commit()
    except: db.rollback(); raise HTTPException(400, "Tiene datos asociados")
    return {"msg": "Borrado"}

@router.post("/", response_model=schemas.RecepcionResponse)
def crear_recepcion(r: schemas.RecepcionCreate, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    obj = models.Recepcion(**r.dict())
    obj.recibido_por = u.id_usuario
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("/", response_model=List[schemas.RecepcionResponse])
def listar_recepciones(db: Session = Depends(database.get_db)):
    return db.query(models.Recepcion).order_by(models.Recepcion.id_recepcion.desc()).limit(100).all()

@router.delete("/{id}")
def delete_recepcion(id: int, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    obj = db.query(models.Recepcion).filter(models.Recepcion.id_recepcion == id).first()
    if not obj: raise HTTPException(404, "No existe")
    try: db.delete(obj); db.commit()
    except: db.rollback(); raise HTTPException(400, "Contiene muestras")
    return {"msg": "Borrado"}

# Muestras
@router.post("/muestras", response_model=schemas.MuestraResponse)
def registrar_muestra(m: schemas.MuestraCreate, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    anio = datetime.now().year
    corto = datetime.now().strftime("%y")
    last = db.query(models.Muestra).filter(extract('year', models.Muestra.fecha_recepcion) == anio).order_by(models.Muestra.correlativo_anual.desc()).first()
    corr = (last.correlativo_anual + 1) if (last and last.correlativo_anual) else 1
    
    obj = models.Muestra(**m.dict(exclude={"pnts_ids"}))
    obj.correlativo_anual = corr
    obj.codigo_laboratorio = f"M-{corto}_{corr:05d}"
    db.add(obj); db.flush()
    
    cnt = 0
    if m.pnts_ids:
        for pid in m.pnts_ids:
            db.add(models.SubmuestraAnalisis(id_muestra_padre=obj.id_muestra, id_pnt_destino=pid, estado_individual="Pendiente"))
            cnt += 1
            
    db.commit(); db.refresh(obj)
    obj.cod_lims = obj.codigo_laboratorio
    obj.submuestras_generadas = cnt
    return obj

@router.get("/muestras", response_model=List[schemas.MuestraResponse])
def listar_muestras(db: Session = Depends(database.get_db)):
    objs = db.query(models.Muestra).filter(models.Muestra.is_deleted == False).order_by(models.Muestra.id_muestra.desc()).all()
    for o in objs:
        o.cod_lims = o.codigo_laboratorio if o.codigo_laboratorio else f"OLD-{o.id_muestra}"
        o.submuestras_generadas = 0
    return objs
