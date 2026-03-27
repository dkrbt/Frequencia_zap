import requests
import logging
from config import SCHOOL_API_URL, SCHOOL_API_TOKEN

logger = logging.getLogger(__name__)

class SchoolAPI:
    def __init__(self):
        self.url = SCHOOL_API_URL
        self.token = SCHOOL_API_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def get_attendance_data(self, date=None):
        """
        Busca dados de presença da API da escola.
        :param date: Data opcional no formato YYYY-MM-DD
        :return: Dados de presença em formato JSON ou None se erro
        """
        try:
            params = {'date': date} if date else {}
            response = requests.get(self.url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            logger.info("Dados de presença obtidos com sucesso.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar dados da API da escola: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado na SchoolAPI: {e}")
            return None