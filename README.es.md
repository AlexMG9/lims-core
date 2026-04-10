# LIMS Core

Prototipo de sistema de gestión de información de laboratorio (LIMS) diseñado para laboratorios analíticos acreditados bajo ISO 17025. Construido con FastAPI, MySQL y Streamlit.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

> 🇬🇧 [English version](README.md)

## El problema

Los laboratorios analíticos pequeños y medianos que operan bajo acreditación ISO 17025 necesitan gestionar el ciclo de vida completo de una muestra — desde la recepción hasta el Certificado de Análisis final — manteniendo la trazabilidad, la integridad de datos y el cumplimiento normativo.

Muchos de estos laboratorios aún dependen de hojas de cálculo desconectadas, transcripción manual entre instrumentos y sistemas de gestión, y flujos de revisión en papel. Esto provoca tiempos de respuesta lentos, errores de transcripción y una preparación de auditorías innecesariamente costosa.

LIMS Core es un prototipo funcional que cubre este ciclo en un único sistema: gestión de clientes, recepción de muestras, planificación de órdenes de trabajo, ejecución analítica con detección de OOS, trazabilidad de reactivos, revisión de calidad y generación de Certificados de Análisis en PDF.

## Estado del proyecto

> **Este es un prototipo de portfolio**, no un sistema en producción. Fue construido para demostrar una arquitectura LIMS completa y conocimiento del dominio de laboratorios regulados. Es completamente funcional a nivel demostrativo: se pueden registrar muestras, ejecutar órdenes de trabajo, revisar resultados mediante el módulo de calidad y generar Certificados de Análisis.

