# LIMS Core

A laboratory information management system prototype designed for ISO 17025 accredited analytical laboratories. Built with FastAPI, MySQL, and Streamlit.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

> 🇪🇸 [Versión en español](README.es.md)

## The Problem

Small and mid-sized analytical laboratories operating under ISO 17025 accreditation need to manage the complete lifecycle of a sample — from reception through analysis to the final Certificate of Analysis — while maintaining traceability, data integrity, and regulatory compliance.

Many of these laboratories still rely on disconnected spreadsheets, manual transcription between instruments and management systems, and paper-based review workflows. This leads to slow turnaround times, transcription errors, and difficult audit preparation.

LIMS Core is a working prototype that covers this lifecycle in a single system: client management, sample reception, work order planning, analytical execution with OOS detection, reagent traceability, quality review, and Certificate of Analysis generation in PDF.

## Project Status

> **This is a portfolio prototype**, not a production-ready system. It was built to demonstrate end-to-end LIMS architecture and domain knowledge in regulated laboratory environments. It is fully functional for demonstration purposes: you can register samples, execute work orders, review results through a quality module, and generate Certificates of Analysis.

> Known limitations and planned improvements are documented in the [Roadmap](#roadmap--known-limitations) section.

## Features

### Sample Lifecycle
- Client registry with fiscal data and contact information
- Sample reception with automatic LIMS coding (`M-YY_XXXXX`), multi-split derivation, and client reference tracking
- Work order planning linked to standardized analytical methods (PNTs)

### Analytical Execution
- Result entry grid with validation against specification limits
- Automatic OOS detection (Out of Specification) with deviation confirmation workflow
- Batch result saving with per-parameter validation status (`Draft → Validated → Correction`)
- Automatic order finalization when all parameters are validated

### Quality Review
- Dedicated module showing orders pending review (status: `Finalized`, awaiting QA approval)
- CoA preview download for reviewers before final approval
- Order closure only after quality sign-off

### Reporting
- Certificate of Analysis (CoA) generation in PDF via WeasyPrint + Jinja2
- Only validated results appear in the CoA (regulatory compliance)
- Download button integrated in Execution, Quality, and History modules

### Inventory & Traceability
- Unified reagent inventory covering commercial reagents, reference materials, standards, and prepared solutions
- Solution preparation with parent-child genealogy tracking
- Soft-delete pattern preserving audit history
- Expiration highlighting for reagents approaching shelf life

### History & Archive
- Sample and work order history with date range, status, and free-text filters
- Integrated CoA download per order
- Client-side filtering via pandas

### Data Integrity
- Foreign key constraints with explicit `ON DELETE` / `ON UPDATE` policies across all relationships
- Audit trail via MySQL trigger with server-managed UTC timestamps
- Data model aligned with ALCOA+ principles and designed for ISO 17025 / GxP environments

## Architecture

```
┌─────────────┐     HTTP/REST      ┌─────────────────┐     SQLAlchemy ORM     ┌──────────────┐
│  Streamlit   │ ◄────────────────► │    FastAPI       │ ◄──────────────────► │   MySQL 8.0   │
│  Frontend    │     Port 8501      │    Backend       │                      │   Database    │
│              │                    │    JWT auth      │                      │               │
│  - Pages     │                    │    Pydantic V2   │                      │   Views       │
│  - Filters   │                    │    WeasyPrint    │                      │   Triggers    │
└─────────────┘                    └─────────────────┘                      └──────────────┘
       │                                   │                                       │
       └───────────────────────────────────┴───────────────────────────────────────┘
                                    Docker Compose
                                  (3 services, 1 named volume)
```

Three-tier architecture, fully containerized with Docker Compose:

- **Frontend (Streamlit)**: Multi-page application handling user interaction, form rendering, and PDF downloads. Communicates with the backend via REST with Bearer token authentication.
- **Backend (FastAPI)**: Stateless API server with endpoints organized by domain. Validates inputs with Pydantic V2 schemas. Generates PDF reports with WeasyPrint.
- **Database (MySQL 8.0)**: Relational schema with foreign key constraints, views for common query patterns, and an audit trigger for change tracking. The schema is generated from SQLAlchemy ORM models as the single source of truth.

### Key architectural decisions

| Decision | Rationale |
|----------|-----------|
| SQLAlchemy models as source of truth | `init.sql` is generated from `models.py`, not maintained separately. This prevents ORM-database drift — a problem encountered and resolved during development. |
| JWT stateless authentication | No server-side session storage. Tokens are self-contained and validated per request. |
| MySQL triggers for audit trail | Audit logging at the database level captures even direct SQL modifications — relevant for ALCOA+ compliance in regulated environments. |
| SQL views for complex queries | Frequently joined datasets are encapsulated in views, keeping backend code clean and providing a stable query interface. |
| Soft-delete pattern | Records are never physically deleted. An `is_deleted` flag preserves full history, which is a regulatory requirement under ISO 17025. |
| Server-managed timestamps | Audit timestamps use `DEFAULT CURRENT_TIMESTAMP` at the MySQL level, ensuring consistency regardless of application layer. |

## Data Model

Some design choices that reflect the laboratory domain:

- **Unified reagent table**: Commercial reagents, reference materials, standards, and prepared solutions share a single table (`tb_reactivos`) differentiated by `clasificacion`. Prepared solutions link to their parent reagents through a composition table, providing genealogy traceability.
- **Sample derivation chain**: `tb_recepcion → tb_muestras → tb_submuestras_analisis → tb_orden_items` models the multi-split pattern where a single reception generates sub-samples routed to different analytical methods.
- **Result validation lifecycle**: Results move through `Draft → Validated → Correction`. Only validated results appear in the Certificate of Analysis. Corrections preserve the original value in the audit trail.
- **Explicit deletion policies**: Foreign keys use `CASCADE`, `RESTRICT`, or `SET NULL` based on the regulatory semantics of each relationship — chosen case by case, not by default.
- **Polymorphic references (known debt)**: Two columns use polymorphic integer references without FK constraints, marked with `TODO` comments in the codebase. The planned refactor involves exclusive arc pattern with CHECK constraints.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI 0.109+ | REST API with automatic OpenAPI documentation |
| ORM | SQLAlchemy 2.0+ | Declarative models and schema generation |
| Validation | Pydantic 2.6+ | Request/response schemas |
| Auth | python-jose + passlib | JWT tokens and bcrypt password hashing |
| Database | MySQL 8.0 | Relational storage with trigger support |
| Reports | WeasyPrint + Jinja2 | Server-side PDF generation |
| Frontend | Streamlit 1.36+ | UI with built-in data components |
| Infrastructure | Docker Compose | Three-service orchestration with health checks |

## Repository Structure

```
lims-core/
├── backend/
│   ├── routers/          # API endpoints by domain (auth, reception, execution, quality, ...)
│   ├── templates/        # Jinja2 template for CoA PDF generation
│   ├── models.py         # SQLAlchemy ORM models (source of truth for DB schema)
│   ├── schemas.py        # Pydantic V2 request/response schemas
│   ├── security.py       # JWT + bcrypt authentication
│   ├── database.py       # Connection pool configuration
│   ├── dependencies.py   # FastAPI dependency injection
│   ├── main.py           # Entry point and router registration
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── pages/            # Streamlit modules (config, lab, quality, history)
│   ├── app.py            # Navigation and authentication UI
│   ├── utils.py          # API client with Bearer token management
│   ├── Dockerfile
│   └── requirements.txt
├── sql/
│   └── init.sql          # Schema, views, trigger, and seed data
├── scripts/
│   └── reset_password.py # Dev utility: bcrypt hash generator
├── docker-compose.yml    # Service orchestration
├── .env.example          # Environment variable template
└── LICENSE
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/AlexMG9/lims-core.git
cd lims-core
```

2. **Create your environment file**

```bash
cp .env.example .env
```

Edit `.env` and set secure values. Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. **Start the system**

```bash
docker compose up --build
```

The first launch takes a few minutes while Docker builds images and MySQL initializes the schema.

4. **Access the application**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8501 |
| API Docs | http://localhost:8000/docs |

5. **Demo credentials**

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Administrator |

> These are development credentials seeded by `init.sql`. Change them immediately in any non-demo environment.

### Stopping

```bash
docker compose down        # Stop (data persists in volume)
docker compose down -v     # Stop and reset database (full clean start)
```

## Roadmap & Known Limitations

### Limitations

- **No automated tests**. Adding pytest API tests for core endpoints is the highest-priority improvement.
- **No role-based access control**. The roles table exists but endpoint-level permission checks are not implemented.
- **Inconsistent frontend error handling**. The Quality module reports errors explicitly; other modules use silent fallbacks.
- **No email integration**. CoA delivery is via PDF download only.

### Planned

- [ ] Pytest integration tests for critical API paths
- [ ] RBAC middleware using existing `tb_roles`
- [ ] Refactor polymorphic references to exclusive arc with CHECK constraints
- [ ] CoA template with laboratory logo and digital signature placeholder
- [ ] Batch sample import via CSV
- [ ] Instrument data parser for automated result ingestion (ICP-MS, HPLC export files)
- [ ] Email delivery of Certificates of Analysis
- [ ] Comprehensive demo dataset with realistic sample data

## About the Author

**Alejandro Martín García**

PhD Analytical Chemistry · IT Specialist

Background in ISO 17025 laboratory environments. Built this project to solve problems I encountered working with analytical data management in accredited labs.

[LinkedIn](https://www.linkedin.com/in/alejandromartingarcia) · alex.martn.garcia@gmail.com

## License

MIT — see [LICENSE](LICENSE).

---

<sub>Built with AI-assisted pair programming. Data model, architecture, and domain logic are the result of a human-led iterative design process.</sub>
