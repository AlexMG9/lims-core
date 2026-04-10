import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.title("Gestión de Clientes")

c1, c2 = st.columns([1, 2])
with c1:
    with st.form("new"):
        n = st.text_input("Nombre"); e = st.text_input("Email")
        if st.form_submit_button("Crear"):
            utils.api_request("POST", "/recepcion/clientes", {"nombre_fiscal":n, "email_contacto":e})
            st.rerun()

with c2:
    res = utils.api_request("GET", "/recepcion/clientes")
    if res:
        df = pd.DataFrame(res.json())
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        if not df.empty:
            ops = {c['nombre_fiscal']:c['id_cliente'] for c in res.json()}
            s = st.selectbox("Gestionar:", list(ops.keys()))
            if st.button("Borrar"):
                utils.api_request("DELETE", f"/recepcion/clientes/{ops[s]}")
                st.rerun()
