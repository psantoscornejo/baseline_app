# Baseline Solutions — Guía Interactiva de Cierre de Minas

Aplicación web interactiva que consolida el estado del arte en cierre de minas para Chile, integrando tres marcos:

- **Ley 20.551 chilena** y guías metodológicas de SERNAGEOMIN
- **ICMM Integrated Mine Closure Good Practice Guide (2019)** — los 17 elementos
- **GISTM Global Industry Standard on Tailings Management (2020)** — 15 principios / 77 requisitos

## Contenido de la app

1. **Inicio** — página principal con el logo de Baseline Solutions y resumen de la herramienta
2. **Marco regulatorio Chile** — clasificación de planes, contenidos, garantías financieras, auditorías RPAE, guías SERNAGEOMIN
3. **ICMM Integrated Mine Closure** — los 17 elementos navegables con descripción, entregable típico y fase del Life of Asset
4. **GISTM** — los 15 principios agrupados en 6 topics, con referencia cruzada a normativa chilena
5. **Matriz de correlación** — cruce SERNAGEOMIN ↔ ICMM ↔ GISTM con recomendaciones concretas de incorporación
6. **Roadmap de cumplimiento** — hoja de ruta en 7 fases (diagnóstico → relinquishment)
7. **Checklist auto-evaluable** — auto-evaluación con scoring por marco y exportable
8. **Referencias y descargas** — enlaces oficiales + exportación de tablas en CSV

## Cómo ejecutarla

### Requisitos previos

- Python 3.9 o superior
- pip

### Instalación

```bash
# 1. Clonar o copiar la carpeta baseline_app
cd baseline_app

# 2. (Opcional pero recomendado) crear entorno virtual
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# .venv\Scripts\activate      # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Ejecución

```bash
streamlit run app.py
```

Streamlit levantará automáticamente un servidor local (por defecto en http://localhost:8501) y abrirá la aplicación en tu navegador. Si no se abre sola, copia la URL que aparece en la terminal.

## Estructura de archivos

```
baseline_app/
├── app.py              # Aplicación principal Streamlit
├── logo.jpeg           # Logo de Baseline Solutions (se muestra en sidebar + inicio)
├── requirements.txt    # Dependencias Python
└── README.md           # Este archivo
```

## Despliegue en la web (opcional)

La aplicación está lista para desplegarse gratis en **Streamlit Community Cloud**:

1. Sube la carpeta `baseline_app/` a un repositorio de GitHub (puede ser privado).
2. Entra a https://share.streamlit.io y conecta tu cuenta GitHub.
3. Selecciona el repositorio, la rama y el archivo `app.py`.
4. Click en *Deploy*. En 1–2 minutos tendrás una URL pública compartible.

Alternativas de despliegue: Render, Railway, Hugging Face Spaces, Azure App Service, AWS App Runner.

## Personalización

- **Paleta de marca**: edita las constantes `BRAND_DARK`, `BRAND_ORANGE`, `BRAND_SLATE` al inicio de `app.py` si quieres ajustar los colores.
- **Logo**: reemplaza `logo.jpeg` por tu versión en mayor resolución. Si cambias el nombre, ajusta la función `get_logo_base64()`.
- **Contenidos**: todas las listas de datos (guías, elementos ICMM, principios GISTM, matriz de correlación, roadmap) están como estructuras Python al inicio del archivo; son fáciles de editar sin tocar la lógica de interfaz.

## Disclaimer

Esta herramienta es una guía de referencia general sobre el estado del arte en cierre de minas. No reemplaza asesoría legal ni técnica especializada. La normativa chilena y los estándares internacionales evolucionan; verifica siempre las versiones vigentes antes de aplicar los contenidos a un caso real.

---

**Baseline Solutions** · v1.0
