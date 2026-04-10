import streamlit as st
import utils
import os
import requests

st.set_page_config(page_title="LIMS Core", layout="wide", page_icon="🧪")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.token:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🧪 Acceso LIMS")
        st.markdown("Sistema de Gestión de Laboratorio ISO 17025")
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submitted:
                try:
                    API_URL = os.getenv("API_URL", "http://lims_api:8000")
                    res = requests.post(f"{API_URL}/token", data={"username": u, "password": p})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user = u
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                except Exception as e:
                    st.error(f"No se puede conectar con el servidor: {e}")

else:
    # --- MENÚ DE NAVEGACIÓN ---
    pg = st.navigation({
        "🧬 Laboratorio (Operaciones)": [
            st.Page("pages/lab_inventario.py", title="Inventario", icon="🧪"),
            st.Page("pages/lab_recepcion.py", title="Recepción y Muestras", icon="📦"),
            st.Page("pages/lab_ejecucion.py", title="Ejecución Analítica", icon="🔬"),
        ],
        "✅ Calidad y Emisión": [
            st.Page("pages/lab_calidad.py", title="Revisión de Informes", icon="🖨️"),
            st.Page("pages/lab_historico.py", title="Histórico y Archivo", icon="🗂️"),
        ],
        "🛠️ Configuración (Admin)": [
            st.Page("pages/conf_clientes.py", title="Gestión de Clientes", icon="👥"),
            st.Page("pages/conf_metodos.py", title="Métodos y PNTs", icon="⚙️"),
            st.Page("pages/conf_equipos.py", title="Equipos (Activos)", icon="📟"),
            st.Page("pages/conf_recursos.py", title="Tipos y Familias", icon="🏷️"),
        ]
    })
    
    with st.sidebar:
        st.divider()
        col_avatar, col_info = st.columns([1, 3])
        with col_avatar: st.write("👤")
        with col_info:
            st.write(f"**{st.session_state.user}**")
            st.caption("Analista / Admin")
            
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    pg.run()
