@echo off
setlocal
title MAMAE CORUJA - INICIAR (ORQUESTRADOR)
color 0B

:: ===================================================
:: 1. ELEVACAO DE PRIVILEGIOS (UAC)
:: ===================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando privilegios de administrador...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:: Garante que o contexto da execucao seja a pasta onde este arquivo reside
cd /d "%~dp0"
echo [*] Pasta do sistema: %cd%
echo.

:: ===================================================
:: 2. VERIFICACAO DE INSTALACAO (Flag File)
:: ===================================================
if not exist "database\.instalado" (
    echo [!] Primeira execucao detectada. Iniciando configuracao...
    echo.
    call instalar.bat
    if not exist "database" mkdir database
    echo 1 > "database\.instalado"
)

:: ===================================================
:: 3. EXECUCAO DOS SERVICOS - BLINDAGEM NIVEL 3
:: ===================================================
echo ======================================================
echo    LANÇANDO SERVICOS MAMÃE CORUJA
echo ======================================================
echo.

:: A. Subir infraestrutura (Reset e Recriacao Forcada)
echo [*] Parando servicos antigos para limpar o cache...
docker-compose --env-file .env down --remove-orphans >nul 2>&1

echo [*] Forcando recriacao com o novo .env e autenticacao...
docker-compose --env-file .env up -d --force-recreate
if %errorlevel% neq 0 (
    echo [!] Aviso: Nao foi possivel iniciar os containers Docker.
    echo Verifique se o Docker Desktop esta aberto.
)

:: B. Iniciar Interface Grafica (Streamlit)
echo [*] Abrindo painel administrativo no seu navegador...
echo [*] Caso nao abra automaticamente, acesse: http://localhost:8501
echo.

:: Abre o navegador padrao (opcional start)
start http://localhost:8501

:: Inicia o Streamlit usando o interpretador absoluto do venv
"%~dp0.venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0

echo.
echo ======================================================
echo    SISTEMA ENCERRADO OU INTERROMPIDO.
echo ======================================================
pause
exit /b 0
