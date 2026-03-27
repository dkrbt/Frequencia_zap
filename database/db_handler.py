import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)

class DBHandler:
    def __init__(self):
        self.db_path = DB_PATH
        self._create_tables()

    def _create_tables(self):
        """
        Cria as tabelas do sistema se não existirem.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_name TEXT NOT NULL,
                        guardian_phone TEXT NOT NULL,
                        date_sent TEXT NOT NULL,
                        UNIQUE(student_name, guardian_phone, date_sent)
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alunos_contatos (
                        matricula TEXT PRIMARY KEY,
                        nome TEXT,
                        nascimento TEXT,
                        telefone_responsavel TEXT,
                        telefone_celular TEXT,
                        turno TEXT,
                        turma TEXT
                    )
                ''')
                logger.info("Tabelas do banco de dados criadas/verificadas.")
        except sqlite3.Error as e:
            logger.error(f"Erro ao criar tabelas: {e}")

    def check_sent_today(self, student_name, guardian_phone, today_date):
        """
        Verifica se a notificação já foi enviada hoje.
        :param student_name: Nome do aluno
        :param guardian_phone: Telefone do responsável
        :param today_date: Data no formato YYYY-MM-DD
        :return: True se já enviada, False caso contrário
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM notifications
                    WHERE student_name = ? AND guardian_phone = ? AND date_sent = ?
                ''', (student_name, guardian_phone, today_date))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Erro ao verificar envio: {e}")
            return False

    def log_sent(self, student_name, guardian_phone, today_date):
        """
        Registra o envio da notificação.
        :param student_name: Nome do aluno
        :param guardian_phone: Telefone do responsável
        :param today_date: Data no formato YYYY-MM-DD
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR IGNORE INTO notifications (student_name, guardian_phone, date_sent)
                    VALUES (?, ?, ?)
                ''', (student_name, guardian_phone, today_date))
                logger.info(f"Notificação registrada para {student_name}.")
        except sqlite3.Error as e:
            logger.error(f"Erro ao registrar envio: {e}")

    def upsert_students(self, data_list):
        """
        Salva ou atualiza a base de alunos em batch prevenindo injeção SQL.
        :param data_list: Lista de tuplas com os dados do aluno.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany('''
                    INSERT OR REPLACE INTO alunos_contatos (
                        matricula, nome, nascimento, telefone_responsavel, 
                        telefone_celular, turno, turma
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', data_list)
                logger.info(f"{len(data_list)} registros de alunos salvos/atualizados via UPSERT.")
        except sqlite3.Error as e:
            logger.error(f"Erro ao inserir lote de alunos: {e}")

    def get_student_info(self, matricula):
        """
        Busca telefone e nome do responsável/aluno via matrícula.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT nome, telefone_responsavel, telefone_celular 
                    FROM alunos_contatos WHERE matricula = ?
                ''', (matricula,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar aluno por matricula: {e}")
            return None