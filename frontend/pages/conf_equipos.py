import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Equipos", layout="wide", page_icon="📟")
utils.check_login()

st.title("📟 Gestión de Equipos e Instrumentos")

# --- FORMULARIO ALTA ---
with st.expander("➕ Alta de Nuevo Equipo"):
    with st.form("new_eq"):
        tipos_bd = utils.api_request("GET", "/equipos/tipos")
        map_tipos = {}
        if tipos_bd.status_code == 200:
            map_tipos = {t['nombre_tipo']: t['id_tipo_equipo'] for t in tipos_bd.json()}

        c1, c2 = st.columns(2)
        nom = c1.text_input("Nombre Equipo *", placeholder="Ej: HPLC Agilent 1200")
        ser = c2.text_input("Nº Serie *", placeholder="SN-123456")
        
        c3, c4, c5, c6 = st.columns(4)
        sel_tipo = c3.selectbox("Tipo *", list(map_tipos.keys()) if map_tipos else [])
        ubi = c3.text_input("Ubicación", placeholder="Lab Fisicoquímica")
        calib = c4.date_input("Próxima Calibración", value=None)
        estado = c5.selectbox("Estado", ["Operativo", "Mantenimiento", "Fuera de Servicio"])
        
        if st.form_submit_button("Registrar Equipo"):
            if nom and ser and sel_tipo:
                p = {
                    "nombre_equipo": nom, "numero_serie": ser, "ubicacion": ubi,
                    "fecha_prox_calib": str(calib) if calib else None,
                    "estado_operativo": estado,
                    "id_tipo_equipo": map_tipos[sel_tipo]
                }
                res = utils.api_request("POST", "/equipos/", p)
                if res.status_code == 200: st.success("Equipo Creado"); st.rerun()
                else: st.error(res.text)
            else:
                st.warning("Nombre y Serie obligatorios")

st.divider()

# --- LISTADO Y GESTIÓN ---
st.subheader("Inventario de Activos")
res = utils.api_request("GET", "/equipos/")

def highlight_calib(row):
    try:
        if row['estado_operativo'] != 'Operativo':
            return ['background-color: #ffcccb'] * len(row) # Rojo
        if row['fecha_prox_calib']:
            dt = pd.to_datetime(row['fecha_prox_calib']).date()
            if dt < date.today():
                return ['background-color: #ffe68c'] * len(row) # Amarillo
    except: pass
    return [''] * len(row)

if res and res.status_code == 200:
    data = res.json()
    if data:
        df = pd.DataFrame(data)
        cols = ["cod_interno", "nombre_equipo", "numero_serie", "ubicacion", "fecha_prox_calib", "estado_operativo"]
        st.dataframe(
            df[cols].style.apply(highlight_calib, axis=1), 
            use_container_width=True, 
            hide_index=True,
            column_config={"fecha_prox_calib": st.column_config.DateColumn("Vencimiento Calib.", format="DD/MM/YYYY")}
        )
    else:
        st.info("No hay equipos registrados.")
