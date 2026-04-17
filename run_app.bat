@echo off
cd /d "%~dp0"

if exist ".venv_app\Scripts\activate.bat" (
    call .venv_app\Scripts\activate.bat
) else (
    echo Creando entorno virtual...
    python -m venv .venv_app
    call .venv_app\Scripts\activate.bat
    pip install -r baseline_app\requirements.txt
)

echo.
echo Iniciando Guia Cierre de Minas...
echo Abre tu navegador en: http://localhost:8501
echo.
streamlit run baseline_app\app.py
pause
