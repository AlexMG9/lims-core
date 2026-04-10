from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import database, models, schemas, dependencies

router = APIRouter(prefix="/ejecucion", tags=["Ejecución Analítica"])

# --- WORKLIST ---
@router.get("/pendientes/{id_pnt}")
def ver_pendientes_por_pnt(id_pnt: int, db: Session = Depends(database.get_db)):
    subs = db.query(models.SubmuestraAnalisis).filter(
        models.SubmuestraAnalisis.id_pnt_destino == id_pnt,
        models.SubmuestraAnalisis.estado_individual == "Pendiente"
    ).all()
    res = []
    for s in subs:
        m = db.query(models.Muestra).filter(models.Muestra.id_muestra == s.id_muestra_padre).first()
        if m:
            res.append({
                "id_submuestra": s.id_submuestra,
                "cod_lims": m.codigo_laboratorio or f"M-{m.id_muestra}",
                "referencia": m.referencia_cliente_externa,
                "tipo": m.tipo_muestra
            })
    return res

# --- ÓRDENES ---
@router.post("/ordenes", response_model=schemas.OrdenTrabajoResponse)
def crear_orden(orden: schemas.OrdenTrabajoCreate, db: Session = Depends(database.get_db), user: models.Usuario = Depends(dependencies.get_current_user)):
    db_orden = models.OrdenTrabajo(**orden.dict(), id_analista_responsable=user.id_usuario, fecha_inicio=datetime.now())
    db.add(db_orden); db.commit(); db.refresh(db_orden)
    db_orden.cod_orden = f"OT-{db_orden.id_orden:05d}"
    return db_orden

@router.get("/ordenes")
def listar_ordenes(db: Session = Depends(database.get_db)):
    ordenes = db.query(models.OrdenTrabajo).order_by(models.OrdenTrabajo.id_orden.desc()).all()
    for o in ordenes:
        o.cod_orden = f"OT-{o.id_orden:05d}"
    return ordenes

@router.post("/ordenes/{id_orden}/items")
def agregar_items_orden(id_orden: int, items: List[int], db: Session = Depends(database.get_db)):
    for id_sub in items:
        db.add(models.OrdenItem(id_orden=id_orden, id_submuestra=id_sub))
        sub = db.query(models.SubmuestraAnalisis).filter(models.SubmuestraAnalisis.id_submuestra == id_sub).first()
        if sub: sub.estado_individual = "En Curso"
    db.commit()
    return {"msg": "Items añadidos"}

# --- DATA GRID ---
@router.get("/ordenes/{id_orden}/grid")
def obtener_datos_grid(id_orden: int, db: Session = Depends(database.get_db)):
    items = db.query(models.OrdenItem).filter(models.OrdenItem.id_orden == id_orden).all()
    grid_data = []
    for item in items:
        sub = db.query(models.SubmuestraAnalisis).filter(models.SubmuestraAnalisis.id_submuestra == item.id_submuestra).first()
        madre = db.query(models.Muestra).filter(models.Muestra.id_muestra == sub.id_muestra_padre).first()
        codigo = madre.codigo_laboratorio or f"M-{madre.id_muestra}"
        
        resultados = db.query(models.Resultado).filter(models.Resultado.id_item_orden == item.id_item_orden).all()
        res_dict = {r.id_parametro: r.valor_resultado for r in resultados}
        
        # Estado de la fila: Si tiene resultados y todos son 'Validado'
        estado_fila = "Pendiente"
        if resultados:
            if all(r.estado_validacion == 'Validado' for r in resultados):
                estado_fila = "Validado"
        
        grid_data.append({
            "id_item_orden": item.id_item_orden,
            "cod_lims": codigo,
            "referencia": madre.referencia_cliente_externa,
            "estado": estado_fila,
            "resultados": res_dict
        })
    return grid_data

