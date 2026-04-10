import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Ejecución", layout="wide", page_icon="🔬")
utils.check_login()

# --- ESTADO PARA EL POPUP DE CONFIRMACIÓN ---
if "pending_save" not in st.session_state:
    st.session_state.pending_save = None
if "oos_warnings" not in st.session_state:
    st.session_state.oos_warnings = []

st.title("🔬 Ejecución Analítica")
tab_plan, tab_lab, tab_fix = st.tabs(["📅 Planificación", "🧪 Laboratorio (Grid)", "🛠️ Correcciones"])

# ==============================================================================
# TAB 1: PLANIFICACIÓN (Igual que antes)
# ==============================================================================
with tab_plan:
    st.subheader("Cola de Trabajo")
    res_pnt = utils.api_request("GET", "/metodos/pnts")
    if res_pnt and res_pnt.status_code == 200:
        pnts = {f"{p['codigo_pnt']}": p['id_pnt'] for p in res_pnt.json()}
        sel_pnt = st.selectbox("Filtrar por PNT:", list(pnts.keys()))
        
        if sel_pnt:
            res_pend = utils.api_request("GET", f"/ejecucion/pendientes/{pnts[sel_pnt]}")
            if res_pend.status_code == 200:
                data = res_pend.json()
                if data:
                    df = pd.DataFrame(data)
                    df.insert(0, "Sel", False)
                    ed = st.data_editor(
                        df[["Sel", "cod_lims", "referencia"]], 
                        hide_index=True, use_container_width=True,
                        column_config={"Sel": st.column_config.CheckboxColumn(required=True)}
                    )
                    
                    if st.button("🚀 Crear Orden de Trabajo", type="primary"):
                        sel_rows = ed[ed["Sel"]]
                        if not sel_rows.empty:
                            ot = utils.api_request("POST", "/ejecucion/ordenes", {"id_pnt": pnts[sel_pnt]}).json()
                            ids = [data[i]['id_submuestra'] for i in sel_rows.index]
                            utils.api_request("POST", f"/ejecucion/ordenes/{ot['id_orden']}/items", ids)
                            st.success(f"Orden {ot['cod_orden']} creada."); st.rerun()
                    else:
                        pass
                else: st.success("No hay muestras pendientes.")
    else: st.error("Error conexión")

