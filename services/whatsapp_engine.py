import requests
import logging
from config import EVOLUTION_API_URL, EVOLUTION_API_TOKEN, EVOLUTION_INSTANCE

logger = logging.getLogger(__name__)

class WhatsAppEngine:
    def __init__(self):
        # A URL base já cuidará de montar a rota correta (removendo barras duplas se houver)
        self.base_url = EVOLUTION_API_URL.rstrip('/')
        self.instance = EVOLUTION_INSTANCE
        
        # Endpoint padrão da Evolution API para envio de texto
        self.url = f"{self.base_url}/message/sendText/{self.instance}"
        self.token = EVOLUTION_API_TOKEN
        
        self.headers = {
            'apikey': self.token,
            'Content-Type': 'application/json'
        }

    def _normalize_number(self, phone):
        """Limpa caracteres, espaços, hifens e obriga a presença do DDI brasileiro (+55)"""
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        
        # Se for formato local, adiciona o DDI do Brasil (55)
        if len(clean_phone) in [10, 11]:
            clean_phone = f"55{clean_phone}"
            
        return clean_phone

    def send_notification(self, phone_number, message):
        """
        Envia a notificação via WhatsApp usando Evolution API, formatando
        o payload corretamente (texto na raiz) e implementando o fallback do 9º dígito.
        """
        raw_number = self._normalize_number(phone_number)
        
        # PAYLOAD EXATO da Evolution V2 - Note que a chave "text" agora está isolada
        payload = {
            "number": raw_number,
            "text": message,
            "delay": 1200, 
            "presence": "composing",
            "linkPreview": False
        }

        try:
            # Primeira Tentativa Padrão
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            logger.info(f"✅ Disparo primário enviado com sucesso para: {raw_number}")

            # Sistema Gêmeo de Proteção (Double-Tap Backup) 
            # Verifica se o número despachado possui o 9º dígito (tamanho 13 e índice 4 sendo o '9')
            # Exemplo: 55619XXXX
            if len(raw_number) == 13 and raw_number[4] == '9': 
                # Corta fora somente o "9" pós-DDD
                alternative_number = raw_number[:4] + raw_number[5:] 
                payload["number"] = alternative_number
                
                # Executa o segundo tiro silenciosamente
                requests.post(self.url, headers=self.headers, json=payload, timeout=30)
                logger.info(f"✅ Disparo de Backup (formato antigo de 8 dígitos) enviado para: {alternative_number}")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro de HTTP ao enviar notificação para {phone_number}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro genérico na WhatsAppEngine: {e}")
            return False