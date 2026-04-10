from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
import os
import database, models, schemas, dependencies

router = APIRouter(prefix="/reportes", tags=["Reporting"])

# Configurar Jinja2
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
env = Environment(loader=FileSystemLoader(templates_dir))

@router.get("/coa/{id_orden}", response_class=Response)
def generar_coa(id_orden: int, db: Session = Depends(database.get_db)):
    # 1. Obtener Datos
    ot = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == id_orden).first()
    if not ot: raise HTTPException(404, "Orden no encontrada")
    
    # Datos relacionados (asumiendo 1ª muestra para cabecera)
    item = db.query(models.OrdenItem).filter(models.OrdenItem.id_orden == id_orden).first()
    if not item: raise HTTPException(400, "Orden vacía")
    
    sub = db.query(models.SubmuestraAnalisis).filter(models.SubmuestraAnalisis.id_submuestra == item.id_submuestra).first()
    muestra = db.query(models.Muestra).filter(models.Muestra.id_muestra == sub.id_muestra_padre).first()
    recepcion = db.query(models.Recepcion).filter(models.Recepcion.id_recepcion == muestra.id_recepcion).first()
    cliente = db.query(models.Cliente).filter(models.Cliente.id_cliente == recepcion.id_cliente).first()
    pnt = db.query(models.PNT).filter(models.PNT.id_pnt == ot.id_pnt).first()
    analista = db.query(models.Usuario).filter(models.Usuario.id_usuario == ot.id_analista_responsable).first()
    
    # 2. Recopilar Resultados
    items = db.query(models.OrdenItem).filter(models.OrdenItem.id_orden == id_orden).all()
    lista_res = []
    
    for it in items:
        # ISO 17025: un CoA oficial sólo puede incluir resultados validados.
        resultados = db.query(models.Resultado).filter(
            models.Resultado.id_item_orden == it.id_item_orden,
            models.Resultado.estado_validacion == 'Validado'
        ).all()
        for r in resultados:
            param = db.query(models.Parametro).filter(models.Parametro.id_parametro == r.id_parametro).first()
            # Límites configurados
            conf = db.query(models.PNTParametroConfig).filter(
                models.PNTParametroConfig.id_pnt == ot.id_pnt, 
                models.PNTParametroConfig.id_parametro == r.id_parametro
            ).first()
            
            lista_res.append({
                "parametro": param.nombre_parametro,
                "valor": r.valor_resultado,
                "unidad": r.unidad or param.unidad_por_defecto,
                "min": conf.limite_min if conf else None,
                "max": conf.limite_max if conf else None,
                "metodo": pnt.codigo_pnt
            })

    # 3. Renderizar HTML
    template = env.get_template("coa_template.html")
    html_out = template.render(
        ot=ot, 
        muestra=muestra, 
        cliente=cliente, 
        pnt=pnt,
        analista=analista,
        resultados=lista_res,
        fecha_impresion=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    # 4. Generar PDF
    pdf_file = HTML(string=html_out).write_pdf()
    
    # 5. Respuesta Binaria
    return Response(content=pdf_file, media_type="application/pdf", headers={'Content-Disposition': f'attachment; filename="CoA_{ot.cod_orden}.pdf"'})
