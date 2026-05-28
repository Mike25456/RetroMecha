@echo off
cd /d "%~dp0"
title RetroMecha Launcher

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3 run_retromecha.py
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        python run_retromecha.py
    ) else (
        echo [RetroMecha] No se encontro Python en este PC.
        echo Instala Python 3 o ejecuta desde una terminal donde python este disponible.
        pause
        exit /b 1
    )
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [RetroMecha] El lanzador termino con errores.
    pause
)
