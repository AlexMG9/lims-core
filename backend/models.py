from sqlalchemy import Column, Integer, String, Date, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# --- AUDITORÍA ---
class AuditLog(Base):
    __tablename__ = "sys_audit_log"
    evento_id = Column(Integer, primary_key=True)
    fecha_hora_utc = Column(DateTime, nullable=True, server_default=func.now())
    usuario = Column(String(100))
    tabla_afectada = Column(String(50))
    id_registro = Column(String(100))
    tipo_accion = Column(String(20))
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)
    motivo_cambio = Column(Text)

# --- ROLES ---
class Role(Base):
    __tablename__ = "tb_roles"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255))

# --- USUARIOS ---
class Usuario(Base):
    __tablename__ = "tb_usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    nombre_completo = Column(String(100))
    id_rol = Column(
        Integer,
        ForeignKey("tb_roles.id_rol", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    estado = Column(Boolean, default=True)

# --- TIPOS ---
class TipoEquipo(Base):
    __tablename__ = "tb_tipos_equipo"
    id_tipo_equipo = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(100), unique=True)  # Ej: "HPLC"
    descripcion = Column(String(255))

class TipoReactivo(Base):
    __tablename__ = "tb_tipos_reactivo"
    id_tipo_reactivo = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(100), unique=True)  # Ej: "Metanol"
    descripcion = Column(String(255))

# --- INVENTARIO ---
class Equipo(Base):
    __tablename__ = "tb_equipos"
    id_equipo = Column(Integer, primary_key=True, index=True)
    nombre_equipo = Column(String(100))
    numero_serie = Column(String(100))
    id_tipo_equipo = Column(
        Integer,
        ForeignKey("tb_tipos_equipo.id_tipo_equipo", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True
    )
    fecha_prox_calib = Column(Date)
    estado_operativo = Column(String(50))
    ubicacion = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    cod_interno = Column(String(20))

class Reactivo(Base):
    __tablename__ = "tb_reactivos"
    id_reactivo = Column(Integer, primary_key=True, index=True)
    id_tipo_reactivo = Column(
        Integer,
        ForeignKey("tb_tipos_reactivo.id_tipo_reactivo", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True
    )
    nombre = Column(String(255), nullable=False)
    # CLASIFICACIÓN Y PDF
    clasificacion = Column(String(50), default="Reactivo")  # Reactivo, MR, MRC, Patron
    ruta_certificado = Column(String(255), nullable=True)   # Ruta al PDF

    calidad = Column(String(100))
    proveedor = Column(String(150))
    referencia_proveedor = Column(String(100), nullable=True)
    numero_lote = Column(String(100), nullable=False)
    cantidad_inicial = Column(Float)
    unidad = Column(String(20))
    condiciones_conservacion = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)
    fecha_caducidad = Column(Date, nullable=False)
    fecha_apertura = Column(Date)
    estado_calidad = Column(String(20), default="En Stock")
    ubicacion_fisica = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False)
    cod_interno = Column(String(20))

# --- CLIENTES Y RECEPCIÓN ---
class Cliente(Base):
    __tablename__ = "tb_clientes"
    id_cliente = Column(Integer, primary_key=True, index=True)
    nombre_fiscal = Column(String(255))
    email_contacto = Column(String(150))

