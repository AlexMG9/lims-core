import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.title("📦 Recepción de Muestras")
t_rec, t_mues = st.tabs(["1. Nueva Recepción", "2. Registrar Muestras"])

with t_rec:
    st.subheader("Entrada de Material")
    cli = utils.api_request("GET", "/recepcion/clientes").json()
    if cli:
        mc = {c['nombre_fiscal']:c['id_cliente'] for c in cli}
        with st.form("new_rec"):
            s = st.selectbox("Cliente", list(mc.keys()))
            comm = st.text_area("Comentarios")
            if st.form_submit_button("Generar Albarán"):
                r = utils.api_request("POST", "/recepcion/", {"id_cliente":mc[s], "comentarios_envio":comm})
                if r.status_code == 200: st.success(f"Recepción #{r.json()['id_recepcion']} creada"); st.rerun()
    
    st.divider()
    recs = utils.api_request("GET", "/recepcion/").json()
    if recs: st.dataframe(pd.DataFrame(recs), use_container_width=True)

with t_mues:
    st.subheader("Etiquetado")
    rec = utils.api_request("GET", "/recepcion/").json()
    pnt = utils.api_request("GET", "/metodos/pnts").json()
    
    if rec and pnt:
        mr = {f"Rec #{r['id_recepcion']}":r['id_recepcion'] for r in rec}
        mp = {p['codigo_pnt']:p['id_pnt'] for p in pnt}
        
        with st.form("new_sample"):
            c1, c2 = st.columns(2)
            s_r = c1.selectbox("Recepción", list(mr.keys()))
            ref = c2.text_input("Ref. Cliente")
            tip = c1.text_input("Tipo")
            ana = c2.multiselect("Análisis", list(mp.keys()))
            
            if st.form_submit_button("Registrar"):
                if ref and ana:
                    ids = [mp[x] for x in ana]
                    r = utils.api_request("POST", "/recepcion/muestras", {"id_recepcion":mr[s_r], "referencia_cliente_externa":ref, "pnts_ids":ids})
                    if r.status_code==200: st.success(f"Código: {r.json()['cod_lims']}"); st.rerun()
        
        st.divider()
        ms = utils.api_request("GET", "/recepcion/muestras").json()
        if ms: st.dataframe(pd.DataFrame(ms)[["cod_lims", "referencia_cliente_externa", "tipo_muestra"]], use_container_width=True)
    else: st.warning("Faltan Recepciones o PNTs.")
