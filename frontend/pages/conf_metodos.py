import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Métodos", layout="wide", page_icon="⚙️")
utils.check_login()

st.title("⚙️ Gestión de Métodos y Ensayos")
t1, t2, t3, t4, t5 = st.tabs(["1. PNTs", "2. Parámetros", "3. Configuración (Límites)", "4. Recetas (Preparaciones)", "5. Recursos Necesarios"])

# ==============================================================================
# TAB 1: GESTIÓN DE PNTs
# ==============================================================================
with t1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("##### Nuevo Procedimiento")
        with st.form("np"):
            c = st.text_input("Código (ej: PNT-01)")
            n = st.text_input("Nombre del Ensayo")
            if st.form_submit_button("Crear PNT"):
                utils.api_request("POST", "/metodos/pnts", {"codigo_pnt": c, "nombre_ensayo": n})
                st.success("Creado")
                st.rerun()
    
    with c2:
        res = utils.api_request("GET", "/metodos/pnts")
        if res and res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("Sin datos.")

# ==============================================================================
# TAB 2: GESTIÓN DE PARÁMETROS
# ==============================================================================
with t2:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("##### Nuevo Parámetro")
        with st.form("npa"):
            nm = st.text_input("Nombre (ej: pH)")
            u = st.text_input("Unidad (ej: ud)")
            if st.form_submit_button("Crear Parámetro"):
                utils.api_request("POST", "/metodos/parametros", {"nombre_parametro": nm, "unidad_por_defecto": u})
                st.success("Creado")
                st.rerun()
    
    with c2:
        res = utils.api_request("GET", "/metodos/parametros")
        if res and res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                st.dataframe(df, use_container_width=True)

# ==============================================================================
# TAB 3: CONFIGURACIÓN DE LÍMITES (RESTITUIDO COMPLETO)
# ==============================================================================
with t3:
    st.subheader("Configuración de Límites y Especificaciones")
    
    pnts = utils.api_request("GET", "/metodos/pnts").json()
    pars = utils.api_request("GET", "/metodos/parametros").json()
    
    if pnts and pars:
        map_pnt = {f"{p['codigo_pnt']}": p['id_pnt'] for p in pnts}
        map_par = {f"{p['nombre_parametro']}": p['id_parametro'] for p in pars}
        map_par_inv = {v: k for k, v in map_par.items()} # ID -> Nombre
        
        # Selector Principal
        sel_pnt_key = st.selectbox("Selecciona PNT a configurar:", list(map_pnt.keys()))
        id_pnt_actual = map_pnt[sel_pnt_key]
        
        st.divider()
        
        c_add, c_list = st.columns([1, 2])
        
        # A. AÑADIR NUEVO LÍMITE
        with c_add:
            st.markdown("##### 🔗 Vincular Nuevo Parámetro")
            with st.form("link_config"):
                sel_par = st.selectbox("Parámetro", list(map_par.keys()))
                lod = st.number_input("LOD", value=0.0, format="%.4f")
                mn = st.number_input("Mínimo", value=None, step=None, placeholder="Sin límite")
                mx = st.number_input("Máximo", value=None, step=None, placeholder="Sin límite")
                
                if st.form_submit_button("Añadir"):
                    p = {"id_pnt": id_pnt_actual, "id_parametro": map_par[sel_par], 
                         "limite_deteccion_LOD": lod, "limite_min": mn, "limite_max": mx}
                    r = utils.api_request("POST", "/metodos/config", p)
                    if r.status_code == 200: st.success("Añadido"); st.rerun()
                    else: st.error(r.text)

        # B. LISTAR Y EDITAR EXISTENTES
        with c_list:
            st.markdown("##### 📋 Parámetros Actuales (Edición)")
            res_conf = utils.api_request("GET", f"/metodos/config/{id_pnt_actual}")
            
            if res_conf and res_conf.status_code == 200:
                configs = res_conf.json()
                if configs:
                    # Selector para editar
                    opciones_conf = {f"{map_par_inv.get(c['id_parametro'])} (Límites: {c['limite_min']} - {c['limite_max']})": c for c in configs}
                    sel_conf = st.selectbox("Selecciona parámetro para EDITAR LÍMITES:", list(opciones_conf.keys()))
                    conf_activa = opciones_conf[sel_conf]
                    
                    with st.form("edit_limits"):
                        c1, c2, c3 = st.columns(3)
                        # Pre-llenamos con los valores actuales
                        n_lod = c1.number_input("LOD", value=conf_activa['limite_deteccion_LOD'], format="%.4f")
                        n_min = c2.number_input("Mínimo", value=conf_activa['limite_min'])
                        n_max = c3.number_input("Máximo", value=conf_activa['limite_max'])
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            p = {"id_pnt": id_pnt_actual, "id_parametro": conf_activa['id_parametro'], 
                                 "limite_deteccion_LOD": n_lod, "limite_min": n_min, "limite_max": n_max}
                            r = utils.api_request("PUT", f"/metodos/config/{conf_activa['id_config']}", p)
                            if r.status_code == 200: st.success("Actualizado"); st.rerun()
                            else: st.error(r.text)
                    
                    if st.button("🗑️ Desvincular este parámetro"):
                         utils.api_request("DELETE", f"/metodos/config/{conf_activa['id_config']}")
                         st.rerun()

                    # Tabla resumen visual
                    df_c = pd.DataFrame(configs)
                    df_c['Parámetro'] = df_c['id_parametro'].map(map_par_inv)
                    st.dataframe(df_c[["Parámetro", "limite_min", "limite_max", "limite_deteccion_LOD"]], use_container_width=True, hide_index=True)
                else:
                    st.info("Sin parámetros asignados.")
    else:
        st.warning("Crea PNTs y Parámetros primero.")

