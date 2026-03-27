import os
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Configurações da API da escola
SCHOOL_API_URL = os.getenv('SCHOOL_API_URL', 'https://api.escola.com/presenca')
SCHOOL_API_TOKEN = os.getenv('SCHOOL_API_TOKEN', 'token_padrao')

# Configurações da Evolution API (WhatsApp)
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'https://api.evolution.com/send')
EVOLUTION_API_TOKEN = os.getenv('EVOLUTION_API_TOKEN', 'token_evolution')
EVOLUTION_INSTANCE = os.getenv('EVOLUTION_INSTANCE', 'instance_padrao')

# Configurações do banco de dados
DB_PATH = os.getenv('DB_PATH', 'database/escola.db')

# Configurações de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)