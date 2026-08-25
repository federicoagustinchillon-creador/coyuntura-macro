@echo off
REM =================================================================
REM EJECUTOR AUTOMATICO DEL PIPELINE MAESTRO DE COYUNTURA MACRO
REM Autor: Federico Agustin Chillon (FCE UNCUYO / OERU)
REM =================================================================

echo =================================================================
echo [INICIO] EJECUTANDO PIPELINE MAESTRO DESATENDIDO
echo =================================================================

cd /d "%~dp0\.."

python pipeline_coyuntura_master.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =================================================================
    echo [EXITO] Pipeline completado y sincronizado con Google Drive.
    echo =================================================================
) else (
    echo.
    echo =================================================================
    echo [ERROR] Fallo en la ejecucion del pipeline. Codigo: %ERRORLEVEL%
    echo =================================================================
)

exit /b %ERRORLEVEL%
