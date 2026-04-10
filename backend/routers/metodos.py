from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, database

router = APIRouter(prefix="/metodos", tags=["Metodos"])

# --- PNTS ---
@router.post("/pnts", response_model=schemas.PNTResponse)
def crear_pnt(pnt: schemas.PNTCreate, db: Session = Depends(database.get_db)):
    db_pnt = models.PNT(**pnt.dict())
    db.add(db_pnt); db.commit(); db.refresh(db_pnt)
    return db_pnt

@router.get("/pnts", response_model=List[schemas.PNTResponse])
def listar_pnts(db: Session = Depends(database.get_db)):
    return db.query(models.PNT).all()

# --- PARAMETROS ---
@router.post("/parametros", response_model=schemas.ParametroResponse)
def crear_parametro(par: schemas.ParametroCreate, db: Session = Depends(database.get_db)):
    db_par = models.Parametro(**par.dict())
    db.add(db_par); db.commit(); db.refresh(db_par)
    return db_par

@router.get("/parametros", response_model=List[schemas.ParametroResponse])
def listar_parametros(db: Session = Depends(database.get_db)):
    return db.query(models.Parametro).all()

# --- CONFIGURACION LIMITES ---
@router.post("/config", response_model=schemas.PNTConfigResponse)
def configurar_limites(conf: schemas.PNTConfigCreate, db: Session = Depends(database.get_db)):
    obj = models.PNTParametroConfig(**conf.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("/config/{id_pnt}", response_model=List[schemas.PNTConfigResponse])
def listar_config_pnt(id_pnt: int, db: Session = Depends(database.get_db)):
    return db.query(models.PNTParametroConfig).filter(models.PNTParametroConfig.id_pnt == id_pnt).all()

@router.put("/config/{id_config}")
def actualizar_config(id_config: int, conf: schemas.PNTConfigCreate, db: Session = Depends(database.get_db)):
    c = db.query(models.PNTParametroConfig).filter(models.PNTParametroConfig.id_config == id_config).first()
    if not c: raise HTTPException(404, "No encontrado")
    c.limite_min = conf.limite_min
    c.limite_max = conf.limite_max
    c.limite_deteccion_LOD = conf.limite_deteccion_LOD
    db.commit()
    return c

@router.delete("/config/{id_config}")
def borrar_config(id_config: int, db: Session = Depends(database.get_db)):
    db.query(models.PNTParametroConfig).filter(models.PNTParametroConfig.id_config == id_config).delete()
    db.commit()
    return {"msg": "Borrado"}

# --- RECETAS (COCINA) ---
@router.post("/recetas", response_model=schemas.RecetaResponse)
def crear_receta(r: schemas.RecetaCreate, db: Session = Depends(database.get_db)):
    obj = models.PNTReceta(**r.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("/recetas/{id_pnt}")
def listar_recetas_pnt(id_pnt: int, db: Session = Depends(database.get_db)):
    recetas = db.query(models.PNTReceta).filter(models.PNTReceta.id_pnt == id_pnt).all()
    res = []
    for r in recetas:
        ings = db.query(models.PNTRecetaIngrediente).filter(models.PNTRecetaIngrediente.id_receta == r.id_receta).all()
        ings_data = []
        for i in ings:
            tipo = db.query(models.TipoReactivo).filter(models.TipoReactivo.id_tipo_reactivo == i.id_tipo_reactivo).first()
            ings_data.append({
                "id_ingrediente": i.id_ingrediente_receta,
                "tipo": tipo.nombre_tipo if tipo else "Desconocido",
                "id_tipo_reactivo": tipo.id_tipo_reactivo if tipo else None,
                "cantidad": i.cantidad_necesaria
            })
        
        res.append({
            "receta": r,
            "ingredientes": ings_data
        })
    return res

@router.post("/recetas/ingredientes")
def agregar_ingrediente(i: schemas.IngredienteCreate, db: Session = Depends(database.get_db)):
    obj = models.PNTRecetaIngrediente(**i.dict())
    db.add(obj); db.commit()
    return {"msg": "Ingrediente añadido"}

# --- GESTIÓN DE RECURSOS NECESARIOS POR PNT ---
@router.post("/recursos", response_model=schemas.PNTRecursoResponse)
def definir_recurso_pnt(r: schemas.PNTRecursoCreate, db: Session = Depends(database.get_db)):
    # Usamos el modelo PNTRecurso mapeado a tb_pnt_recursos
    obj = models.PNTRecurso(**r.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("/recursos/{id_pnt}", response_model=List[schemas.PNTRecursoResponse])
def listar_recursos_pnt(id_pnt: int, db: Session = Depends(database.get_db)):
    items = db.query(models.PNTRecurso).filter(models.PNTRecurso.id_pnt == id_pnt).all()
    for item in items:
        if item.tipo_recurso == "Reactivo":
            t = db.query(models.TipoReactivo).filter(models.TipoReactivo.id_tipo_reactivo == item.id_tipo_necesario).first()
            item.nombre_tipo_necesario = t.nombre_tipo if t else "Desconocido"
        else:
            t = db.query(models.TipoEquipo).filter(models.TipoEquipo.id_tipo_equipo == item.id_tipo_necesario).first()
            item.nombre_tipo_necesario = t.nombre_tipo if t else "Desconocido"
    return items

@router.delete("/recursos/{id_pnt_recurso}")
def borrar_recurso_pnt(id_pnt_recurso: int, db: Session = Depends(database.get_db)):
    db.query(models.PNTRecurso).filter(models.PNTRecurso.id_pnt_recurso == id_pnt_recurso).delete()
    db.commit()
    return {"msg": "Recurso desvinculado del PNT"}