# --- GUARDAR RESULTADOS (LÓGICA DE CIERRE) ---
@router.post("/resultados_batch")
def guardar_resultados_batch(
    datos: List[schemas.ResultadoCreate], 
    validar: bool = False, 
    db: Session = Depends(database.get_db), 
    user: models.Usuario = Depends(dependencies.get_current_user)
):
    ot_ids_afectadas = set()
    
    # 1. Guardar / Actualizar Resultados
    for res in datos:
        # Buscar item para saber la OT
        item = db.query(models.OrdenItem).filter(models.OrdenItem.id_item_orden == res.id_item_orden).first()
        if item: ot_ids_afectadas.add(item.id_orden)

        existe = db.query(models.Resultado).filter(
            models.Resultado.id_item_orden == res.id_item_orden,
            models.Resultado.id_parametro == res.id_parametro
        ).first()
        
        estado_nuevo = "Validado" if validar else "Borrador"
        
        if existe:
            existe.valor_resultado = res.valor_resultado
            existe.estado_validacion = estado_nuevo
            existe.fecha_hora_resultado = datetime.now()
        else:
            new_res = models.Resultado(**res.dict())
            new_res.estado_validacion = estado_nuevo
            db.add(new_res)
            
    db.commit()
    
    # 2. LÓGICA DE CIERRE AUTOMÁTICO DE OTs
    # Solo si estamos validando, comprobamos si se pueden cerrar las OTs afectadas
    if validar:
        for oid in ot_ids_afectadas:
            # Obtener todos los items de esta orden
            all_items = db.query(models.OrdenItem).filter(models.OrdenItem.id_orden == oid).all()
            
            orden_completa = True
            if not all_items: orden_completa = False # Orden vacía no se cierra sola
            
            for it in all_items:
                # Buscar resultados de este item
                res_item = db.query(models.Resultado).filter(models.Resultado.id_item_orden == it.id_item_orden).all()
                
                # Criterio: Debe tener resultados y todos validados
                if not res_item:
                    orden_completa = False
                    break
                
                # Si hay algún resultado en borrador, la orden sigue abierta
                for r in res_item:
                    if r.estado_validacion != 'Validado':
                        orden_completa = False
                        break
                
                if not orden_completa: break
            
            if orden_completa:
                ot = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == oid).first()
                ot.estado = 'Finalizada'
                ot.fecha_cierre = datetime.now()
                db.add(ot)
                
        db.commit()
        
    return {"msg": "Datos guardados y estados actualizados"}

# --- CORRECCIONES ---
@router.post("/correcciones/reabrir")
def reabrir_muestra(req: schemas.ReabrirMuestraRequest, db: Session = Depends(database.get_db), user: models.Usuario = Depends(dependencies.get_current_user)):
    m = db.query(models.Muestra).filter(models.Muestra.codigo_laboratorio == req.cod_lims).first()
    if not m: raise HTTPException(404, "Código no encontrado")
    
    subs = db.query(models.SubmuestraAnalisis).filter(models.SubmuestraAnalisis.id_muestra_padre == m.id_muestra).all()
    ot_ids = set()
    
    for s in subs:
        s.estado_individual = "En Curso"
        items = db.query(models.OrdenItem).filter(models.OrdenItem.id_submuestra == s.id_submuestra).all()
        for i in items:
            ot_ids.add(i.id_orden)
            res = db.query(models.Resultado).filter(models.Resultado.id_item_orden == i.id_item_orden).all()
            for r in res:
                r.estado_validacion = "Corrección"
    
    for oid in ot_ids:
        ot = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == oid).first()
        if ot and ot.estado == "Finalizada":
            ot.estado = "Abierta"
            ot.fecha_cierre = None
            
    db.add(models.AuditLog(usuario=user.username, tabla_afectada="tb_muestras", id_registro=req.cod_lims, tipo_accion="REOPEN", motivo_cambio=req.motivo))
    db.commit()
    return {"msg": "Reabierta"}

# Router para cerrar las OT
@router.put("/ordenes/{id_orden}/cerrar")
def cerrar_orden(id_orden: int, db: Session = Depends(database.get_db), u: models.Usuario = Depends(dependencies.get_current_user)):
    ot = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == id_orden).first()
    if not ot: raise HTTPException(404, "Orden no encontrada")
    
    ot.estado = "Cerrada"
    db.commit()
    return {"msg": "Orden cerrada y bloqueada correctamente"}

