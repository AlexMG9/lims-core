import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Inventario", layout="wide", page_icon="🧪")
utils.check_login()

st.title("🧪 Gestión de Inventario")

def mostrar_leyenda():
    st.markdown("""
    <div style="display: flex; gap: 20px; font-size: 0.9rem; margin-bottom: 10px; padding: 5px; border-radius: 5px; background-color: transparent;">
        <div style="display: flex; align-items: center;">
            <span style="background-color: #ffcccb; width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; border: 1px solid #ccc;"></span>
            <span style="color: white;">Caducado</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background-color: #ffe68c; width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; border: 1px solid #ccc;"></span>
            <span style="color: white;">Próximo a caducar (< 30 días)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background-color: white; width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; border: 1px solid #ccc;"></span>
            <span style="color: white;">Vigente</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

res = utils.api_request("GET", "/reactivos/")
df_master = pd.DataFrame()
if res and res.status_code == 200:
    data = res.json()
    if data:
        df_master = pd.DataFrame(data)

tipos_r = utils.api_request("GET", "/reactivos/tipos").json()
map_t = {t['nombre_tipo']: t['id_tipo_reactivo'] for t in tipos_r} if tipos_r else {}

t_react, t_patron, t_alta_ext, t_alta_int = st.tabs([
    "🧴 Stock Reactivos", 
    "🏆 Stock Patrones (MR/MRC)", 
    "🚚 Alta Compra (Externo)", 
    "⚗️ Alta Preparación (Interno)"
])

# 1. STOCK REACTIVOS
with t_react:
    st.subheader("Inventario de Trabajo Diario")
    if not df_master.empty:
        mask_react = ~df_master['clasificacion'].isin(['MR', 'MRC', 'Patron', 'Patron Interno'])
        df_r = df_master[mask_react].copy()
        if not df_r.empty:
            mostrar_leyenda()
            st.dataframe(df_r[["cod_interno", "nombre", "clasificacion", "numero_lote", "proveedor", "fecha_caducidad", "fecha_apertura", "cantidad_inicial", "unidad"]].style.apply(utils.resaltar_caducados, axis=1), use_container_width=True, hide_index=True)
            st.divider()
            c1, c2 = st.columns([3, 2])
            with c1:
                opts = {f"{r['cod_interno']} | {r['nombre']}": r for i, r in df_r.iterrows()}
                if opts:
                    sel = st.selectbox("Seleccionar para Acciones:", list(opts.keys()), key="sel_react")
                    obj_sel = opts[sel]
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        if obj_sel.get('fecha_apertura'): st.info(f"🔓 Abierto: {obj_sel['fecha_apertura']}")
                        else:
                            if st.button("🍾 Registrar Apertura (HOY)", key="open_react", type="primary"):
                                utils.api_request("PATCH", f"/reactivos/{obj_sel['id_reactivo']}/abrir")
                                st.rerun()
                    with cb2:
                        if st.button("🗑️ Dar de Baja", key="del_react"):
                            utils.api_request("DELETE", f"/reactivos/{obj_sel['id_reactivo']}")
                            st.rerun()
        else: st.info("No hay reactivos.")
    else: st.warning("Inventario vacío.")

# 2. STOCK PATRONES
with t_patron:
    st.subheader("Material de Referencia y Patrones")
    if not df_master.empty:
        mask_pat = df_master['clasificacion'].isin(['MR', 'MRC', 'Patron', 'Patron Interno'])
        df_p = df_master[mask_pat].copy()
        if not df_p.empty:
            mostrar_leyenda()
            st.dataframe(df_p[["cod_interno", "clasificacion", "nombre", "numero_lote", "fecha_caducidad", "fecha_apertura", "ruta_certificado"]].style.apply(utils.resaltar_caducados, axis=1), use_container_width=True, hide_index=True)
            st.divider()
            opts_p = {f"{r['cod_interno']} | {r['nombre']}": r for i, r in df_p.iterrows()}
            if opts_p:
                sel_p = st.selectbox("Seleccionar Patrón:", list(opts_p.keys()), key="sel_pat")
                obj_p = opts_p[sel_p]
                if st.button("🍾 Registrar Apertura Patrón", key="open_pat"):
                     utils.api_request("PATCH", f"/reactivos/{obj_p['id_reactivo']}/abrir")
                     st.rerun()
                k1, k2 = st.columns(2)
                with k1:
                    if obj_p.get('ruta_certificado'):
                        url = f"{utils.API_URL}/uploads/{obj_p['ruta_certificado']}"
                        st.markdown(f"[📥 **Descargar PDF**]({url})", unsafe_allow_html=True)
                    else: st.error("⚠️ Falta Certificado")
                with k2:
                    upl = st.file_uploader("Subir PDF", type="pdf", key="upl_pat")
                    if upl and st.button("Subir"):
                        files = {'file': (upl.name, upl, 'application/pdf')}
                        h = {"Authorization": f"Bearer {st.session_state.token}"}
                        utils.api_request("POST", f"/reactivos/{obj_p['id_reactivo']}/upload_certificado", None).status_code
                        requests.post(f"{utils.API_URL}/reactivos/{obj_p['id_reactivo']}/upload_certificado", files=files, headers=h)
                        st.rerun()
        else: st.info("No hay patrones.")

# 3. ALTA COMPRA
with t_alta_ext:
    st.subheader("🚚 Registro de Material Comprado")
    with st.form("form_compra"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre del Producto *")
        clas = c2.selectbox("Clasificación", ["Reactivo", "Patron", "MR", "MRC"])
        c3, c4 = st.columns(2)
        prov = c3.text_input("Proveedor *")
        lote = c4.text_input("Nº Lote Fabricante *")
        c5, c6 = st.columns(2)
        cant = c5.number_input("Cantidad", min_value=0.0, step=0.1)
        ud = c6.selectbox("Unidad", ["L", "mL", "kg", "g", "mg", "ud"])
        cad = st.date_input("Fecha Caducidad *")
        tipo_sel = st.selectbox("Familia/Tipo (Para PNTs)", ["Sin asignar"] + list(map_t.keys()))
        
        if st.form_submit_button("Registrar Entrada"):
            if n and prov and lote:
                p = { "nombre": n, "clasificacion": clas, "proveedor": prov, "numero_lote": lote, "cantidad_inicial": cant, "unidad": ud, "fecha_caducidad": str(cad), "id_tipo_reactivo": map_t.get(tipo_sel) if tipo_sel != "Sin asignar" else None }
                r = utils.api_request("POST", "/reactivos/", p)
                if r.status_code == 200: st.success("Registrado."); st.rerun()
                else: st.error(r.text)

# 4. ALTA PREPARACIÓN (COCINA)
with t_alta_int:
    st.subheader("⚗️ Preparación de Disoluciones Trazables")
    pnts = utils.api_request("GET", "/metodos/pnts").json()
    if pnts:
        mp = {p['codigo_pnt']: p['id_pnt'] for p in pnts}
        s_pnt = st.selectbox("1. PNT a preparar:", list(mp.keys()))
        recetas = utils.api_request("GET", f"/metodos/recetas/{mp[s_pnt]}").json()
        if recetas:
            opts_rec = {f"{r['receta']['nombre_receta']} (Ref: {r['receta']['cantidad_referencia']} {r['receta']['unidad_referencia']})": r for r in recetas}
            s_rec = st.selectbox("2. Seleccionar Receta:", list(opts_rec.keys()))
            receta_obj = opts_rec[s_rec]
            
            st.divider()
            
            tipo_preparado = st.radio("Tipo de Salida:", ["Disolucion (Uso General)", "Patron Interno (Para calibrar)"], horizontal=True)
            clas_final = "Patron Interno" if "Patron" in tipo_preparado else "Disolucion"
            
            st.markdown("#### 3. Escanear Ingredientes")
            padres_seleccionados = [] 
            todo_listo = True
            
            for ing in receta_obj['ingredientes']:
                st.markdown(f"**🔸 Necesario: {ing['tipo']} ({ing['cantidad']})**")
                
                # Filtrar stock por tipo de reactivo requerido
                target_id = ing.get('id_tipo_reactivo')
                
                # Filtrar DF si existe columna y tenemos ID
                candidatos = df_master
                if target_id is not None and not df_master.empty and 'id_tipo_reactivo' in df_master.columns:
                    # NaN-safe: pandas puede devolver float en columnas con nulos
                    candidatos = df_master[df_master['id_tipo_reactivo'] == target_id]
                
                if candidatos.empty:
                    st.error(f"❌ No hay stock de '{ing['tipo']}' en inventario.")
                    todo_listo = False
                    opts_inv = {}
                else:
                    opts_inv = {f"{r['cod_interno']} | {r['nombre']} (Lote: {r['numero_lote']})": r['id_reactivo'] for i,r in candidatos.iterrows()}
                
                sel_padre = st.selectbox(f"Seleccionar Lote:", ["Seleccionar..."] + list(opts_inv.keys()), key=f"ing_{ing['id_ingrediente']}")
                
                if sel_padre != "Seleccionar...":
                    padres_seleccionados.append([opts_inv[sel_padre], ing['cantidad']])
                else:
                    todo_listo = False
            
            st.divider()
            c_cant, c_btn = st.columns([1, 2])
            tipo_preparado = c_cant.radio("Tipo de Salida:", ["Disolucion", "Patron Interno"])
            clas_final = "Patron Interno" if "Patron" in tipo_preparado else "Disolucion"
            cant_real = c_cant.number_input("Cantidad Final Preparada:", value=receta_obj['receta']['cantidad_referencia'])
            
            if c_btn.button("🔥 GENERAR PREPARADO", type="primary", disabled=not todo_listo):
                payload = {
                    "id_receta": receta_obj['receta']['id_receta'],
                    "cantidad_preparada": cant_real,
                    "ids_padres": padres_seleccionados
                }
                r = utils.api_request("POST", f"/reactivos/preparar?clasificacion={clas_final}", payload)
                
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ Generado: **{data['cod_interno']}** ({data['numero_lote']})")
                else:
                    st.error(f"Error ({r.status_code}): {r.text}")
        else: st.warning("Sin recetas.")
