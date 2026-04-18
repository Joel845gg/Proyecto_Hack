# Benchmark 360: Inteligencia Competitiva Automatizada

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-green.svg)
![uv](https://img.shields.io/badge/uv-Package%20Manager-purple.svg)

**Benchmark 360** es un *Data Product de grado Enterprise* construido para el Hackathon de Netlife, diseñado para resolver el problema de monitoreo comercial en el océano rojo de ISPs ecuatorianos. 

La herramienta monitorea y estandariza las ofertas, precios y velocidades de los principales competidores (Netlife, Claro, Ecuanet, CNT, Xtrim, Celerity, Alfanet, Fibramax) automatizando un proceso manual a través de un arquitectura híbrida robusta.

## 🚀 Arquitectura "Híbrida" e Inteligencia Artificial

Este pipeline destaca por su flexibilidad y resiliencia ante roturas del código HTML o bloqueos de IP comerciales:
1. **Extracción en Crudo (Raw Requests):** Navega por las páginas como un navegador fantasma evadiendo tiempos de carga y dependencias gráficas pesadas de Selenium.
2. **Generative Guardrail (Gemini Flash):** En lugar de depender de reglas XPATH frágiles o selectores de BeautifulSoup, todo el código fuente y las variables `Javascript` ocultas fluyen hacia el modelo `Gemini 2.5 Flash`. El LLM extrae meticulosamente todos los planes, deduciendo las combinaciones lógicas del negocio (por ejemplo, estructuras *"Arma tu plan"*).
3. **Escudo Anti-Prompt Injection:** Implementamos etiquetas especiales en el `System Prompt` de la IA que previenen inyecciones cruzadas desde las páginas web de los competidores.
4. **Validación Inquebrantable (Pydantic V2):** Toda inferencia del LLM rebota de manera determinística contra dictámenes estrictos, asegurando la existencia de las *30 columnas operativas* exigidas en el reto (incluyendo cálculos automáticos de métricas de descuento y diccionarios snake_case).

## 🗂️ Estructura del Proyecto

* `src/pipeline.py`: El orquestador principal del proyecto que lidera la inserción en la factoría y consolida la salida Dual (JSON y Parquet).
* `src/parser/gemini_extractor.py`: Motor del LLM basado en el API de GenAI de Google que extrae datos directamente del código fuente web.
* `src/models/plan_schema.py`: Reglas duras y tipado estricto `Pydantic V2` para validación antes de guardar.
* `src/scraper/`: Módulos de fallback para extracción tradicional adaptada.
* `output/`: Directorio autogenerado que agrupa en tiempo real la ingesta en formatos `.json` y el solicitado `.parquet`.
* `notebook/benchmark_industria_notebook.ipynb`: Demostración visual e investigaciones del EDA para el jurado.

## 🛠️ Instalación y Uso de Ejecución Rápida

Se utiliza [uv](https://github.com/astral-sh/uv) como gestor de paquetes para garantizar trazabilidad y eficiencia a nivel de entorno global.

### 1. Clonar el repositorio
```bash
git clone https://github.com/Joel845gg/Proyecto_Hack.git
cd Proyecto_Hack
```

### 2. Variables de Entorno
Crea un archivo llamado `.env` en la raíz (Este archivo no se versiona por seguridad) e incluye tu Google AI Studio API:
```env
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Sincronización y Ejecución
```bash
# Sincroniza todas las dependencias
uv sync

# Dispara el Pipeline
uv run python src/pipeline.py
```

Al cabo de menos de un minuto, los archivos maestrales reposarán en el directorio local listos para ser explotados por los analistas Pricing de Netlife.

## ✅ Criterios de Éxito Superados
- Entregado 100% en Python 3.12 y gestión con `uv`.
- Estructuración JSON anidada correcta de `pys_adicionales_detalle` estandarizada.
- Mecanismo "Arma tu Plan" resuelto a través de inferencia combinatoria LLM.
- Generación de Archivo Parquet (`benchmark_industria.parquet`).


env

- OPENAI_API_KEY=
- GEMINI_API_KEY=