# ==============================================================================
# TAB 4: RECETAS (PREPARACIONES) - RESTITUIDO
# ==============================================================================
with t4:
    st.subheader("👨‍🍳 Libro de Recetas por PNT")
    
    # Cargar datos necesarios
    pnts = utils.api_request("GET", "/metodos/pnts").json()
    tipos_re = utils.api_request("GET", "/reactivos/tipos").json()
    
    if pnts and tipos_re:
        map_pnt = {f"{p['codigo_pnt']}": p['id_pnt'] for p in pnts}
        map_tipo = {t['nombre_tipo']: t['id_tipo_reactivo'] for t in tipos_re}
        
        sel_pnt = st.selectbox("Selecciona PNT para ver sus recetas:", list(map_pnt.keys()), key="sel_pnt_receta")
        id_pnt = map_pnt[sel_pnt]
        
        st.divider()
        
        # 1. Definir Nueva Receta (Cabecera)
        with st.expander("➕ Definir Nueva Receta (Ej: Fase Móvil A)"):
            with st.form("new_recipe"):
                c1, c2 = st.columns(2)
                nom = c1.text_input("Nombre Preparado (ej: Fase Móvil A)")
                cad = c2.number_input("Caducidad (Horas)", value=24)
                cant = c1.number_input("Cantidad Ref.", value=1000.0)
                ud = c2.selectbox("Unidad", ["mL", "L", "g"])
                
                if st.form_submit_button("Crear Receta"):
                    p = {"id_pnt": id_pnt, "nombre_receta": nom, "cantidad_referencia": cant, "unidad_referencia": ud, "caducidad_horas": cad}
                    r = utils.api_request("POST", "/metodos/recetas", p)
                    if r.status_code == 200: st.success("Receta creada"); st.rerun()
                    else: st.error(r.text)
        
        # 2. Listar Recetas y Añadir Ingredientes
        recetas_data = utils.api_request("GET", f"/metodos/recetas/{id_pnt}").json()
        
        if recetas_data:
            st.markdown("##### 📋 Recetas Definidas")
            for item in recetas_data:
                r = item['receta']
                ings = item['ingredientes']
                
                with st.container(border=True):
                    # Cabecera de la Receta
                    c_head, c_act = st.columns([3, 1])
                    c_head.markdown(f"**🔹 {r['nombre_receta']}**")
                    c_head.caption(f"Ref: {r['cantidad_referencia']} {r['unidad_referencia']} | Caducidad: {r['caducidad_horas']}h")
                    
                    # Añadir Ingrediente
                    c1, c2, c3 = st.columns([2, 1, 1])
                    sel_ing = c1.selectbox(f"Añadir Ingrediente a '{r['nombre_receta']}':", list(map_tipo.keys()), key=f"sel_{r['id_receta']}")
                    q_ing = c2.number_input("Cant:", key=f"q_{r['id_receta']}", value=0.0)
                    
                    if c3.button("➕ Añadir", key=f"btn_{r['id_receta']}"):
                        utils.api_request("POST", "/metodos/recetas/ingredientes", {
                            "id_receta": r['id_receta'],
                            "id_tipo_reactivo": map_tipo[sel_ing],
                            "cantidad_necesaria": q_ing
                        })
                        st.rerun()
                    
                    # Mostrar Ingredientes Actuales
                    if ings:
                        st.table(pd.DataFrame(ings)[["tipo", "cantidad"]])
                    else:
                        st.info("Esta receta aún no tiene ingredientes.")
        else:
            st.info("No hay recetas definidas para este PNT.")
    else:
        st.warning("Necesitas crear PNTs y Tipos de Reactivos primero.")