class Recepcion(Base):
    __tablename__ = "tb_recepcion"
    id_recepcion = Column(Integer, primary_key=True)
    id_cliente = Column(
        Integer,
        ForeignKey("tb_clientes.id_cliente", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    fecha_entrada = Column(DateTime(timezone=True), server_default=func.now())
    recibido_por = Column(
        Integer,
        ForeignKey("tb_usuarios.id_usuario", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    comentarios_envio = Column(Text)

class Muestra(Base):
    __tablename__ = "tb_muestras"
    id_muestra = Column(Integer, primary_key=True)
    id_recepcion = Column(
        Integer,
        ForeignKey("tb_recepcion.id_recepcion", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    referencia_cliente_externa = Column(String(255))
    tipo_muestra = Column(String(100))
    fecha_recepcion = Column(DateTime(timezone=True), server_default=func.now())
    codigo_laboratorio = Column(String(20))
    correlativo_anual = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    condicion_llegada = Column(String(50))

# --- MÉTODOS Y PNTs ---
class PNT(Base):
    __tablename__ = "tb_pnt"
    id_pnt = Column(Integer, primary_key=True)
    codigo_pnt = Column(String(50), unique=True)
    nombre_ensayo = Column(String(255))
    version_vigente = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

class Parametro(Base):
    __tablename__ = "tb_parametros"
    id_parametro = Column(Integer, primary_key=True)
    nombre_parametro = Column(String(100))
    unidad_por_defecto = Column(String(50))

class PNTParametroConfig(Base):
    __tablename__ = "tb_pnt_parametros_config"
    id_config = Column(Integer, primary_key=True)
    id_pnt = Column(
        Integer,
        ForeignKey("tb_pnt.id_pnt", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    id_parametro = Column(
        Integer,
        ForeignKey("tb_parametros.id_parametro", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    limite_deteccion_LOD = Column(Float)
    limite_min = Column(Float)
    limite_max = Column(Float)

# --- EJECUCIÓN ---
class OrdenTrabajo(Base):
    __tablename__ = "tb_orden_trabajo"
    id_orden = Column(Integer, primary_key=True)
    id_pnt = Column(
        Integer,
        ForeignKey("tb_pnt.id_pnt", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_cierre = Column(DateTime(timezone=True))
    id_analista_responsable = Column(
        Integer,
        ForeignKey("tb_usuarios.id_usuario", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    estado = Column(String(50), default='Abierta')
    cod_orden = Column(String(20))

class SubmuestraAnalisis(Base):
    __tablename__ = "tb_submuestras_analisis"
    id_submuestra = Column(Integer, primary_key=True)
    id_muestra_padre = Column(
        Integer,
        ForeignKey("tb_muestras.id_muestra", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    id_pnt_destino = Column(
        Integer,
        ForeignKey("tb_pnt.id_pnt", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    estado_individual = Column(String(50))

class OrdenItem(Base):
    __tablename__ = "tb_orden_items"
    id_item_orden = Column(Integer, primary_key=True)
    id_orden = Column(
        Integer,
        ForeignKey("tb_orden_trabajo.id_orden", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    id_submuestra = Column(
        Integer,
        ForeignKey("tb_submuestras_analisis.id_submuestra", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )

class Resultado(Base):
    __tablename__ = "tb_resultados"
    id_resultado = Column(Integer, primary_key=True)
    id_item_orden = Column(
        Integer,
        ForeignKey("tb_orden_items.id_item_orden", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    id_parametro = Column(
        Integer,
        ForeignKey("tb_parametros.id_parametro", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    valor_resultado = Column(String(255))
    unidad = Column(String(50))
    estado_validacion = Column(String(50))
    fecha_hora_resultado = Column(DateTime(timezone=True))
    id_revisor = Column(
        Integer,
        ForeignKey("tb_usuarios.id_usuario", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True
    )
    observaciones = Column(Text)

class TrazabilidadUso(Base):
    __tablename__ = "tb_trazabilidad_uso"
    id_uso = Column(Integer, primary_key=True)
    id_orden = Column(
        Integer,
        ForeignKey("tb_orden_trabajo.id_orden", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    tipo_recurso = Column(String(20))
    id_recurso_especifico = Column(Integer)  # TODO: refactorizar polimorfismo con exclusive arc (antipatrón conocido)
    cantidad_usada = Column(Float, nullable=True)

# --- GESTIÓN DE RECETAS ---
class PNTReceta(Base):
    __tablename__ = "tb_pnt_recetas"
    id_receta = Column(Integer, primary_key=True)
    id_pnt = Column(
        Integer,
        ForeignKey("tb_pnt.id_pnt", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    nombre_receta = Column(String(100))
    cantidad_referencia = Column(Float)
    unidad_referencia = Column(String(20))
    caducidad_horas = Column(Integer)

class PNTRecetaIngrediente(Base):
    __tablename__ = "tb_pnt_receta_ingredientes"
    id_ingrediente_receta = Column(Integer, primary_key=True)
    id_receta = Column(
        Integer,
        ForeignKey("tb_pnt_recetas.id_receta", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    id_tipo_reactivo = Column(
        Integer,
        ForeignKey("tb_tipos_reactivo.id_tipo_reactivo", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    cantidad_necesaria = Column(Float)

class ComposicionReactivo(Base):
    __tablename__ = "tb_composicion_reactivo"
    id_composicion = Column(Integer, primary_key=True)
    id_reactivo_hijo = Column(
        Integer,
        ForeignKey("tb_reactivos.id_reactivo", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    id_reactivo_padre = Column(
        Integer,
        ForeignKey("tb_reactivos.id_reactivo", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    cantidad_gastada = Column(Float)

class PNTRecurso(Base):
    __tablename__ = "tb_pnt_recursos"
    id_pnt_recurso = Column(Integer, primary_key=True)
    id_pnt = Column(
        Integer,
        ForeignKey("tb_pnt.id_pnt", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    tipo_recurso = Column(String(20))  # 'Equipo' o 'Reactivo'
    id_tipo_necesario = Column(Integer)  # TODO: refactorizar polimorfismo con exclusive arc (antipatrón conocido)
    cantidad_necesaria = Column(Float, default=1.0)

# --- TRAZABILIDAD ---
class TrazabilidadOrden(Base):
    __tablename__ = "tb_trazabilidad_orden"
    id_traza = Column(Integer, primary_key=True)
    id_orden = Column(
        Integer,
        ForeignKey("tb_orden_trabajo.id_orden", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    tipo_recurso = Column(String(20))
    id_reactivo = Column(
        Integer,
        ForeignKey("tb_reactivos.id_reactivo", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True
    )
    id_equipo = Column(
        Integer,
        ForeignKey("tb_equipos.id_equipo", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True
    )
    fecha_uso = Column(DateTime, default=datetime.utcnow)
