import requests
import time
import os
import sys
import logging
from dotenv import load_dotenv

# Configuração de Logs básica
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

def auto_setup():
    # Carrega dados do .env (Criados pelo Inno Setup)
    url_base = os.getenv("EVOLUTION_API_URL", "http://localhost:8081").rstrip('/')
    token_global = os.getenv("EVOLUTION_API_TOKEN")
    instance_token = os.getenv("EVOLUTION_INSTANCE_TOKEN", token_global)
    instance_name = os.getenv("EVOLUTION_INSTANCE", "whatsapp_bot")

    if not token_global:
        logger.error("❌ Erro: EVOLUTION_API_TOKEN não encontrado no seu arquivo .env")
        return

    logger.info(f"[*] Iniciando auto-configuração da Evolution API para: '{instance_name}'...")
    logger.info(f"[*] Destino: {url_base}")

    # 1. Loop de Espera: Aguarda a API responder (Até 2 minutos)
    api_ready = False
    for i in range(24): # 24 x 5s = 120s
        try:
            # Query simples para ver se a API está online
            res = requests.get(f"{url_base}/instance/fetchInstances", headers={"apikey": token_global}, timeout=5)
            if res.status_code in [200, 401]: # 401 também significa que a API respondeu (embora sem autorização se o token estiver errado)
                logger.info("✅ Evolution API detectada e operando!")
                api_ready = True
                break
        except Exception as e:
            logger.info(f"[...] Aguardando Docker API subir (Tentativa {i+1}/24)...")
            time.sleep(5)
    
    if not api_ready:
        logger.error("❌ FALHA: A API não respondeu a tempo. Verifique se o Docker Desktop está rodando.")
        return

    # 2. Configurar a Instância
    try:
        # Verifica se a instância já existe
        check_res = requests.get(f"{url_base}/instance/connectionState/{instance_name}", headers={"apikey": token_global}, timeout=10)
        
        if check_res.status_code == 200:
            logger.info(f"ℹ️ A instância '{instance_name}' já existe. Nenhuma ação necessária.")
        else:
            # Payload para criação automática (QRCode habilitado)
            payload = {
                "instanceName": instance_name,
                "token": instance_token, # <- AGORA USA O TOKEN ESPECIFICO
                "qrcode": True
            }
            create_res = requests.post(f"{url_base}/instance/create", headers={"apikey": token_global}, json=payload, timeout=20)
            
            if create_res.status_code == 201:
                logger.info(f"🚀 SUCESSO: Instância '{instance_name}' criada automaticamente pela instalação!")
                
                # Opcional: Configurar Webhooks ou comportamentos padrão aqui
                pass
            else:
                logger.warning(f"⚠️ Aviso: A API respondeu com status {create_res.status_code}. Talvez criação manual seja necessária.")
                print(create_res.text)

    except Exception as e:
        logger.error(f"❌ Erro ao tentar criar a instância: {e}")

if __name__ == "__main__":
    auto_setup()
