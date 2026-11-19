@echo off
title Preciario de Mantenimientos Toyota
echo ====================================================
echo   Iniciando Simulador de Preciario Toyota
echo ====================================================
echo.

set PYTHON_EXE=

if exist "%APPDATA%\uv\python\cpython-3.14.5-windows-x86_64-none\python.exe" (
    set PYTHON_EXE=%APPDATA%\uv\python\cpython-3.14.5-windows-x86_64-none\python.exe
)
if "%PYTHON_EXE%"=="" (
    if exist "%USERPROFILE%\.local\bin\python3.14.exe" (
        set PYTHON_EXE=%USERPROFILE%\.local\bin\python3.14.exe
    )
)
if "%PYTHON_EXE%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_EXE=python
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] No se encontro un interprete de Python compatible.
    pause
    exit /b 1
)

echo Usando Python: %PYTHON_EXE%
echo Abriendo la aplicacion en tu navegador...
echo.
echo Presiona Ctrl + C en esta ventana para cerrar la aplicacion.
echo ====================================================
echo.

set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
"%PYTHON_EXE%" -m streamlit run app_preciario.py --browser.gatherUsageStats false
pause
