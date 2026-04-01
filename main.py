import logging
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE
from services.school_api import SchoolAPI
from services.whatsapp_engine import WhatsAppEngine
from core.processor import Processor
from core.db_handler import DBHandler

logger = logging.getLogger(__name__)

def main():
    """
    Orquestrador principal do sistema de automação de presença.
    """
    try:
        # Inicializar componentes
        school_api = SchoolAPI()
        whatsapp_engine = WhatsAppEngine()
        db_handler = DBHandler()
        processor = Processor(db_handler)

        # Data atual
        today = datetime.now().strftime('%Y-%m-%d')

        # 1. Buscar dados de presença
        attendance_data = school_api.get_attendance_data(date=today)
        if not attendance_data:
            logger.error("Falha ao obter dados de presença. Encerrando.")
            return

        # 2. Processar faltas
        absences_df = processor.process_attendance(attendance_data)
        if absences_df.empty:
            logger.info("Nenhuma notificação a enviar.")
            return

        # 3. Enviar notificações, verificando duplicidade
        for _, row in absences_df.iterrows():
            student_name = row['student_name']
            guardian_phone = row['guardian_phone']
            message = row['message']

            if not db_handler.check_sent_today(student_name, guardian_phone, today):
                if whatsapp_engine.send_notification(guardian_phone, message):
                    db_handler.log_sent(student_name, guardian_phone, today)
                else:
                    logger.warning(f"Falha ao enviar para {guardian_phone}.")
            else:
                logger.info(f"Notificação já enviada hoje para {student_name}.")

        logger.info("Processo concluído com sucesso.")

    except Exception as e:
        logger.error(f"Erro crítico no main: {e}")

if __name__ == "__main__":
    main()