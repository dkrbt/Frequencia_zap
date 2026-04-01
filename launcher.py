import os
import sys
import subprocess
import time
import webbrowser
import logging

# 1. Obter o diretório base absoluto do projeto dinamicamente
base_dir = os.path.dirname(os.path.abspath(__file__))

# Configurações de caminhos absolutos
venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
app_script = os.path.join(base_dir, "app.py")
env_file = os.path.join(base_dir, ".env")

def log_section(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def verificar_configuracao():
    """
    Verifica se os arquivos essenciais e o ambiente virtual estão prontos.
    """
    log_section("CHECAGEM DE INTEGRIDADE")
    
    # 1. Verificar .env
    if not os.path.exists(env_file):
        print("[ERRO] Arquivo de configuração .env não encontrado!")
        print("Causa provável: O instalador não finalizou a etapa de configuração.")
        return False
    
    # 2. Verificar ADMIN_PASSWORD no .env
    with open(env_file, 'r') as f:
        content = f.read()
        if "ADMIN_PASSWORD=" not in content or "ADMIN_PASSWORD=" + "\n" in content:
            print("[ERRO] Variável ADMIN_PASSWORD está ausente ou vazia no seu .env!")
            print("Causa provável: Você não definiu a senha durante a instalação.")
            return False
            
    # 3. Verificar .venv e interpretador
    if not os.path.exists(venv_python):
        print(f"[ERRO] Ambiente virtual não encontrado em: {venv_python}")
        print("Causa provável: O 'instalar.bat' falhou ou foi interrompido.")
        return False
        
    # 4. Verificar se o Streamlit está instalado no venv
    try:
        subprocess.run([venv_python, "-c", "import streamlit"], check=True, capture_output=True)
        print("[OK] Ambiente Python verificado.")
    except subprocess.CalledProcessError:
        print("[ERRO] A biblioteca 'streamlit' não foi instalada no seu ambiente virtual.")
        print("Sugestão: Tente rodar o 'instalar.bat' como administrador e verifique a sua internet.")
        return False
        
    return True

def iniciar_docker():
    """Inicia os serviços do Docker."""
    log_section("INICIANDO INFRAESTRUTURA (DOCKER)")
    
    try:
        # Executa o docker-compose up -d
        result = subprocess.run(
            ['docker-compose', 'up', '-d'], 
            cwd=base_dir, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("[OK] Banco de Dados e WhatsApp API ativos.")
        else:
            print(f"[!] Aviso Docker: {result.stderr}")
            
    except FileNotFoundError:
        print("[ERRO] Docker Desktop não detectado no sistema.")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

def iniciar_streamlit():
    """Inicia a interface do Streamlit."""
    log_section("LANÇANDO INTERFACE MAMÃE CORUJA")
    
    try:
        # Comando mais robusto para rodar o Streamlit
        cmd = [
            venv_python, "-m", "streamlit", "run", app_script, 
            "--server.port", "8501", 
            "--server.address", "0.0.0.0", 
            "--server.headless", "true"
        ]
        
        print(f"[*] Acompanhe em: http://localhost:8501")
        
        # Abre o navegador
        time.sleep(3)
        webbrowser.open("http://localhost:8501")

        # Inicia o processo
        process = subprocess.Popen(
            cmd, 
            cwd=base_dir,
            stdout=None, # Herda stdout para mostrar erro no console
            stderr=None,
            text=True
        )
        
        print("\n--- SISTEMA ONLINE (Logs abaixo) ---")
        process.wait()
            
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Falha ao lançar Streamlit: {e}")
        input("\nPressione Enter para fechar...")

if __name__ == "__main__":
    if verificar_configuracao():
        iniciar_docker()
        iniciar_streamlit()
    else:
        print("\n[FALHA] O sistema não pôde ser iniciado por problemas de configuração.")
        input("\nPressione Enter para sair e tente reinstalar...")
        sys.exit(1)
