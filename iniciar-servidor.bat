@echo off
title Servidor Lubens Farnesio 3D
echo ==============================================
echo  Iniciando servidor para Lubens Farnesio 3D
echo  URL: http://localhost:8000
echo ==============================================
echo.
"%LOCALAPPDATA%\Programs\nodejs\node.exe" server.js
if %ERRORLEVEL% NEQ 0 (
    node server.js
)
pause
