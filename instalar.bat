@echo off
setlocal enabledelayedexpansion
title MAMAE CORUJA - CONFIGURADOR
color 0A

:: Garante que o contexto da execucao seja o local deste script
cd /d "%~dp0"

echo ======================================================
echo    INSTALADOR DO SISTEMA MAMAE CORUJA
echo ======================================================
echo.

:: 1. Tentar detectar Python (Instala se nao houver)
echo [*] Verificando dependencias base (Python)...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Python nao detectado. Instalando via Winget...
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements --silent
    
    :: Busca o comando PY no PATH atualizado temporariamente ou caminhos padrao
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    if not exist "!PY_CMD!" set "PY_CMD=C:\Program Files\Python311\python.exe"
) else (
    set "PY_CMD=python"
)

:: 2. Criar Ambiente Virtual (.venv)
echo.
echo [*] Criando a bolha do ambiente virtual (.venv)...
"!PY_CMD!" -m venv .venv
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar o ambiente virtual! 
    echo Verifique sua instalacao do Python e tente novamente.
    pause
    exit /b 1
)

:: 3. Instalar Pip/Requirements usando o interpretador do venv para blindagem total
echo.
echo [*] Instalando bibliotecas do sistema (pode levar alguns minutos)...
set "VENV_PYTHON=%cd%\.venv\Scripts\python.exe"

:: Garante Pip atualizado no venv
"!VENV_PYTHON!" -m pip install --upgrade pip --quiet --default-timeout=100

:: Instala requirements.txt
"!VENV_PYTHON!" -m pip install -r requirements.txt --no-warn-script-location --default-timeout=100
if %errorlevel% neq 0 (
    echo.
    echo [ERRO CRITICO] Falha ao instalar dependencias do requirements.txt.
    echo [DICA] Verifique sua conexao com a internet e tente rodar novamente.
    echo.
    pause
    exit /b 1
)

:: 4. Verificacao de Integridade (Checkmate)
echo.
echo [*] Verificando integridade da instalacao (Streamlit)...
"!VENV_PYTHON!" -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Streamlit nao detectado. Reparando instalacao...
    "!VENV_PYTHON!" -m pip install streamlit --default-timeout=100
)

echo.
echo [OK] CONFIGURACAO DO AMBIENTE CONCLUIDA!
echo.
:: Devolve o controle para o chamar (iniciar.bat) síncronamente
exit /b 0