# ==============================================================================
# TAB 2: LABORATORIO (GRID CON CONFIRMACIÓN OOS)
# ==============================================================================
with tab_lab:
    st.subheader("Hoja de Resultados y Trazabilidad")
    
    ots = utils.api_request("GET", "/ejecucion/ordenes").json()
    if ots:
        map_ot = {f"{o['cod_orden']} ({o['estado']})": o for o in ots}
        sel_ot = st.selectbox("Seleccionar Orden:", list(map_ot.keys()))
        ot_obj = map_ot[sel_ot]
        
        st.divider()
        
        # --- ESTRUCTURA DE COLUMNAS (IZQ: GRID | DER: RECURSOS) ---
        c_grid, c_resources = st.columns([3, 1])
        
        # --- RECURSOS ---
        with c_resources:
            st.info("📦 **Recursos (PNT)**")
            
            # 1. Cargar datos
            req_resp = utils.api_request("GET", f"/metodos/recursos/{ot_obj['id_pnt']}")
            requisitos = req_resp.json() if req_resp.status_code == 200 else []
            
            vin_resp = utils.api_request("GET", f"/ejecucion/ordenes/{ot_obj['id_orden']}/recursos")
            vinculados = []
            if vin_resp.status_code == 200:
                data_v = vin_resp.json()
                if isinstance(data_v, list): vinculados = data_v

            # 2. Cargar Inventario
            stock_reactivos = utils.api_request("GET", "/reactivos/").json()
            stock_equipos = utils.api_request("GET", "/equipos/").json()
            
            # --- LISTA TEMPORAL PARA GUARDAR ELECCIONES ---
            datos_para_vincular = [] 

            if not requisitos:
                st.caption("ℹ️ PNT sin requisitos.")
            else:
                st.write("**Selecciona los lotes/equipos a usar:**")
                
                for req in requisitos:
                    st.markdown(f"🔸 {req.get('nombre_tipo_necesario', 'Recurso')}")
                    
                    # Filtramos stock disponible
                    candidatos = []
                    if req['tipo_recurso'] == "Reactivo":
                        candidatos = [r for r in stock_reactivos if r.get('id_tipo_reactivo') == req['id_tipo_necesario']]
                    else:
                        candidatos = [e for e in stock_equipos if e.get('id_tipo_equipo') == req['id_tipo_necesario']]
                    
                    if not candidatos:
                        st.error("❌ Sin stock disponible")
                    else:
                        # Creamos el desplegable
                        opts = {f"{c.get('cod_interno')} | {c.get('nombre') or c.get('nombre_equipo')}": (c.get('id_reactivo') or c.get('id_equipo')) for c in candidatos}
                        
                        sel = st.selectbox(
                            "Seleccionar:", 
                            ["..."] + list(opts.keys()), 
                            key=f"req_{req['id_pnt_recurso']}",
                            label_visibility="collapsed" # Ocultamos etiqueta para ahorrar espacio
                        )
                        
                        # Si el usuario ha elegido algo, lo apuntamos en la lista
                        if sel != "...":
                            datos_para_vincular.append({
                                "id_orden": ot_obj['id_orden'],
                                "tipo_recurso": req['tipo_recurso'],
                                "id_recurso": opts[sel]
                            })
                    st.divider()

                # --- BOTÓN MAESTRO AL FINAL ---
                if st.button("🔗 VINCULAR TODO LO SELECCIONADO", type="primary", use_container_width=True):
                    if not datos_para_vincular:
                        st.warning("⚠️ No has seleccionado nada en los desplegables de arriba.")
                    else:
                        # Barra de progreso visual
                        bar = st.progress(0)
                        for i, payload in enumerate(datos_para_vincular):
                            utils.api_request("POST", "/ejecucion/ordenes/recursos", payload)
                            bar.progress((i + 1) / len(datos_para_vincular))
                        
                        st.success("✅ Recursos vinculados")
                        st.rerun()

            # Recursos ya vinculados
            if vinculados:
                st.caption(f"✅ **Ya Vinculados ({len(vinculados)}):**")
                for v in vinculados:
                    c1, c2 = st.columns([4,1])
                    nombre = v.get('nombre_recurso', 'Desconocido')
                    c1.text(f"🔹 {nombre}")
                    if c2.button("🗑️", key=f"del_{v['id_traza']}"):
                        utils.api_request("DELETE", f"/ejecucion/ordenes/recursos/{v['id_traza']}")
                        st.rerun()
        # --- GRID DE RESULTADOS ---
        with c_grid:
            conf = utils.api_request("GET", f"/metodos/config/{ot_obj['id_pnt']}").json()
            pars = utils.api_request("GET", "/metodos/parametros").json()
            map_p_name = {p['id_parametro']: p['nombre_parametro'] for p in pars}
            cols_p = {str(c['id_parametro']): map_p_name.get(c['id_parametro'], f"ID{c['id_parametro']}") for c in conf}
            
            limits_map = {}
            for c in conf:
                p_name = map_p_name.get(c['id_parametro'])
                if p_name:
                    limits_map[p_name] = {"min": c['limite_min'], "max": c['limite_max'], "id": c['id_parametro']}

            # Carga del Grid
            grid = utils.api_request("GET", f"/ejecucion/ordenes/{ot_obj['id_orden']}/grid").json()
            
            if grid:
                rows = []
                for g in grid:
                    if g['estado'] != 'Validado' or ot_obj['estado'] == 'Finalizada':
                        row = {
                            "id_item": g['id_item_orden'],
                            "Muestra": g['cod_lims'],
                            "Ref": g['referencia'],
                            "Validar": (g['estado'] == 'Validado')
                        }
                        for pid, pname in cols_p.items():
                            row[pname] = g['resultados'].get(pid, "")
                        rows.append(row)
                
                if rows:
                    df_grid = pd.DataFrame(rows)
                    col_defs = {
                        "id_item": st.column_config.Column(disabled=True),
                        "Muestra": st.column_config.Column(disabled=True),
                        "Ref": st.column_config.Column(disabled=True),
                        "Validar": st.column_config.CheckboxColumn("✅ Validar", default=False)
                    }
                    
                    # --- ZONA DE ALERTA OOS ---
                    if st.session_state.pending_save:
                        st.error("⚠️ **ALERTA DE CALIDAD: OOS DETECTADO**")
                        for err in st.session_state.oos_warnings: st.markdown(f"- {err}")
                        
                        cc1, cc2 = st.columns([1, 4])
                        with cc1:
                            if st.button("☣️ CONFIRMAR DESVIACIÓN", type="primary"):
                                p_d, p_v = st.session_state.pending_save
                                if p_d: utils.api_request("POST", "/ejecucion/resultados_batch?validar=false", p_d)
                                if p_v: utils.api_request("POST", "/ejecucion/resultados_batch?validar=true", p_v)
                                st.session_state.pending_save = None
                                st.session_state.oos_warnings = []
                                st.rerun()
                        with cc2:
                            if st.button("❌ Corregir"):
                                st.session_state.pending_save = None
                                st.session_state.oos_warnings = []
                                st.rerun()
                        st.divider()

                    # GRID EDITABLE
                    if ot_obj['estado'] == 'Finalizada':
                        st.dataframe(df_grid, use_container_width=True, hide_index=True)
                    else:
                        ed_grid = st.data_editor(df_grid, column_config=col_defs, use_container_width=True, hide_index=True)
                    
                        # Guardar con detección OOS
                        if st.button("💾 Analizar y Guardar"):
                            payload_draft = []
                            payload_valid = []
                            oos_list = []
                            
                            for idx, row in ed_grid.iterrows():
                                item_id = row['id_item']
                                do_valid = row['Validar']
                                muestra_cod = row['Muestra']
                                
                                for p_name, p_info in limits_map.items():
                                    if p_name in row:
                                        val_str = str(row[p_name])
                                        if val_str and val_str.strip():
                                            obj = {"id_item_orden": item_id, "id_parametro": p_info['id'], "valor_resultado": val_str}
                                            if do_valid: payload_valid.append(obj)
                                            else: payload_draft.append(obj)
                                            
                                            # CHECK OOS
                                            if do_valid:
                                                try:
                                                    val_num = float(val_str)
                                                    mn, mx = p_info['min'], p_info['max']
                                                    if mn is not None and val_num < mn:
                                                        oos_list.append(f"**{muestra_cod}** - {p_name}: {val_num} < {mn}")
                                                    if mx is not None and val_num > mx:
                                                        oos_list.append(f"**{muestra_cod}** - {p_name}: {val_num} > {mx}")
                                                except: pass
                            
                            if oos_list:
                                st.session_state.pending_save = (payload_draft, payload_valid)
                                st.session_state.oos_warnings = oos_list
                                st.rerun()
                            else:
                                if payload_draft: utils.api_request("POST", "/ejecucion/resultados_batch?validar=false", payload_draft)
                                if payload_valid: utils.api_request("POST", "/ejecucion/resultados_batch?validar=true", payload_valid)
                                st.success("Guardado.")
                                st.rerun()

        # --- DESCARGA CoA (solo cuando la orden ya está finalizada o cerrada) ---
        if ot_obj['estado'] in ('Finalizada', 'Cerrada'):
            pdf_resp = utils.api_request("GET", f"/reportes/coa/{ot_obj['id_orden']}")
            cod_orden_safe = ot_obj.get('cod_orden') or f"OT-{ot_obj['id_orden']:05d}"
            if pdf_resp is not None and pdf_resp.status_code == 200:
                st.download_button(
                    label="📄 Descargar Certificado de Análisis (CoA)",
                    data=pdf_resp.content,
                    file_name=f"CoA_{cod_orden_safe}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.warning("No se pudo generar el Certificado de Análisis en este momento.")

        # BOTÓN CERRAR ORDEN (CON VALIDACIÓN DE RECURSOS)
        st.divider()
        if st.button("🔒 Cerrar Orden de Trabajo", type="primary"):
            # Comprobación de Trazabilidad
            req_check = utils.api_request("GET", f"/metodos/recursos/{ot_obj['id_pnt']}").json()
            vin_check = utils.api_request("GET", f"/ejecucion/ordenes/{ot_obj['id_orden']}/recursos").json()

            if req_check and not vin_check:
                st.error("⚠️ CALIDAD: No puedes cerrar sin vincular los equipos/reactivos requeridos (Panel Derecho).")
            else:
                utils.api_request("PUT", f"/ejecucion/ordenes/{ot_obj['id_orden']}/cerrar")
                st.success("Orden cerrada.")
                st.rerun()

# --- TAB 3: CORRECCIONES ---
with tab_fix:
    st.subheader("Gestión de Incidencias")
    c1, c2 = st.columns(2)
    with c1:
        cod = st.text_input("Código Muestra:")
        mot = st.text_area("Motivo:")
        if st.button("🔓 Reabrir", type="primary"):
            if cod and mot:
                r = utils.api_request("POST", "/ejecucion/correcciones/reabrir", {"cod_lims": cod, "motivo": mot})
                if r.status_code == 200: st.success("Reabierta"); st.rerun()
                else: st.error(r.text)