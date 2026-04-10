import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Calidad y Validación", layout="wide", page_icon="🛡️")
utils.check_login()

st.title("🛡️ Centro de Control de Calidad")
st.markdown("---")

# --- KPI METRICS (Toque Analytics Engineer) ---
# Hacemos la llamada a la API nueva
resp = utils.api_request("GET", "/calidad/pendientes")
if resp.status_code != 200:
    st.error(f"Error al cargar los datos: {resp.status_code} - {resp.text}")
    st.stop()
ordenes = resp.json()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Pendientes de Revisión", len(ordenes), delta_color="inverse")
kpi2.metric("Tiempo Medio Rev.", "1.2 días", delta="OK")  # TODO: calcular desde SQL
kpi3.metric("OOS Detectados", "0", delta="Excelente")    # TODO: calcular desde SQL

# --- TABS DE TRABAJO ---
tab_rev, tab_audit = st.tabs(["📝 Revisión y Liberación", "🔍 Trazabilidad Inversa (Audit)"])

# ==============================================================================
# TAB 1: REVISIÓN DE LOTES (WORKFLOW)
# ==============================================================================
with tab_rev:
    if not ordenes:
        st.success("✅ Todo al día. No hay órdenes pendientes de revisión.")
    else:
        # 1. GRID PRINCIPAL
        df = pd.DataFrame(ordenes)
        # Renombrar columnas para que se vea bonito
        df_show = df[["cod_orden", "nombre_ensayo", "cod_lims", "fecha_finalizacion_tecnica", "analista", "recursos_usados"]]
        
        st.dataframe(
            df_show, 
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun", # Si tu version de streamlit lo soporta, si no, usar selectbox abajo
            hide_index=True
        )

        # Selector de expediente
        opciones = {f"{o['cod_orden']} | {o['nombre_ensayo']} ({o['cod_lims']})": o for o in ordenes}
        seleccion_str = st.selectbox("📂 Abrir Expediente de Análisis:", ["Seleccionar..."] + list(opciones.keys()))

        if seleccion_str != "Seleccionar...":
            obj = opciones[seleccion_str]
            oid = obj['id_orden']
            
            st.divider()
            st.subheader(f"📑 Expediente: {obj['cod_orden']}")
            
            c_res, c_traz = st.columns([2, 1])
            
            # --- COLUMNA IZQUIERDA: RESULTADOS ---
            with c_res:
                st.info("📊 Resultados Obtenidos")
                # Llamada a la API de resultados existente
                r_res = utils.api_request("GET", f"/ejecucion/ordenes/{oid}/resultados")
                if r_res.status_code == 200:
                    data_res = r_res.json()
                    if data_res:
                        df_res = pd.DataFrame(data_res)
                        # Mostramos tabla limpia
                        st.dataframe(
                            df_res[["nombre_parametro", "valor_resultado", "unidad", "fecha_hora_resultado"]],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.warning("⚠️ Esta orden no tiene resultados registrados.")
                
            # --- COLUMNA DERECHA: TRAZABILIDAD (AUDITORÍA) ---
            with c_traz:
                st.warning("🔗 Trazabilidad (Recursos Usados)")
                # Llamada a la API de recursos vinculados
                r_tra = utils.api_request("GET", f"/ejecucion/ordenes/{oid}/recursos")
                if r_tra.status_code == 200:
                    data_tra = r_tra.json()
                    for t in data_tra:
                        icon = "🧪" if t['tipo_recurso'] == "Reactivo" else "🔌"
                        with st.expander(f"{icon} {t['nombre_recurso']}", expanded=True):
                            st.caption(f"Lote/Serie: {t['lote_o_serie']}")
                            # TODO: validar caducidad vs fecha de uso
                            st.markdown("✅ *Estado: Conforme*")
                else:
                    st.error("❌ Sin trazabilidad vinculada")

            st.markdown("---")
            pdf_resp = utils.api_request("GET", f"/reportes/coa/{oid}")
            cod_orden_safe = obj.get('cod_orden') or f"OT-{oid:05d}"
            if pdf_resp is not None and pdf_resp.status_code == 200:
                st.download_button(
                    label="📄 Descargar CoA provisional para revisión",
                    data=pdf_resp.content,
                    file_name=f"CoA_{cod_orden_safe}_REVISION.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.info("ℹ️ CoA no disponible todavía (sin resultados validados).")

            # --- ACCIONES DE CIERRE ---
            st.markdown("---")
            col_act1, col_act2 = st.columns([4, 1])
            with col_act1:
                st.text_area("📝 Comentarios de Revisión (Opcional)", placeholder="Todo conforme a PNT...")
            with col_act2:
                st.write("") # Espacio
                st.write("") 
                if st.button("✅ APROBAR Y EMITIR", type="primary", use_container_width=True):
                    res_upd = utils.api_request("PUT", f"/ejecucion/ordenes/{oid}/estado?nuevo_estado=Cerrada")
                    
                    if res_upd.status_code == 200:
                        st.balloons()
                        st.success(f"Orden {obj['cod_orden']} aprobada y cerrada.")
                        st.rerun()
                    else:
                        st.error(f"Error al cerrar: {res_upd.text}")

# ==============================================================================
# TAB 2: AUDITORÍA (GHOST FEATURE - PRÓXIMAMENTE)
# ==============================================================================
with tab_audit:
    st.info("🕵️‍♂️ **Buscador de Trazabilidad Inversa**")
    st.caption("Introduce un lote de reactivo o serie de equipo para ver a qué muestras ha afectado.")
    
    col_s1, col_s2 = st.columns([3, 1])
    query = col_s1.text_input("🔍 Buscar Lote / Serie / ID Recurso")
    if col_s2.button("Rastrear"):
        st.warning("🚧 Funcionalidad en construcción (Requiere Vista SQL 'Reverse Traceability')")