import os
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Configurações da API da escola
SCHOOL_API_URL = os.getenv('SCHOOL_API_URL')
SCHOOL_API_TOKEN = os.getenv('SCHOOL_API_TOKEN')

# Configurações da Evolution API (WhatsApp)
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL')
EVOLUTION_API_TOKEN = os.getenv('EVOLUTION_API_TOKEN')
EVOLUTION_INSTANCE = os.getenv('EVOLUTION_INSTANCE')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Contato da Coordenação para incluir nas mensagens
COORD_PHONE_NUMBER = os.getenv('COORD_PHONE_NUMBER')

# Validação de Segurança: Impede o sistema de subir sem senha mestre
if not ADMIN_PASSWORD:
    logging.critical("🚨 VARIÁVEL DE AMBIENTE 'ADMIN_PASSWORD' NÃO DETECTADA. O SISTEMA NÃO IRÁ INICIAR POR SEGURANÇA.")
    raise RuntimeError("Erro de Segurança: ADMIN_PASSWORD ausente.")

# Configurações do banco de dados
DB_PATH = os.getenv('DB_PATH', 'database/escola.db')

# Configurações de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

# Configurar logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
if os.path.dirname(DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)