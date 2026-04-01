@echo off
setlocal
cd /d "%~dp0"
title DIAGNOSTICO DE HERANCA DE DADOS - MAMAE CORUJA
color 0E

echo ======================================================
echo    DIAGNOSTICO DE VARIAVEIS DE AMBIENTE (.ENV)
echo ======================================================
echo.

:: 1. Verificar existencia do arquivo
if not exist ".env" (
    echo [ERRO] O arquivo .env nao foi encontrado na raiz do projeto!
    echo Local verificado: %cd%\.env
    pause
    exit /b
)

:: 2. Conferir conteudo mascarado (Seguranca)
echo [*] Conteudo detectado no .env (Mascarado):
echo ------------------------------------------------------
for /f "tokens=1,2 delims==" %%a in (.env) do (
    set "line=%%b"
    if "%%b" == "" (
        echo %%a
    ) else (
        echo %%a=********
    )
)
echo ------------------------------------------------------
echo.

:: 3. Verificar o que o Docker Compose esta carregando na memoria
echo [*] Simulando carregamento do Docker Compose (docker-compose config):
echo ------------------------------------------------------
docker-compose config
echo ------------------------------------------------------
echo.

echo [DICA] Se os valores acima estiverem vazios ou errados, 
echo a heranca de dados entre o Instalador e o Docker falhou.
echo.
pause
