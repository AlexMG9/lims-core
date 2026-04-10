from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List

# --- AUTH ---
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username: Optional[str] = None

# --- TIPOS ---
class TipoCreate(BaseModel):
    nombre_tipo: str
    descripcion: Optional[str] = None

class TipoResponse(TipoCreate):
    # IDs opcionales: sirve tanto para TipoEquipo como TipoReactivo
    id_tipo_reactivo: Optional[int] = None
    id_tipo_equipo: Optional[int] = None
    class Config: from_attributes = True

# --- INVENTARIO ---
class ReactivoBase(BaseModel):
    nombre: str
    id_tipo_reactivo: Optional[int] = None
    clasificacion: Optional[str] = "Reactivo" 
    calidad: Optional[str] = None
    proveedor: Optional[str] = None
    numero_lote: str
    cantidad_inicial: Optional[float] = None
    unidad: Optional[str] = None
    fecha_caducidad: date
    fecha_apertura: Optional[date] = None
    estado_calidad: Optional[str] = "En Stock"
    ruta_certificado: Optional[str] = None 
    cod_interno: Optional[str] = None 

class ReactivoCreate(ReactivoBase):
    pass

class ReactivoResponse(ReactivoBase):
    id_reactivo: int
    is_deleted: bool
    class Config: from_attributes = True

class EquipoCreate(BaseModel):
    nombre_equipo: str
    numero_serie: str
    id_tipo_equipo: Optional[int] = None
    fecha_prox_calib: Optional[date] = None
    estado_operativo: str = "Operativo"
    ubicacion: Optional[str] = None

class EquipoResponse(EquipoCreate):
    id_equipo: int
    cod_interno: Optional[str] = None
    class Config: from_attributes = True

# --- CLIENTES Y MUESTRAS ---
class ClienteCreate(BaseModel):
    nombre_fiscal: str
    email_contacto: Optional[str] = None
class ClienteResponse(ClienteCreate):
    id_cliente: int
    class Config: from_attributes = True

class RecepcionCreate(BaseModel):
    id_cliente: int
    comentarios_envio: Optional[str] = None
class RecepcionResponse(RecepcionCreate):
    id_recepcion: int
    fecha_entrada: datetime
    recibido_por: int
    class Config: from_attributes = True

class MuestraCreate(BaseModel):
    id_recepcion: int
    referencia_cliente_externa: str
    tipo_muestra: Optional[str] = "Generica"
    pnts_ids: List[int] = []
class MuestraResponse(BaseModel):
    id_muestra: int
    cod_lims: Optional[str] = None
    referencia_cliente_externa: str
    tipo_muestra: Optional[str]
    fecha_recepcion: datetime
    class Config: from_attributes = True

# --- METODOS ---
class ParametroResponse(BaseModel):
    id_parametro: int
    nombre_parametro: str
    unidad_por_defecto: Optional[str]
    class Config: from_attributes = True
class ParametroCreate(BaseModel):
    nombre_parametro: str
    unidad_por_defecto: Optional[str] = "mg/kg"

class PNTCreate(BaseModel):
    codigo_pnt: str
    nombre_ensayo: str
class PNTResponse(PNTCreate):
    id_pnt: int
    class Config: from_attributes = True

class PNTConfigCreate(BaseModel):
    id_pnt: int
    id_parametro: int
    limite_deteccion_LOD: Optional[float]
    limite_min: Optional[float]
    limite_max: Optional[float]
class PNTConfigResponse(PNTConfigCreate):
    id_config: int
    class Config: from_attributes = True

# --- RECETAS ---
class RecetaCreate(BaseModel):
    id_pnt: int
    nombre_receta: str
    cantidad_referencia: float
    unidad_referencia: str
    caducidad_horas: int

class RecetaResponse(RecetaCreate):
    id_receta: int
    class Config: from_attributes = True

class IngredienteCreate(BaseModel):
    id_receta: int
    id_tipo_reactivo: int
    cantidad_necesaria: float

class IngredienteResponse(IngredienteCreate):
    id_ingrediente_receta: int
    tipo: Optional[str] = None
    class Config: from_attributes = True

class PreparacionCreate(BaseModel):
    id_receta: int
    cantidad_preparada: float
    ids_padres: List[List[float]]

# --- EJECUCIÓN Y REPORTING ---
class OrdenTrabajoCreate(BaseModel):
    id_pnt: int
class OrdenTrabajoResponse(OrdenTrabajoCreate):
    id_orden: int
    cod_orden: Optional[str] = None
    fecha_inicio: datetime
    estado: str
    fecha_cierre: Optional[datetime] = None
    class Config: from_attributes = True

class ResultadoCreate(BaseModel):
    id_item_orden: int
    id_parametro: int
    valor_resultado: str
class ReabrirMuestraRequest(BaseModel):
    cod_lims: str
    motivo: str

class PNTRecursoCreate(BaseModel):
    id_pnt: int
    tipo_recurso: str 
    id_tipo_necesario: int 
    cantidad_necesaria: float = 1.0

class PNTRecursoResponse(PNTRecursoCreate):
    id_pnt_recurso: int
    nombre_tipo_necesario: Optional[str] = None
    class Config: from_attributes = True

# --- TRAZABILIDAD ---
class TrazaCreate(BaseModel):
    id_orden: int
    tipo_recurso: str
    id_recurso: int

class TrazaResponse(BaseModel):
    id_traza: int
    tipo_recurso: str
    nombre_recurso: Optional[str] = "Desconocido"
    cod_recurso: Optional[str] = "???"
    fecha_uso: datetime
    lote_o_serie: Optional[str] = None
    class Config: from_attributes = True

class CalidadOrdenView(BaseModel):
    id_orden: int
    cod_orden: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_finalizacion_tecnica: Optional[datetime] = None
    codigo_pnt: str
    nombre_ensayo: str
    cod_lims: Optional[str] = None
    referencia_cliente_externa: Optional[str] = None
    analista: Optional[str] = None
    total_resultados: int
    recursos_usados: int

    model_config = ConfigDict(from_attributes=True)