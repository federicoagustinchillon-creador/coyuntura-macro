@echo off
setlocal
cd /d "%~dp0"
title Dashboard Coyuntura Macro

echo Instalando dependencias (solo tarda la primera vez)...
python -m pip install -q -r dashboard\requirements.txt

echo.
echo Iniciando servidor en http://127.0.0.1:8420 ...
echo (dejar esta ventana abierta mientras uses el dashboard; cerrarla lo apaga)
echo.

start "" cmd /c "timeout /t 2 >nul && start http://127.0.0.1:8420"
python -m uvicorn dashboard.api:app --port 8420