# ==============================================================================
# TAB 5: RECURSOS NECESARIOS
# ==============================================================================
with t5:
    st.subheader("📋 Definición de Material Necesario")
    st.caption("Define qué TIPOS de reactivos o equipos son obligatorios para ejecutar este ensayo.")
    
    # Cargamos PNTs para el selector
    pnts_res = utils.api_request("GET", "/metodos/pnts").json()
    if pnts_res:
        map_pnt_res = {p['codigo_pnt']: p['id_pnt'] for p in pnts_res}
        sel_pnt_res = st.selectbox("Seleccionar PNT:", list(map_pnt_res.keys()), key="sel_pnt_res")
        id_pnt_res = map_pnt_res[sel_pnt_res]
        
        st.divider()
        col_form, col_tabla = st.columns([1, 2])
        
        # --- FORMULARIO AÑADIR ---
        with col_form:
            st.markdown("##### Añadir Requisito")
            tipo_req = st.radio("Tipo Recurso:", ["Reactivo", "Equipo"], horizontal=True)
            
            map_tipos = {}
            if tipo_req == "Reactivo":
                # Buscamos tipos de reactivos (API existente)
                tipos = utils.api_request("GET", "/reactivos/tipos").json()
                if tipos:
                    map_tipos = {t['nombre_tipo']: t['id_tipo_reactivo'] for t in tipos}
            else:
                # Buscamos tipos de equipos (API existente tb_tipos_equipo?)
                res_t_eq = utils.api_request("GET", "/equipos/tipos")
                if res_t_eq and res_t_eq.status_code == 200:
                    tipos = res_t_eq.json()
                    map_tipos = {t['nombre_tipo']: t['id_tipo_equipo'] for t in tipos}
                else:
                    st.warning("⚠️ No se pudieron cargar Tipos de Equipo. Revisa /equipos/tipos")

            if map_tipos:
                sel_tipo = st.selectbox("Tipo Necesario:", list(map_tipos.keys()))
                
                if st.button("➕ Añadir Requisito"):
                    payload = {
                        "id_pnt": id_pnt_res,
                        "tipo_recurso": tipo_req,
                        "id_tipo_necesario": map_tipos[sel_tipo],
                        "cantidad_necesaria": 1.0
                    }
                    # Usamos el endpoint nuevo que mapeamos a tb_pnt_recursos
                    r = utils.api_request("POST", "/metodos/recursos", payload)
                    if r.status_code == 200:
                        st.success("Añadido")
                        st.rerun()
                    else:
                        st.error(f"Error: {r.text}")
            else:
                st.info("No hay tipos disponibles para seleccionar.")

        # --- TABLA LISTADO ---
        with col_tabla:
            st.markdown(f"##### 📝 Lista para {sel_pnt_res}")
            # Endpoint GET que acabamos de crear
            reqs = utils.api_request("GET", f"/metodos/recursos/{id_pnt_res}").json()
            
            if reqs:
                # Mostramos tabla simple
                df_req = pd.DataFrame(reqs)
                # Renombramos columnas para que se lea mejor
                if not df_req.empty and 'nombre_tipo_necesario' in df_req.columns:
                    st.dataframe(df_req[["tipo_recurso", "nombre_tipo_necesario"]], use_container_width=True, hide_index=True)
                    
                    # Botones de borrar (Iteramos uno a uno)
                    st.caption("Eliminar requisitos:")
                    for r in reqs:
                        if st.button(f"🗑️ Quitar {r['nombre_tipo_necesario']}", key=f"del_req_{r['id_pnt_recurso']}"):
                            utils.api_request("DELETE", f"/metodos/recursos/{r['id_pnt_recurso']}")
                            st.rerun()
            else:
                st.info("Este PNT aún no tiene requisitos definidos.")