import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Histórico", layout="wide", page_icon="🗂️")
utils.check_login()

st.title("🗂️ Histórico y Archivo")
st.caption("Búsqueda retrospectiva de muestras y órdenes de trabajo.")

# Filtros comunes: rango de fechas (últimos 90 días por defecto)
hoy = datetime.now().date()
default_desde = hoy - timedelta(days=90)

tab_muestras, tab_ordenes = st.tabs(["🧪 Muestras", "📋 Órdenes de Trabajo"])

# ==============================================================================
# TAB 1: MUESTRAS
# ==============================================================================
with tab_muestras:
    st.subheader("Histórico de Muestras")

    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        f_desde_m = st.date_input("Desde", value=default_desde, key="m_desde")
    with c2:
        f_hasta_m = st.date_input("Hasta", value=hoy, key="m_hasta")
    with c3:
        q_m = st.text_input("🔍 Buscar (código, referencia, cliente)", key="m_q")

    resp_m = utils.api_request("GET", "/recepcion/muestras")
    if resp_m is None or resp_m.status_code != 200:
        st.error("No se pudieron cargar las muestras.")
    else:
        data = resp_m.json()
        if not data:
            st.info("No hay muestras registradas.")
        else:
            df = pd.DataFrame(data)

            # Normalizar fecha
            if "fecha_recepcion" in df.columns:
                df["fecha_recepcion"] = pd.to_datetime(df["fecha_recepcion"], errors="coerce")
                mask = (df["fecha_recepcion"].dt.date >= f_desde_m) & (df["fecha_recepcion"].dt.date <= f_hasta_m)
                df = df.loc[mask]

            # Filtro por texto libre
            if q_m:
                ql = q_m.lower()
                def match_row(r):
                    campos = [str(r.get(c, "")) for c in ("cod_lims", "codigo_laboratorio", "referencia_cliente_externa", "tipo_muestra")]
                    return any(ql in c.lower() for c in campos)
                df = df[df.apply(match_row, axis=1)]

            cols_mostrar = [c for c in ["cod_lims", "referencia_cliente_externa", "tipo_muestra", "fecha_recepcion"] if c in df.columns]
            st.caption(f"**{len(df)}** muestras encontradas")
            st.dataframe(df[cols_mostrar], use_container_width=True, hide_index=True)

# ==============================================================================
# TAB 2: ÓRDENES DE TRABAJO
# ==============================================================================
with tab_ordenes:
    st.subheader("Histórico de Órdenes de Trabajo")

    resp_o = utils.api_request("GET", "/ejecucion/ordenes")
    if resp_o is None or resp_o.status_code != 200:
        st.error("No se pudieron cargar las órdenes.")
    else:
        ordenes = resp_o.json()
        if not ordenes:
            st.info("No hay órdenes registradas.")
        else:
            df_o = pd.DataFrame(ordenes)

            estados_disponibles = sorted(df_o["estado"].dropna().unique().tolist()) if "estado" in df_o.columns else []

            c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
            with c1:
                f_desde_o = st.date_input("Desde", value=default_desde, key="o_desde")
            with c2:
                f_hasta_o = st.date_input("Hasta", value=hoy, key="o_hasta")
            with c3:
                estados_sel = st.multiselect("Estado", estados_disponibles, default=estados_disponibles, key="o_estados")
            with c4:
                q_o = st.text_input("🔍 Buscar (código orden)", key="o_q")

            # Filtro de fecha
            if "fecha_inicio" in df_o.columns:
                df_o["fecha_inicio"] = pd.to_datetime(df_o["fecha_inicio"], errors="coerce")
                mask = (df_o["fecha_inicio"].dt.date >= f_desde_o) & (df_o["fecha_inicio"].dt.date <= f_hasta_o)
                df_o = df_o.loc[mask]

            # Filtro de estado
            if estados_sel and "estado" in df_o.columns:
                df_o = df_o[df_o["estado"].isin(estados_sel)]

            # Filtro texto
            if q_o and "cod_orden" in df_o.columns:
                df_o = df_o[df_o["cod_orden"].astype(str).str.contains(q_o, case=False, na=False)]

            cols_o = [c for c in ["cod_orden", "estado", "fecha_inicio", "id_pnt"] if c in df_o.columns]
            st.caption(f"**{len(df_o)}** órdenes encontradas")
            st.dataframe(df_o[cols_o], use_container_width=True, hide_index=True)

            # --- Descarga CoA por orden (Finalizada / Cerrada) ---
            st.markdown("### 📄 Descargar Certificado de Análisis")
            descargables = df_o[df_o["estado"].isin(["Finalizada", "Cerrada"])] if "estado" in df_o.columns else df_o.iloc[0:0]
            if descargables.empty:
                st.caption("No hay órdenes descargables en el filtro actual.")
            else:
                for _, row in descargables.iterrows():
                    cod = row.get("cod_orden") or f"OT-{row['id_orden']:05d}"
                    with st.expander(f"📄 {cod} — {row.get('estado', '')}"):
                        if st.button(f"Generar CoA {cod}", key=f"coa_btn_{row['id_orden']}"):
                            pdf_resp = utils.api_request("GET", f"/reportes/coa/{row['id_orden']}")
                            if pdf_resp is not None and pdf_resp.status_code == 200:
                                st.download_button(
                                    label=f"⬇️ Descargar {cod}.pdf",
                                    data=pdf_resp.content,
                                    file_name=f"CoA_{cod}.pdf",
                                    mime="application/pdf",
                                    key=f"coa_dl_{row['id_orden']}",
                                )
                            else:
                                st.error("No se pudo generar el CoA.")
