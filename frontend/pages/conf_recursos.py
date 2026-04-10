import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Tipos de Recursos", layout="wide", page_icon="🏷️")
utils.check_login()

st.title("🏷️ Configuración de Familias de Recursos")
st.info("Define aquí los tipos de equipos y reactivos para usarlos en las recetas de los PNTs.")

t1, t2 = st.tabs(["🧪 Tipos de Reactivos", "📟 Tipos de Equipos"])

with t1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("##### Nuevo Tipo Reactivo")
        nr = st.text_input("Nombre (ej: Metanol)", key="ntr")
        if st.button("Crear Tipo Reactivo"):
            utils.api_request("POST", "/reactivos/tipos?nombre="+nr)
            st.rerun()
    with c2:
        res = utils.api_request("GET", "/reactivos/tipos")
        if res and res.status_code==200: st.dataframe(pd.DataFrame(res.json()), use_container_width=True)

with t2:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("##### Nuevo Tipo Equipo")
        ne = st.text_input("Nombre (ej: HPLC)", key="nte")
        if st.button("Crear Tipo Equipo"):
            utils.api_request("POST", "/equipos/tipos?nombre="+ne)
            st.rerun()
    with c2:
        res = utils.api_request("GET", "/equipos/tipos")
        if res and res.status_code==200: st.dataframe(pd.DataFrame(res.json()), use_container_width=True)