# --- TRAZABILIDAD (RECURSOS) ---
@router.post("/ordenes/recursos", response_model=schemas.TrazaResponse)
def agregar_recurso_orden(t: schemas.TrazaCreate, db: Session = Depends(database.get_db)):
    # 1. Verificar Orden
    ot = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == t.id_orden).first()
    if not ot: raise HTTPException(404, "Orden no encontrada")
    
    # 2. Verificar Recurso y obtener datos
    nuevo = models.TrazabilidadOrden(id_orden=t.id_orden, tipo_recurso=t.tipo_recurso)
    nombre_display = ""
    cod_display = ""
    
    if t.tipo_recurso == "Reactivo":
        r = db.query(models.Reactivo).filter(models.Reactivo.id_reactivo == t.id_recurso).first()
        if not r: raise HTTPException(404, "Reactivo no encontrado")
        nuevo.id_reactivo = t.id_recurso
        nombre_display = r.nombre
        cod_display = r.cod_interno
        
    elif t.tipo_recurso == "Equipo":
        e = db.query(models.Equipo).filter(models.Equipo.id_equipo == t.id_recurso).first()
        if not e: raise HTTPException(404, "Equipo no encontrado")
        nuevo.id_equipo = t.id_recurso
        nombre_display = e.nombre_equipo
        cod_display = e.cod_interno
        
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    
    return schemas.TrazaResponse(
        id_traza=nuevo.id_traza,
        tipo_recurso=nuevo.tipo_recurso,
        nombre_recurso=nombre_display,
        cod_recurso=cod_display,
        fecha_uso=nuevo.fecha_uso
    )

@router.get("/ordenes/{id_orden}/recursos", response_model=List[schemas.TrazaResponse])
def listar_recursos_orden(id_orden: int, db: Session = Depends(database.get_db)):
    trazas = db.query(models.TrazabilidadOrden).filter(models.TrazabilidadOrden.id_orden == id_orden).all()
    res = []
    for t in trazas:
        if t.tipo_recurso == "Reactivo":
            obj = db.query(models.Reactivo).filter(models.Reactivo.id_reactivo == t.id_reactivo).first()
            lote_val = obj.numero_lote if (obj and hasattr(obj, 'numero_lote')) else "???"
            res.append({
                "id_traza": t.id_traza, "tipo_recurso": "Reactivo",
                "nombre_recurso": obj.nombre if obj else "Borrado",
                "cod_recurso": obj.cod_interno if obj else "???",
                "fecha_uso": t.fecha_uso
            })
        elif t.tipo_recurso == "Equipo":
            obj = db.query(models.Equipo).filter(models.Equipo.id_equipo == t.id_equipo).first()
            res.append({
                "id_traza": t.id_traza, "tipo_recurso": "Equipo",
                "nombre_recurso": obj.nombre_equipo if obj else "Borrado",
                "cod_recurso": obj.cod_interno if obj else "???",
                "fecha_uso": t.fecha_uso
            })
    return res

@router.delete("/ordenes/recursos/{id_traza}")
def quitar_recurso_orden(id_traza: int, db: Session = Depends(database.get_db)):
    db.query(models.TrazabilidadOrden).filter(models.TrazabilidadOrden.id_traza == id_traza).delete()
    db.commit()
    return {"msg": "Recurso desvinculado"}

# --- GESTIÓN DE ESTADOS ---
@router.put("/ordenes/{id_orden}/estado")
def actualizar_estado_orden(
    id_orden: int, 
    nuevo_estado: str, 
    db: Session = Depends(database.get_db)
):
    """
    Endpoint genérico para cambiar el estado de una orden.
    Usado por el módulo de Calidad para aprobar/cerrar OTs.
    """
    ot = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == id_orden).first()
    
    if not ot:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Actualizamos el estado
    ot.estado = nuevo_estado
    
    # Si el estado es de finalización, actualizamos la fecha de cierre administrativa
    if nuevo_estado in ["Cerrada", "Emitida"]:
        ot.fecha_cierre = datetime.now()
        
    db.commit()
    db.refresh(ot)
    return ot

@router.get("/ordenes/{id_orden}/resultados")
def obtener_resultados_completos_orden(id_orden: int, db: Session = Depends(database.get_db)):
    """
    Obtiene todos los resultados de una orden completa,
    resolviendo el nombre del parámetro usando el modelo Parametro existente.
    """
    # 1. Obtener todos los items de la orden
    items = db.query(models.OrdenItem).filter(models.OrdenItem.id_orden == id_orden).all()
    
    lista_final = []
    
    # 2. Iterar items para buscar resultados
    for item in items:
        resultados = db.query(models.Resultado).filter(models.Resultado.id_item_orden == item.id_item_orden).all()
        
        for r in resultados:
            nombre_p = f"ID: {r.id_parametro}"
            param_obj = db.query(models.Parametro).filter(models.Parametro.id_parametro == r.id_parametro).first()
            if param_obj:
                nombre_p = param_obj.nombre_parametro

            lista_final.append({
                "nombre_parametro": nombre_p,
                "valor_resultado": r.valor_resultado,
                "unidad": r.unidad or "",
                "fecha_hora_resultado": r.fecha_hora_resultado,
                "estado_validacion": r.estado_validacion
            })
            
    return lista_final