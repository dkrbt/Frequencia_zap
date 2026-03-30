import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def process_attendance(self, attendance_data):
        """
        Processa dados de presença usando a API e cruzando com o banco de dados físico (alunos_contatos).
        :param attendance_data: Dados JSON da API (que contém matricula/student_id)
        :return: DataFrame com alunos que faltaram e dados dos responsáveis
        """
        try:
            if not attendance_data:
                logger.warning("Dados de presença vazios ou inválidos.")
                return pd.DataFrame()

            # Converter para df e filtrar faltas
            df = pd.DataFrame(attendance_data)
            
            # Buscar nome da coluna de identificação (geralmente student_id ou matricula)
            id_col = 'matricula' if 'matricula' in df.columns else 'student_id'
            if id_col not in df.columns and 'aluno_id' in df.columns:
                id_col = 'aluno_id'
                
            if id_col not in df.columns:
                logger.error(f"Coluna de identificador do aluno ausente no retorno da API.")
                return pd.DataFrame()

            # Filtrar por status ausente
            status_col = 'status'
            if status_col not in df.columns:
                logger.error("Coluna 'status' não encontrada no retorno da API.")
                return pd.DataFrame()

            # Normalizar absenses
            absences = df[df[status_col].astype(str).str.lower().isin(['absent', 'ausente'])].copy()

            if absences.empty:
                logger.info("Nenhuma falta detectada.")
                return pd.DataFrame()

            # Cruzamento de Dados: Buscar cada estudante no nosso SQLite para recuperar NOME e TELEFONE
            enriched_records = []
            for _, row in absences.iterrows():
                matricula = str(row[id_col])
                student_info = self.db_handler.get_student_info(matricula)
                
                if student_info:
                    nome, tel_resp, tel_cel = student_info
                    
                    phone = tel_resp if tel_resp else tel_cel
                    if not phone:
                        logger.warning(f"Aluno(a) {nome} ({matricula}) faltou, mas não tem telefone cadastrado.")
                        continue
                    
                    data_hoje = datetime.now().strftime('%d/%m/%Y')
                    NUM_COORD_CEDOM = "556198931247"
                    nome_aluno = nome

                    mensagem = (
                        f"Prezado(a) responsável pelo(a) {nome_aluno}, "
                        f"estamos entrando em contato para avisar que hoje, {data_hoje}, "
                        f"ele(a) não veio à unidade de ensino. Favor entrar em contato com a coordenação: {NUM_COORD_CEDOM}."
                    )
                        
                    enriched_records.append({
                        'student_name': nome,
                        'guardian_phone': phone,
                        'message': mensagem
                    })
                else:
                    logger.warning(f"Falta (mat {matricula}) sem dados no banco físico XML/XLSX. Ignore.")

            if not enriched_records:
                logger.info("Falta detectada pela API mas nenhum correspondente achado no DB.")
                return pd.DataFrame()
                
            result = pd.DataFrame(enriched_records)
            logger.info(f"{len(result)} faltas casadas localmente processadas.")
            return result
            
        except KeyError as e:
            logger.error(f"Coluna esperada não encontrada nos dados: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Erro inesperado no Processor: {e}")
            return pd.DataFrame()