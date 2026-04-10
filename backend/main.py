from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import auth, reactivos, recepcion, metodos, ejecucion, equipos, reportes, calidad
import os

app = FastAPI(title="LIMS ISO 17025 API", version="2.4.0")

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(reactivos.router)
app.include_router(recepcion.router)
app.include_router(metodos.router)
app.include_router(ejecucion.router)
app.include_router(equipos.router)
app.include_router(reportes.router)
app.include_router(calidad.router)

@app.get("/")
def root():
    return {"Sistema": "LIMS Core v2.4", "Status": "Ready"}
