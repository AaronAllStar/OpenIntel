# OpenIntel 🛰️
> **Unified, Interactive, and Self-Hosted OSINT Intelligence Platform**  
> *Plataforma Unificada, Interactiva y Autohospedada de Inteligencia OSINT*

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](src/ui)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)](src/ui/tailwind.config.js)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌐 Language Navigation / Navegación por Idioma
* 🇬🇧 [English Documentation](#-english-documentation)
* 🇪🇸 [Documentación en Español](#-documentación-en-español)

---

# 🇬🇧 English Documentation

## Overview
**OpenIntel** is a modern, self-hosted OSINT (Open Source Intelligence) investigation cockpit designed for security analysts, journalists, and authorized investigators. It orchestrates **27 specialized reconnaissance engines** behind a sleek, cyberpunk-inspired real-time web dashboard.

Unlike legacy command-line tools that operate in silos, OpenIntel normalizes, deduplicates, and correlates findings into an interactive graph with strict evidence provenance tracking, public registry validation, and legal classifications.

---

## Key Features

* **Interactive Cyber OSINT Cockpit**:
  * Real-time spinning radar widget and operational telemetry.
  * Live Server-Sent Events (SSE) streaming logs and progress indicators.
  * Interactive relationship graph and evidence provenance inspection modal.
* **5 Tailored Multi-Modal Search Spaces**:
  * 👤 **Person (Name & Surname)**: Dedicated fields for First Name, Last Name, and optional Company/Domain to infer corporate email schemas.
  * 📱 **Phone with Country Selector**: Interactive dropdown with international flags and dial codes (+34, +52, +1, +57, +54, etc.) formatted automatically to ITU E.164.
  * 🌍 **Location (Country & City)**: Geographic reconnaissance mapped to cities and regions.
  * 🪪 **National ID & Tax Identifiers**: Country-specific checksum validation for 70+ countries (SSN, DNI, NIE, CPF, CURP, RFC, etc.) using `python-stdnum` and `idnumbers`.
  * 🌐 **Digital & Network Assets**: Usernames, corporate emails, domains, URLs, IPs, and Git repositories.
* **Granular Facet & Engine Selection ("Choose What You Need")**:
  * One-click presets: *Social Only*, *Phone & WhatsApp*, *Corporate Recon*, *Infrastructure & Leaks*, *ID Validation*, or *All Engines*.
  * Modular checkboxes categorized by domain.
* **Specialized Platform Adapters**:
  * 🐦 **X (Twitter)**: Sherlock + `Twikit` (public guest lookup without API keys) + Socialscan.
  * 📸 **Instagram**: Sherlock + `Instaloader` (public profile and metadata extraction) + Socialscan.
  * 💬 **WhatsApp**: `WhatsAppAdapter` (Click-to-Chat `wa.me` verification, presence signal, vCard links) + PhoneInfoga + `phonenumbers`.
  * 💼 **Business Emails**: `EmailEnrich` (pattern generator `first.last@company.com` + async DNS MX validation) + theHarvester + `EmailFinder`.
* **Single-Container Multi-Stage Docker Packaging**:
  * Single container serving both the React/Tailwind frontend and the FastAPI backend on port `8000`.

---

## Integrated OSINT Engines (27 Adapters)

| Category | Engines | Capabilities |
|---|---|---|
| **Social & Profiles** | **Sherlock**, **Maigret**, **Blackbird**, **Twikit**, **Instaloader**, **Socialscan** | Multi-platform username scans, profile correlation, bio metadata, and non-intrusive registration signal probes. |
| **Phone & Messaging** | **WhatsApp**, **PhoneInfoga**, **Bellingcat Telegram**, **SearchPhone**, **Ignorant** | ITU E.164 normalization, carrier lookup, WhatsApp presence, and Telegram signals. |
| **Corporate & Emails** | **Email Enrich**, **Email Finder**, **theHarvester**, **Holehe**, **GHunt**, **H8mail**, **CrossLinked** | Business email pattern permutations, async DNS MX verification, role mailboxes, Google footprint, breach disclosures, and LinkedIn mapping. |
| **Network & Code** | **Amass**, **DNSTwist**, **Recon-ng**, **SpiderFoot**, **Photon**, **OctoSuite**, **TruffleHog**, **Metagoofil** | External DNS mapping, typo-squatting permutations, deep web crawling, GitHub repository audit, leaked secrets/keys, and document metadata. |
| **National Registries** | **ID Validation** | Official checksum verification across 70+ countries (DNI, NIE, SSN, CPF, RFC, NIF, CURP). |

---

## Quick Start with Docker

### Option A: Run the Unified Single Container (Recommended)

Run OpenIntel directly with SQLite (no external database needed):

```bash
# 1. Build the unified image (frontend + backend)
docker build -t openintel:latest .

# 2. Launch the container
docker run -d --name openintel-app -p 8000:8000 openintel:latest
```

Open your browser at 👉 **http://localhost:8000/**

### Option B: Run with Docker Compose (PostgreSQL & Redis)

For persistent multi-user environments with PostgreSQL and Redis:

```bash
docker compose up -d --build
```

---

## Local Development (Without Docker)

### Prerequisites
* Python 3.12+ (or `uv`)
* Node.js 20+ & npm

```bash
# 1. Clone repository
git clone https://github.com/your-org/openintel.git
cd openintel

# 2. Install Python dependencies
uv venv
uv pip install -e ".[dev]"

# 3. Install and build Frontend
cd src/ui
npm install
npm run build
cd ../..

# 4. Start Local Backend
uv run uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000
```

### Running Tests & Quality Checks
```bash
# Run complete test suite (27 unit, contract & integration tests)
uv run --no-sync pytest tests/ -v

# Run code style & linter
uv run --no-sync ruff check src tests
```

---

## Legal & Public-Information Model

Every collected observation is explicitly classified according to its legal origin:
* `PUBLIC_OBSERVATION`: Unauthenticated crawling, search indexing, and public commit histories.
* `PUBLIC_REGISTRY`: Authoritative registries (DNS records, ITU-T E.164 telecom plans, official national ID checksum rules).
* `PLATFORM_SIGNAL`: Non-intrusive public account registration presence signals without credential stuffing.
* `INFERENCE`: Correlated link relationships derived by the correlation engine.

---

<br />

# 🇪🇸 Documentación en Español

## Descripción General
**OpenIntel** es una plataforma moderna y autohospedada de investigación OSINT (Inteligencia de Fuentes Abiertas) diseñada para analistas de seguridad, periodistas de investigación y peritos forenses. Orquesta **27 motores de reconocimiento especializados** bajo un panel de control interactivo en tiempo real con estética cibernética de alta fidelidad.

A diferencia de las herramientas tradicionales de terminal, OpenIntel normaliza, desduplica y correlaciona todos los hallazgos en un grafo interactivo con trazabilidad estricta de procedencia, validación de registros públicos y clasificación legal de evidencias.

---

## Características Principales

* **Cockpit Interactivo Cyber-OSINT**:
  * Widget de **Radar Activo** con haz giratorio y telemetría operativa en vivo.
  * Transmisión de registros en tiempo real mediante *Server-Sent Events* (SSE) y barras de progreso dinámicas.
  * Grafo interactivo de entidades y relaciones, con modal de inspección de evidencia original.
* **5 Espacios de Búsqueda Especializados (`SearchCockpit`)**:
  * 👤 **Persona (Nombre y Apellido)**: Campos dedicados para Nombre, Apellido(s) y Empresa / Dominio (opcional) para derivar esquemas de correo corporativo.
  * 📱 **Teléfono con Selector de País**: Menú desplegable interactivo con banderas y prefijos internacionales (🇪🇸 +34, 🇲🇽 +52, 🇺🇸 +1, 🇨🇴 +57, 🇦🇷 +54, etc.) normalizado a E.164.
  * 🌍 **Localización (País y Ciudad)**: Reconocimiento geoespacial estructurado por país y ciudad/región.
  * 🪪 **Documento de Identidad por País**: Validación de algoritmo de dígito de control para 70+ países (DNI/NIE en España, CURP/RFC en México, SSN en EE. UU., CPF en Brasil, etc.) mediante `python-stdnum` e `idnumbers`.
  * 🌐 **Activos Digitales y de Red**: Usuarios de redes, correos corporativos, dominios, URLs, direcciones IP y repositorios Git.
* **Selección Modular de Facetas y Motores ("Poder seleccionar lo que necesito")**:
  * Presets rápidos: *Solo Redes Sociales*, *Teléfono y WhatsApp*, *Reconocimiento Corporativo*, *Infraestructura y Fugas*, *Validación de Documentos*, o *Todos los Motores*.
  * Checkboxes categorizados para encender o apagar motores a demanda.
* **Adaptadores de Plataforma Especializados**:
  * 🐦 **X (Twitter)**: Sherlock + `Twikit` (sondeo público de invitado sin claves API) + Socialscan.
  * 📸 **Instagram**: Sherlock + `Instaloader` (extracción de perfil público, biografía y metadatos) + Socialscan.
  * 💬 **WhatsApp**: `WhatsAppAdapter` (verificación de presencia `wa.me`, enlace de chat directo y vCard) + PhoneInfoga + `phonenumbers`.
  * 💼 **Correos Corporativos**: `EmailEnrich` (generación de permutaciones `nombre.apellido@empresa.com` + resolución DNS MX asíncrona) + theHarvester + `EmailFinder`.
* **Empaquetado en un Solo Contenedor Docker Multi-Etapa**:
  * Un único contenedor que sirve tanto la interfaz React/Tailwind como el backend FastAPI en el puerto `8000`.

---

## Catálogo de Motores Integrados (27 Adaptadores)

| Categoría | Motores | Capacidades |
|---|---|---|
| **Redes y Perfiles** | **Sherlock**, **Maigret**, **Blackbird**, **Twikit**, **Instaloader**, **Socialscan** | Rastreo de alias en 500+ sitios, correlación de perfiles, extracción de biografías y sondeos de señal de cuenta. |
| **Teléfono y Mensajería** | **WhatsApp**, **PhoneInfoga**, **Bellingcat Telegram**, **SearchPhone**, **Ignorant** | Normalización ITU E.164, operador de telecomunicaciones, enlaces de chat directo wa.me y presencia en Telegram. |
| **Empresa y Correos** | **Email Enrich**, **Email Finder**, **theHarvester**, **Holehe**, **GHunt**, **H8mail**, **CrossLinked** | Permutaciones de correo corporativo, validación DNS MX, buzones públicos (contact@, security@), huella en Google, brechas y mapeo en LinkedIn. |
| **Infraestructura y Código** | **Amass**, **DNSTwist**, **Recon-ng**, **SpiderFoot**, **Photon**, **OctoSuite**, **TruffleHog**, **Metagoofil** | Cartografía DNS externa, detección de typosquatting/phishing, rastreo web rápido, auditoría de commits y secretos en repositorios y metadatos de documentos. |
| **Registros Oficiales** | **ID Validation** | Algoritmos de comprobación de dígitos de control para documentos de identidad y fiscales en 70+ países. |

---

## Inicio Rápido con Docker

### Opción A: Contenedor Único Autocontenido (Recomendado)

Inicia OpenIntel directamente con base de datos SQLite integrada (sin necesidad de configurar servicios externos):

```bash
# 1. Construir la imagen unificada (frontend + backend)
docker build -t openintel:latest .

# 2. Iniciar el contenedor
docker run -d --name openintel-app -p 8000:8000 openintel:latest
```

Abre tu navegador en 👉 **http://localhost:8000/**

### Opción B: Arranque con Docker Compose (PostgreSQL y Redis)

Para entornos persistentes con PostgreSQL y Redis:

```bash
docker compose up -d --build
```

---

## Desarrollo Local (Sin Docker)

### Requisitos Previos
* Python 3.12+ (o `uv`)
* Node.js 20+ y npm

```bash
# 1. Clonar el repositorio
git clone https://github.com/your-org/openintel.git
cd openintel

# 2. Instalar dependencias de Python
uv venv
uv pip install -e ".[dev]"

# 3. Compilar el Frontend interactivo
cd src/ui
npm install
npm run build
cd ../..

# 4. Iniciar el servidor local
uv run uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000
```

### Ejecución de Pruebas y Control de Calidad
```bash
# Ejecutar suite de pruebas completa (27 tests)
uv run --no-sync pytest tests/ -v

# Ejecutar formateador y linter ruff
uv run --no-sync ruff check src tests
```

---

## Marco Legal y de Acceso a Información Pública

Cada evidencia recolectada por OpenIntel cuenta con una clasificación formal de origen y legalidad:
* `PUBLIC_OBSERVATION`: Indexación pública, rastreo no autenticado y registros visibles en la web.
* `PUBLIC_REGISTRY`: Registros autorizados (DNS, planes de numeración ITU-T E.164, algoritmos públicos de documentos de identidad).
* `PLATFORM_SIGNAL`: Sondas no intrusivas de existencia de cuenta sin uso de contraseñas ni ataques de fuerza bruta.
* `INFERENCE`: Correlaciones deducidas a través del motor de enlace de entidades.
