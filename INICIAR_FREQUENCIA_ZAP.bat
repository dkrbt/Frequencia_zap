@echo off
setlocal
title HUB - Frequencia_zap
echo ======================================================
echo    INICIALIZADOR DO FREQUENCIA_ZAP
echo ======================================================
echo.

cd /d "%~dp0"

:: 1. Verificar se o Docker Desktop está rodando
docker stats --no-stream >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] O Docker Desktop nao está rodando! Abra o Docker Desktop e tente novamente.
    pause
    exit /b
)

:: 2. Verificar se o .venv está pronto
if not exist ".venv" (
    echo [ERRO] O sistema nao foi configurado! Execute primeiro o 'CONFIGURAR_SISTEMA.bat'.
    pause
    exit /b
)

:: 3. Rodar o launcher (que gerencia o docker compose e o streamlit)
echo [*] Iniciando servicos (aguarde a abertura no navegador)...
.venv\Scripts\python.exe launcher.py

echo.
echo ======================================================
echo    FREQUENCIA_ZAP FINALIZADO COM SUCESSO!
echo ======================================================
pause