> Las limitaciones conocidas y las mejoras previstas están documentadas en la sección [Roadmap](#roadmap-y-limitaciones-conocidas).

## Funcionalidades

### Ciclo de vida de la muestra
- Registro de clientes con datos fiscales e información de contacto
- Recepción de muestras con codificación LIMS automática (`M-YY_XXXXX`), derivación multi-split y seguimiento de referencias del cliente
- Planificación de órdenes de trabajo vinculadas a métodos analíticos normalizados (PNTs)

### Ejecución analítica
- Grid de entrada de resultados con validación contra límites de especificación
- Detección automática de OOS (Out of Specification) con flujo de confirmación de desviaciones
- Guardado de resultados por lote con estado de validación por parámetro (`Borrador → Validado → Corrección`)
- Finalización automática de la orden cuando todos los parámetros están validados

### Revisión de calidad
- Módulo dedicado mostrando las órdenes pendientes de revisión (estado: `Finalizada`, a la espera de aprobación de calidad)
- Descarga previa del CoA para revisión antes de la aprobación definitiva
- Cierre de la orden solo tras el visto bueno de calidad

### Informes
- Generación de Certificados de Análisis (CoA) en PDF mediante WeasyPrint + Jinja2
- Solo los resultados validados aparecen en el CoA (cumplimiento normativo)
- Botón de descarga integrado en los módulos de Ejecución, Calidad e Histórico

### Inventario y trazabilidad
- Inventario unificado de reactivos que cubre reactivos comerciales, materiales de referencia, patrones y disoluciones preparadas internamente
- Preparación de disoluciones con trazabilidad genealógica padre-hijo
- Patrón de borrado lógico (soft-delete) que preserva el historial de auditoría
- Alertas visuales para reactivos próximos a caducidad

### Histórico y archivo
- Historial completo de muestras y órdenes de trabajo con filtros por rango de fechas, estado y texto libre
- Descarga de CoA integrada por orden
- Filtrado en el cliente mediante pandas

### Integridad de datos
- Claves foráneas con políticas explícitas `ON DELETE` / `ON UPDATE` en todas las relaciones
- Audit trail mediante trigger MySQL con marcas temporales UTC gestionadas por el servidor
- Modelo de datos alineado con los principios ALCOA+ y diseñado para entornos ISO 17025 / GxP

## Arquitectura

```
┌─────────────┐     HTTP/REST      ┌─────────────────┐     SQLAlchemy ORM     ┌──────────────┐
│  Streamlit   │ ◄────────────────► │    FastAPI       │ ◄──────────────────► │   MySQL 8.0   │
│  Frontend    │     Puerto 8501    │    Backend       │                      │   Base datos  │
│              │                    │    JWT auth      │                      │               │
│  - Páginas   │                    │    Pydantic V2   │                      │   Vistas      │
│  - Filtros   │                    │    WeasyPrint    │                      │   Triggers    │
└─────────────┘                    └─────────────────┘                      └──────────────┘
       │                                   │                                       │
       └───────────────────────────────────┴───────────────────────────────────────┘
                                    Docker Compose
                                  (3 servicios, 1 volumen nombrado)
```

Arquitectura de tres capas, completamente contenerizada con Docker Compose:

- **Frontend (Streamlit)**: Aplicación multipágina que gestiona la interacción del usuario, formularios y descargas de PDF. Se comunica con el backend por REST con autenticación Bearer.
- **Backend (FastAPI)**: Servidor API sin estado con endpoints organizados por dominio. Valida entradas con esquemas Pydantic V2. Genera informes PDF con WeasyPrint.
- **Base de datos (MySQL 8.0)**: Esquema relacional con claves foráneas, vistas para consultas frecuentes y un trigger de auditoría. El esquema se genera desde los modelos SQLAlchemy como fuente de verdad única.

### Decisiones arquitectónicas clave

| Decisión | Razonamiento |
|----------|-------------|
| Modelos SQLAlchemy como fuente de verdad | `init.sql` se genera desde `models.py`, no se mantiene por separado. Esto previene desincronización entre ORM y base de datos — un problema que encontramos y resolvimos durante el desarrollo. |
| Autenticación JWT sin estado | Sin almacenamiento de sesiones en el servidor. Los tokens son autocontenidos y se validan en cada petición. |
| Triggers MySQL para audit trail | El registro de auditoría ocurre a nivel de base de datos y captura incluso modificaciones SQL directas — relevante para cumplimiento ALCOA+ en entornos regulados. |
| Vistas SQL para consultas complejas | Los datasets de consultas frecuentes están encapsulados en vistas, manteniendo limpio el código del backend y proporcionando una interfaz de consulta estable. |
| Patrón soft-delete | Los registros nunca se borran físicamente. Un flag `is_deleted` preserva el historial completo, un requisito normativo bajo ISO 17025. |
| Timestamps gestionados por el servidor | Los timestamps de auditoría usan `DEFAULT CURRENT_TIMESTAMP` a nivel MySQL, asegurando consistencia independientemente de la capa de aplicación. |

## Modelo de datos

Decisiones de diseño que reflejan el dominio de laboratorio:

- **Tabla unificada de reactivos**: Reactivos comerciales, materiales de referencia, patrones y disoluciones preparadas comparten una única tabla (`tb_reactivos`) diferenciada por `clasificacion`. Las disoluciones preparadas enlazan a sus reactivos padre mediante una tabla de composición, proporcionando trazabilidad genealógica.
- **Cadena de derivación de muestras**: `tb_recepcion → tb_muestras → tb_submuestras_analisis → tb_orden_items` modela el patrón multi-split donde una recepción genera submuestras encaminadas a distintos métodos analíticos.
- **Ciclo de vida de resultados**: Los resultados pasan por `Borrador → Validado → Corrección`. Solo los resultados validados aparecen en el Certificado de Análisis. Las correcciones preservan el valor original en el audit trail.
- **Políticas de borrado explícitas**: Las claves foráneas usan `CASCADE`, `RESTRICT` o `SET NULL` en función de la semántica regulatoria de cada relación, decidida caso por caso.
- **Referencias polimórficas (deuda técnica conocida)**: Dos columnas usan referencias enteras polimórficas sin restricciones FK, marcadas con comentarios `TODO` en el código. El refactor previsto implica patrón exclusive arc con restricciones CHECK.

## Stack tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| Backend | FastAPI 0.109+ | API REST con documentación OpenAPI automática |
| ORM | SQLAlchemy 2.0+ | Modelos declarativos y generación de esquema |
| Validación | Pydantic 2.6+ | Esquemas de petición/respuesta |
| Autenticación | python-jose + passlib | Tokens JWT y hash de contraseñas bcrypt |
| Base de datos | MySQL 8.0 | Almacenamiento relacional con soporte de triggers |
| Informes | WeasyPrint + Jinja2 | Generación de PDF en servidor |
| Frontend | Streamlit 1.36+ | Interfaz con componentes de datos integrados |
| Infraestructura | Docker Compose | Orquestación de tres servicios con health checks |

## Estructura del repositorio

```
lims-core/
├── backend/
│   ├── routers/          # Endpoints API por dominio (auth, recepción, ejecución, calidad, ...)
│   ├── templates/        # Plantilla Jinja2 para generación de CoA en PDF
│   ├── models.py         # Modelos SQLAlchemy ORM (fuente de verdad del esquema)
│   ├── schemas.py        # Esquemas Pydantic V2 de petición/respuesta
│   ├── security.py       # Autenticación JWT + bcrypt
│   ├── database.py       # Configuración del pool de conexiones
│   ├── dependencies.py   # Inyección de dependencias FastAPI
│   ├── main.py           # Punto de entrada y registro de routers
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── pages/            # Módulos Streamlit (configuración, laboratorio, calidad, histórico)
│   ├── app.py            # Navegación y autenticación
│   ├── utils.py          # Cliente API con gestión de Bearer token
│   ├── Dockerfile
│   └── requirements.txt
├── sql/
│   └── init.sql          # Esquema, vistas, trigger y datos iniciales
├── scripts/
│   └── reset_password.py # Utilidad de desarrollo: generador de hashes bcrypt
├── docker-compose.yml    # Orquestación de servicios
├── .env.example          # Plantilla de variables de entorno
└── LICENSE
```

## Puesta en marcha

### Requisitos previos

- Docker y Docker Compose
- Git

### Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/AlexMG9/lims-core.git
cd lims-core
```

2. **Crear el archivo de entorno**

```bash
cp .env.example .env
```

Edita `.env` y establece valores seguros. Genera una clave secreta con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. **Arrancar el sistema**

```bash
docker compose up --build
```

El primer arranque tarda unos minutos mientras Docker construye las imágenes y MySQL inicializa el esquema.

4. **Acceder a la aplicación**

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:8501 |
| Docs API | http://localhost:8000/docs |

5. **Credenciales de demostración**

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | Administrador |

> Son credenciales de desarrollo creadas automáticamente por `init.sql`. En cualquier entorno no demostrativo, cambiar la contraseña inmediatamente.

### Parada

```bash
docker compose down        # Parar (los datos persisten en el volumen)
docker compose down -v     # Parar y resetear la base de datos (arranque limpio)
```

## Roadmap y limitaciones conocidas

### Limitaciones

- **Sin tests automatizados**. Añadir tests pytest para los endpoints principales es la mejora de mayor prioridad.
- **Sin control de acceso por roles (RBAC)**. La tabla de roles existe pero la verificación de permisos a nivel de endpoint no está implementada.
- **Gestión de errores inconsistente en el frontend**. El módulo de Calidad reporta errores explícitamente; otros módulos usan fallbacks silenciosos.
- **Sin integración de email**. La entrega de CoA es únicamente por descarga de PDF.

### Mejoras previstas

- [ ] Tests de integración pytest para las rutas API críticas
- [ ] Middleware RBAC usando la tabla `tb_roles` existente
- [ ] Refactorizar referencias polimórficas a patrón exclusive arc con restricciones CHECK
- [ ] Plantilla de CoA con logotipo de laboratorio y placeholder de firma digital
- [ ] Importación masiva de muestras por CSV
- [ ] Parser de datos instrumentales para ingesta automática de resultados (exports ICP-MS, HPLC)
- [ ] Envío de Certificados de Análisis por email
- [ ] Dataset de demostración completo con datos realistas

## Sobre el autor

**Alejandro Martín García**

Doctor en Química Analítica · Técnico en Informática

Experiencia en laboratorios acreditados bajo ISO 17025. Este proyecto nace de problemas reales que encontré trabajando con la gestión de datos analíticos en esos entornos.

[LinkedIn](https://www.linkedin.com/in/alejandromartingarcia) · alex.martn.garcia@gmail.com

## Licencia

MIT — ver [LICENSE](LICENSE).

---

<sub>Proyecto desarrollado con pair programming asistido por IA. El modelo de datos, la arquitectura y la lógica de dominio son resultado de un proceso de diseño iterativo liderado por el autor.</sub>
