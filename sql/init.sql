-- ======================================================================================
-- SCRIPT MAESTRO LIMS — VERSIÓN 5.0 (GENERADO DESDE models.py Fase 1)
-- FECHA: 2026-04-09
-- Fuente DDL: backend/models.py (27 FKs, 23 modelos)
-- Vistas: /tmp/views.sql (6 vistas, 2 reescritas)
-- Triggers: /tmp/triggers.sql (1 trigger de auditoría)
-- Seeds: /tmp/seeds_roles.sql + /tmp/seeds_admin.sql (hash bcrypt fresco)
-- ======================================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------
-- 0. LIMPIEZA NUCLEAR (idempotente)
-- ---------------------------------------------------------
DROP VIEW IF EXISTS `view_disoluciones_list`;
DROP VIEW IF EXISTS `view_ordenes_trabajo_list`;
DROP VIEW IF EXISTS `view_muestras_list`;
DROP VIEW IF EXISTS `view_equipos_list`;
DROP VIEW IF EXISTS `view_patrones_list`;
DROP VIEW IF EXISTS `view_reactivos_list`;

DROP TRIGGER IF EXISTS `audit_reactivos_update`;

DROP TABLE IF EXISTS `tb_trazabilidad_orden`;
DROP TABLE IF EXISTS `tb_pnt_recursos`;
DROP TABLE IF EXISTS `tb_composicion_reactivo`;
DROP TABLE IF EXISTS `tb_pnt_receta_ingredientes`;
DROP TABLE IF EXISTS `tb_pnt_recetas`;
DROP TABLE IF EXISTS `tb_trazabilidad_uso`;
DROP TABLE IF EXISTS `tb_resultados`;
DROP TABLE IF EXISTS `tb_orden_items`;
DROP TABLE IF EXISTS `tb_orden_trabajo`;
DROP TABLE IF EXISTS `tb_submuestras_analisis`;
DROP TABLE IF EXISTS `tb_pnt_parametros_config`;
DROP TABLE IF EXISTS `tb_muestras`;
DROP TABLE IF EXISTS `tb_recepcion`;
DROP TABLE IF EXISTS `tb_clientes`;
DROP TABLE IF EXISTS `tb_reactivos`;
DROP TABLE IF EXISTS `tb_equipos`;
DROP TABLE IF EXISTS `tb_parametros`;
DROP TABLE IF EXISTS `tb_pnt`;
DROP TABLE IF EXISTS `tb_tipos_reactivo`;
DROP TABLE IF EXISTS `tb_tipos_equipo`;
DROP TABLE IF EXISTS `tb_usuarios`;
DROP TABLE IF EXISTS `tb_roles`;
DROP TABLE IF EXISTS `sys_audit_log`;

