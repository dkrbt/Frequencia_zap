import subprocess
import time
import webbrowser
import os
import sys

# Configurações de Caminhos (Relativos ao local do executável)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PYTHON_PATH = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
STREAMLIT_PATH = os.path.join(BASE_DIR, "app.py")

def log(msg):
    print(f"[*] {msg}")

def start_services():
    print("=" * 50)
    print(" INICIALIZADOR FREQUENCIA_ZAP ".center(50))
    print("=" * 50)

    # 1. Iniciar Docker
    log("Ligando Docker (Evolution API + Postgres)...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True, cwd=BASE_DIR)
        log("Docker [OK]")
    except Exception as e:
        log(f"ERRO ao ligar Docker: {e}")
        input("\nPressione Enter para sair...")
        return

    # 2. Aguardar API responder (Health Check simples)
    log("Aguardando inicialização da API (pode levar alguns segundos)...")
    time.sleep(10) # Pausa inicial

    # 3. Abrir Páginas no Navegador
    log("Abrindo painéis no navegador...")
    webbrowser.open("http://localhost:8501") # Painel Streamlit
    webbrowser.open("http://localhost:8080/dashboard") # Dashboard Evolution API

    # 4. Iniciar Streamlit (Este comando manterá o terminal aberto)
    log("Lançando Interface Web do Frequencia_zap...")
    cmd = [PYTHON_PATH, "-m", "streamlit", "run", STREAMLIT_PATH, "--server.address", "0.0.0.0"]
    
    try:
        # Usamos subprocess.run para manter o terminal preso enquanto o streamlit roda
        subprocess.run(cmd, cwd=BASE_DIR)
    except KeyboardInterrupt:
        log("Desligando por interrupção do usuário (Ctrl+C)...")
    except Exception as e:
        log(f"ERRO ao iniciar Streamlit: {e}")
        input("\nPressione Enter para sair...")

if __name__ == "__main__":
    start_services()
