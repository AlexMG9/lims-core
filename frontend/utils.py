import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Detectar URL del backend (Docker o Local)
API_URL = os.getenv("API_URL", "http://lims_api:8000")

def check_login():
    """Verifica si existe token en sesión. Si no, detiene la ejecución."""
    if "token" not in st.session_state or st.session_state.token is None:
        st.warning("⚠️ Sesión no iniciada o expirada.")
        st.stop()

def api_request(method, endpoint, data=None):
    """
    Wrapper para hacer peticiones al backend inyectando el token.
    """
    if "token" not in st.session_state:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers)
            
        if response.status_code == 401:
            st.error("Sesión caducada. Recarga la página.")
            st.session_state.token = None
            st.stop()
            
        return response
    except Exception as e:
        st.error(f"Error de conexión con API: {e}")
        return None

def resaltar_caducados(row):
    """Ayuda visual para Dataframes"""
    try:
        # Si tiene fecha de caducidad
        if 'fecha_caducidad' in row and row['fecha_caducidad']:
            hoy = pd.Timestamp.now().date()
            cad = pd.to_datetime(row['fecha_caducidad']).date()
            if cad < hoy:
                return ['background-color: #ffcccb; color: black'] * len(row) # Rojo claro
            elif (cad - hoy).days < 30:
                return ['background-color: #ffe68c; color: black'] * len(row) # Amarillo
    except:
        pass
    return [''] * len(row)