-- ---------------------------------------------------------
-- 1. AUDITORÍA
-- Modelo: AuditLog → sys_audit_log
-- ---------------------------------------------------------
CREATE TABLE `sys_audit_log` (
  `evento_id`       INT NOT NULL AUTO_INCREMENT,
  `fecha_hora_utc`  DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `usuario`         VARCHAR(100),
  `tabla_afectada`  VARCHAR(50),
  `id_registro`     VARCHAR(100),
  `tipo_accion`     VARCHAR(20),
  `valor_anterior`  TEXT,
  `valor_nuevo`     TEXT,
  `motivo_cambio`   TEXT,
  PRIMARY KEY (`evento_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 2. SEGURIDAD
-- Modelos: Role → tb_roles, Usuario → tb_usuarios
-- ---------------------------------------------------------
CREATE TABLE `tb_roles` (
  `id_rol`      INT NOT NULL AUTO_INCREMENT,
  `nombre_rol`  VARCHAR(50) NOT NULL UNIQUE,
  `descripcion` VARCHAR(255),
  PRIMARY KEY (`id_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_usuarios` (
  `id_usuario`      INT NOT NULL AUTO_INCREMENT,
  `username`        VARCHAR(50) UNIQUE,
  `password_hash`   VARCHAR(255),
  `nombre_completo` VARCHAR(100),
  `id_rol`          INT NOT NULL,
  `estado`          TINYINT(1) DEFAULT 1,
  PRIMARY KEY (`id_usuario`),
  FOREIGN KEY (`id_rol`)
    REFERENCES `tb_roles`(`id_rol`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 3. TIPOS (CATÁLOGOS)
-- Modelos: TipoEquipo → tb_tipos_equipo
--          TipoReactivo → tb_tipos_reactivo
-- ---------------------------------------------------------
CREATE TABLE `tb_tipos_equipo` (
  `id_tipo_equipo` INT NOT NULL AUTO_INCREMENT,
  `nombre_tipo`    VARCHAR(100) UNIQUE,
  `descripcion`    VARCHAR(255),
  PRIMARY KEY (`id_tipo_equipo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_tipos_reactivo` (
  `id_tipo_reactivo` INT NOT NULL AUTO_INCREMENT,
  `nombre_tipo`      VARCHAR(100) UNIQUE,
  `descripcion`      VARCHAR(255),
  PRIMARY KEY (`id_tipo_reactivo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 4. INVENTARIO
-- Modelos: Equipo → tb_equipos, Reactivo → tb_reactivos
-- ---------------------------------------------------------
CREATE TABLE `tb_equipos` (
  `id_equipo`        INT NOT NULL AUTO_INCREMENT,
  `nombre_equipo`    VARCHAR(100),
  `numero_serie`     VARCHAR(100),
  `id_tipo_equipo`   INT NULL,
  `fecha_prox_calib` DATE,
  `estado_operativo` VARCHAR(50),
  `ubicacion`        VARCHAR(100),
  `is_deleted`       TINYINT(1) DEFAULT 0,
  `cod_interno`      VARCHAR(20),
  PRIMARY KEY (`id_equipo`),
  FOREIGN KEY (`id_tipo_equipo`)
    REFERENCES `tb_tipos_equipo`(`id_tipo_equipo`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_reactivos` (
  `id_reactivo`           INT NOT NULL AUTO_INCREMENT,
  `id_tipo_reactivo`      INT NULL,
  `nombre`                VARCHAR(255) NOT NULL,
  `clasificacion`         VARCHAR(50) DEFAULT 'Reactivo',
  `ruta_certificado`      VARCHAR(255),
  `calidad`               VARCHAR(100),
  `proveedor`             VARCHAR(150),
  `referencia_proveedor`  VARCHAR(100),
  `numero_lote`           VARCHAR(100) NOT NULL,
  `cantidad_inicial`      FLOAT,
  `unidad`                VARCHAR(20),
  `condiciones_conservacion` VARCHAR(100),
  `observaciones`         TEXT,
  `fecha_caducidad`       DATE NOT NULL,
  `fecha_apertura`        DATE,
  `estado_calidad`        VARCHAR(20) DEFAULT 'En Stock',
  `ubicacion_fisica`      VARCHAR(100),
  `is_deleted`            TINYINT(1) DEFAULT 0,
  `cod_interno`           VARCHAR(20),
  PRIMARY KEY (`id_reactivo`),
  FOREIGN KEY (`id_tipo_reactivo`)
    REFERENCES `tb_tipos_reactivo`(`id_tipo_reactivo`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 5. CLIENTES Y RECEPCIÓN
-- Modelos: Cliente → tb_clientes
--          Recepcion → tb_recepcion
--          Muestra → tb_muestras
-- ---------------------------------------------------------
CREATE TABLE `tb_clientes` (
  `id_cliente`      INT NOT NULL AUTO_INCREMENT,
  `nombre_fiscal`   VARCHAR(255),
  `email_contacto`  VARCHAR(150),
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_recepcion` (
  `id_recepcion`      INT NOT NULL AUTO_INCREMENT,
  `id_cliente`        INT NOT NULL,
  `fecha_entrada`     DATETIME DEFAULT CURRENT_TIMESTAMP,
  `recibido_por`      INT NOT NULL,
  `comentarios_envio` TEXT,
  PRIMARY KEY (`id_recepcion`),
  FOREIGN KEY (`id_cliente`)
    REFERENCES `tb_clientes`(`id_cliente`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  FOREIGN KEY (`recibido_por`)
    REFERENCES `tb_usuarios`(`id_usuario`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_muestras` (
  `id_muestra`                  INT NOT NULL AUTO_INCREMENT,
  `id_recepcion`                INT NOT NULL,
  `referencia_cliente_externa`  VARCHAR(255),
  `tipo_muestra`                VARCHAR(100),
  `fecha_recepcion`             DATETIME DEFAULT CURRENT_TIMESTAMP,
  `codigo_laboratorio`          VARCHAR(20),
  `correlativo_anual`           INT,
  `is_deleted`                  TINYINT(1) DEFAULT 0,
  `condicion_llegada`           VARCHAR(50),
  PRIMARY KEY (`id_muestra`),
  FOREIGN KEY (`id_recepcion`)
    REFERENCES `tb_recepcion`(`id_recepcion`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 6. MÉTODOS Y PNTs
-- Modelos: PNT → tb_pnt
--          Parametro → tb_parametros
--          PNTParametroConfig → tb_pnt_parametros_config
-- ---------------------------------------------------------
CREATE TABLE `tb_pnt` (
  `id_pnt`          INT NOT NULL AUTO_INCREMENT,
  `codigo_pnt`      VARCHAR(50) UNIQUE,
  `nombre_ensayo`   VARCHAR(255),
  `version_vigente` INT DEFAULT 1,
  `is_active`       TINYINT(1) DEFAULT 1,
  PRIMARY KEY (`id_pnt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_parametros` (
  `id_parametro`       INT NOT NULL AUTO_INCREMENT,
  `nombre_parametro`   VARCHAR(100),
  `unidad_por_defecto` VARCHAR(50),
  PRIMARY KEY (`id_parametro`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_pnt_parametros_config` (
  `id_config`             INT NOT NULL AUTO_INCREMENT,
  `id_pnt`                INT NOT NULL,
  `id_parametro`          INT NOT NULL,
  `limite_deteccion_LOD`  FLOAT,
  `limite_min`            FLOAT,
  `limite_max`            FLOAT,
  PRIMARY KEY (`id_config`),
  FOREIGN KEY (`id_pnt`)
    REFERENCES `tb_pnt`(`id_pnt`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_parametro`)
    REFERENCES `tb_parametros`(`id_parametro`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 7. EJECUCIÓN (ÓRDENES DE TRABAJO)
-- Modelos: OrdenTrabajo → tb_orden_trabajo
--          SubmuestraAnalisis → tb_submuestras_analisis
--          OrdenItem → tb_orden_items
--          Resultado → tb_resultados
--          TrazabilidadUso → tb_trazabilidad_uso
-- ---------------------------------------------------------
CREATE TABLE `tb_orden_trabajo` (
  `id_orden`                 INT NOT NULL AUTO_INCREMENT,
  `id_pnt`                   INT NOT NULL,
  `fecha_inicio`             DATETIME DEFAULT CURRENT_TIMESTAMP,
  `fecha_cierre`             DATETIME,
  `id_analista_responsable`  INT NOT NULL,
  `estado`                   VARCHAR(50) DEFAULT 'Abierta',
  `cod_orden`                VARCHAR(20),
  PRIMARY KEY (`id_orden`),
  FOREIGN KEY (`id_pnt`)
    REFERENCES `tb_pnt`(`id_pnt`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  FOREIGN KEY (`id_analista_responsable`)
    REFERENCES `tb_usuarios`(`id_usuario`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_submuestras_analisis` (
  `id_submuestra`     INT NOT NULL AUTO_INCREMENT,
  `id_muestra_padre`  INT NOT NULL,
  `id_pnt_destino`    INT NOT NULL,
  `estado_individual` VARCHAR(50),
  PRIMARY KEY (`id_submuestra`),
  FOREIGN KEY (`id_muestra_padre`)
    REFERENCES `tb_muestras`(`id_muestra`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_pnt_destino`)
    REFERENCES `tb_pnt`(`id_pnt`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_orden_items` (
  `id_item_orden` INT NOT NULL AUTO_INCREMENT,
  `id_orden`      INT NOT NULL,
  `id_submuestra` INT NOT NULL,
  PRIMARY KEY (`id_item_orden`),
  FOREIGN KEY (`id_orden`)
    REFERENCES `tb_orden_trabajo`(`id_orden`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_submuestra`)
    REFERENCES `tb_submuestras_analisis`(`id_submuestra`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_resultados` (
  `id_resultado`        INT NOT NULL AUTO_INCREMENT,
  `id_item_orden`       INT NOT NULL,
  `id_parametro`        INT NOT NULL,
  `valor_resultado`     VARCHAR(255),
  `unidad`              VARCHAR(50),
  `estado_validacion`   VARCHAR(50),
  `fecha_hora_resultado` DATETIME,
  `id_revisor`          INT,
  `observaciones`       TEXT,
  PRIMARY KEY (`id_resultado`),
  FOREIGN KEY (`id_item_orden`)
    REFERENCES `tb_orden_items`(`id_item_orden`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_parametro`)
    REFERENCES `tb_parametros`(`id_parametro`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  FOREIGN KEY (`id_revisor`)
    REFERENCES `tb_usuarios`(`id_usuario`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_trazabilidad_uso` (
  `id_uso`                INT NOT NULL AUTO_INCREMENT,
  `id_orden`              INT NOT NULL,
  `tipo_recurso`          VARCHAR(20),
  `id_recurso_especifico` INT,   -- polimórfico, sin FK (antipatrón conocido)
  `cantidad_usada`        FLOAT,
  PRIMARY KEY (`id_uso`),
  FOREIGN KEY (`id_orden`)
    REFERENCES `tb_orden_trabajo`(`id_orden`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 8. GESTIÓN DE RECETAS (COCINA)
-- Modelos: PNTReceta → tb_pnt_recetas
--          PNTRecetaIngrediente → tb_pnt_receta_ingredientes
--          ComposicionReactivo → tb_composicion_reactivo
--          PNTRecurso → tb_pnt_recursos
-- ---------------------------------------------------------
CREATE TABLE `tb_pnt_recetas` (
  `id_receta`          INT NOT NULL AUTO_INCREMENT,
  `id_pnt`             INT NOT NULL,
  `nombre_receta`      VARCHAR(100),
  `cantidad_referencia` FLOAT,
  `unidad_referencia`  VARCHAR(20),
  `caducidad_horas`    INT,
  PRIMARY KEY (`id_receta`),
  FOREIGN KEY (`id_pnt`)
    REFERENCES `tb_pnt`(`id_pnt`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_pnt_receta_ingredientes` (
  `id_ingrediente_receta` INT NOT NULL AUTO_INCREMENT,
  `id_receta`             INT NOT NULL,
  `id_tipo_reactivo`      INT NOT NULL,
  `cantidad_necesaria`    FLOAT,
  PRIMARY KEY (`id_ingrediente_receta`),
  FOREIGN KEY (`id_receta`)
    REFERENCES `tb_pnt_recetas`(`id_receta`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_tipo_reactivo`)
    REFERENCES `tb_tipos_reactivo`(`id_tipo_reactivo`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_composicion_reactivo` (
  `id_composicion`    INT NOT NULL AUTO_INCREMENT,
  `id_reactivo_hijo`  INT NOT NULL,
  `id_reactivo_padre` INT NOT NULL,
  `cantidad_gastada`  FLOAT,
  PRIMARY KEY (`id_composicion`),
  FOREIGN KEY (`id_reactivo_hijo`)
    REFERENCES `tb_reactivos`(`id_reactivo`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_reactivo_padre`)
    REFERENCES `tb_reactivos`(`id_reactivo`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tb_pnt_recursos` (
  `id_pnt_recurso`     INT NOT NULL AUTO_INCREMENT,
  `id_pnt`             INT NOT NULL,
  `tipo_recurso`       VARCHAR(20),
  `id_tipo_necesario`  INT,   -- polimórfico, sin FK (antipatrón conocido)
  `cantidad_necesaria` FLOAT DEFAULT 1.0,
  PRIMARY KEY (`id_pnt_recurso`),
  FOREIGN KEY (`id_pnt`)
    REFERENCES `tb_pnt`(`id_pnt`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 9. TRAZABILIDAD
-- Modelo: TrazabilidadOrden → tb_trazabilidad_orden
-- ---------------------------------------------------------
CREATE TABLE `tb_trazabilidad_orden` (
  `id_traza`     INT NOT NULL AUTO_INCREMENT,
  `id_orden`     INT NOT NULL,
  `tipo_recurso` VARCHAR(20),
  `id_reactivo`  INT,
  `id_equipo`    INT,
  `fecha_uso`    DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_traza`),
  FOREIGN KEY (`id_orden`)
    REFERENCES `tb_orden_trabajo`(`id_orden`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_reactivo`)
    REFERENCES `tb_reactivos`(`id_reactivo`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  FOREIGN KEY (`id_equipo`)
    REFERENCES `tb_equipos`(`id_equipo`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------
-- 10. VISTAS (6 definitivas — 4 originales + 2 reescritas)
-- ---------------------------------------------------------
CREATE VIEW `view_reactivos_list` AS
SELECT
    id_reactivo,
    CONCAT('R-', LPAD(id_reactivo, 4, '0')) AS cod_interno,
    nombre,
    numero_lote,
    fecha_caducidad,
    estado_calidad
FROM `tb_reactivos`
WHERE is_deleted = 0;

CREATE VIEW `view_patrones_list` AS
SELECT
    id_reactivo                                AS id_patron,
    CONCAT('P-', LPAD(id_reactivo, 4, '0'))    AS cod_interno,
    nombre,
    clasificacion                              AS tipo_clasificacion,
    fecha_caducidad
FROM `tb_reactivos`
WHERE clasificacion IN ('MR', 'MRC', 'Patron')
  AND is_deleted = 0;

CREATE VIEW `view_equipos_list` AS
SELECT
    id_equipo,
    CONCAT('EQ-', LPAD(id_equipo, 3, '0')) AS cod_interno,
    nombre_equipo,
    numero_serie,
    fecha_prox_calib,
    estado_operativo
FROM `tb_equipos`
WHERE is_deleted = 0;

CREATE VIEW `view_muestras_list` AS
SELECT
    m.id_muestra,
    CONCAT('M-', LPAD(m.id_muestra, 5, '0')) AS cod_lims,
    c.nombre_fiscal                            AS cliente,
    m.referencia_cliente_externa               AS ref_cliente,
    m.tipo_muestra,
    m.fecha_recepcion
FROM `tb_muestras` m
JOIN `tb_recepcion` r ON m.id_recepcion = r.id_recepcion
JOIN `tb_clientes`  c ON r.id_cliente   = c.id_cliente
WHERE m.is_deleted = 0;

CREATE VIEW `view_ordenes_trabajo_list` AS
SELECT
    o.id_orden,
    CONCAT('OT-', LPAD(o.id_orden, 5, '0')) AS cod_orden,
    p.codigo_pnt,
    p.nombre_ensayo,
    o.fecha_inicio,
    u.username AS responsable,
    o.estado
FROM `tb_orden_trabajo` o
JOIN `tb_pnt`      p ON o.id_pnt                  = p.id_pnt
JOIN `tb_usuarios` u ON o.id_analista_responsable = u.id_usuario;

CREATE VIEW `view_disoluciones_list` AS
SELECT
    r.id_reactivo    AS id_disolucion,
    r.cod_interno    AS cod_lote,
    r.nombre         AS nombre_disolucion,
    r.numero_lote,
    r.cantidad_inicial,
    r.unidad,
    r.fecha_apertura AS fecha_preparacion,
    r.fecha_caducidad,
    r.estado_calidad AS estado
FROM `tb_reactivos` r
WHERE r.clasificacion = 'Disolucion'
  AND r.is_deleted = 0;

CREATE VIEW `view_calidad_pendiente` AS
SELECT
    o.id_orden,
    COALESCE(o.cod_orden, CONCAT('OT-', LPAD(o.id_orden, 5, '0'))) AS cod_orden,
    o.fecha_inicio,
    o.fecha_cierre                                                   AS fecha_finalizacion_tecnica,
    p.codigo_pnt,
    p.nombre_ensayo,
    CONCAT('M-', LPAD(MIN(m.id_muestra), 5, '0'))                   AS cod_lims,
    MIN(m.referencia_cliente_externa)                                AS referencia_cliente_externa,
    u.username                                                       AS analista,
    COUNT(DISTINCT r.id_resultado)                                   AS total_resultados,
    COUNT(DISTINCT t.id_traza)                                       AS recursos_usados
FROM `tb_orden_trabajo` o
JOIN  `tb_pnt`       p  ON o.id_pnt                  = p.id_pnt
JOIN  `tb_usuarios`  u  ON o.id_analista_responsable = u.id_usuario
LEFT JOIN `tb_orden_items`           oi ON o.id_orden          = oi.id_orden
LEFT JOIN `tb_submuestras_analisis`  sa ON oi.id_submuestra    = sa.id_submuestra
LEFT JOIN `tb_muestras`              m  ON sa.id_muestra_padre = m.id_muestra
LEFT JOIN `tb_resultados`            r  ON oi.id_item_orden    = r.id_item_orden
LEFT JOIN `tb_trazabilidad_orden`    t  ON o.id_orden          = t.id_orden
WHERE o.estado = 'Finalizada'
GROUP BY
    o.id_orden, o.cod_orden, o.fecha_inicio, o.fecha_cierre,
    p.codigo_pnt, p.nombre_ensayo, u.username;

-- ---------------------------------------------------------
-- 11. TRIGGERS (auditoría — compatible con nueva fecha_hora_utc)
-- ---------------------------------------------------------
DELIMITER $$
CREATE TRIGGER `audit_reactivos_update`
AFTER UPDATE ON `tb_reactivos`
FOR EACH ROW
BEGIN
    IF OLD.fecha_caducidad != NEW.fecha_caducidad
    OR OLD.estado_calidad  != NEW.estado_calidad
    THEN
        INSERT INTO `sys_audit_log`
            (usuario, tabla_afectada, id_registro, tipo_accion,
             valor_anterior, valor_nuevo, motivo_cambio)
        VALUES (
            'System_DB',
            'tb_reactivos',
            CONCAT('R-', LPAD(OLD.id_reactivo, 4, '0')),
            'UPDATE',
            CONCAT('Caducidad: ', OLD.fecha_caducidad, ', Estado: ', OLD.estado_calidad),
            CONCAT('Caducidad: ', NEW.fecha_caducidad, ', Estado: ', NEW.estado_calidad),
            'Trigger Auto-Audit'
        );
    END IF;
END$$
DELIMITER ;

-- ---------------------------------------------------------
-- 12. PROCEDIMIENTOS ALMACENADOS
-- Ninguno definido en el init.sql original.
-- ---------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------
-- 13. SEEDS
-- ---------------------------------------------------------

-- Roles (compatible con modelo Role — id_rol AUTO_INCREMENT)
INSERT INTO `tb_roles` (`nombre_rol`, `descripcion`) VALUES
  ('Admin',    'Superusuario'),
  ('Analista', 'Lab'),
  ('QA',       'Calidad');

-- Usuario admin (hash bcrypt fresco para admin123, generado 2026-04-09)
-- Hash viejo: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52au9gm.fo8ioG
INSERT INTO `tb_usuarios` (`username`, `password_hash`, `nombre_completo`, `id_rol`, `estado`)
VALUES (
  'admin',
  '$2b$12$ax6HDb14oOnbejE0weZU5.BUh.ghJ3n1kHNaVLiU65M3McDCn1Jqi',
  'Administrador Sistema',
  1,
  1
);

-- Cliente de demo (compatible: nombre_fiscal + email_contacto presentes en modelo Cliente)
INSERT INTO `tb_clientes` (`nombre_fiscal`, `email_contacto`)
VALUES ('Acme Pharma S.L.', 'lab@acme.com');

-- PNT de demo (compatible: codigo_pnt + nombre_ensayo; version_vigente e is_active tienen DEFAULT)
-- Sin columnas obligatorias (NOT NULL sin DEFAULT) pendientes.
INSERT INTO `tb_pnt` (`codigo_pnt`, `nombre_ensayo`)
VALUES ('PNT-HPLC-01', 'Determinación de Cafeína');

-- NOTA: El seed de tb_recetas del init.sql original no se incluye
-- porque la tabla fue refactorizada a tb_pnt_recetas con un esquema distinto.
-- Los seeds de demo data adicionales (recetas, reactivos de ejemplo, muestras)
-- se añadirán en una fase posterior dedicada a enriquecer el entorno de demo.
-- Añádelos manualmente si los necesitas en el entorno de desarrollo.
