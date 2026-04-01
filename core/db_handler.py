import sqlite3
import logging
from datetime import datetime, timedelta
from config import DB_PATH

logger = logging.getLogger(__name__)

class DBHandler:
    def __init__(self):
        self.db_path = DB_PATH
        self._create_tables()
        self.limpar_registros_antigos() # Limpeza ao inicializar o sistema

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
                        time_sent TEXT NOT NULL,
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
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS registro_faltas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        matricula TEXT NOT NULL,
                        data_falta DATE NOT NULL,
                        UNIQUE(matricula, data_falta)
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
                    INSERT OR IGNORE INTO notifications (student_name, guardian_phone, date_sent, time_sent)
                    VALUES (?, ?, ?, ?)
                ''', (student_name, guardian_phone, today_date, datetime.now().strftime('%H:%M:%S')))
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
                    SELECT nome, telefone_responsavel, telefone_celular, turma 
                    FROM alunos_contatos WHERE matricula = ?
                ''', (matricula,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar aluno por matricula: {e}")
            return None

    def salvar_faltas_do_dia(self, lista_matriculas, data_hoje):
        """
        Salva o conjunto de matrículas que faltaram hoje na tabela registro_faltas.
        :param lista_matriculas: Lista de strings (matrículas)
        :param data_hoje: String data no formato YYYY-MM-DD
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                data_tuples = [(str(m), data_hoje) for m in lista_matriculas]
                conn.executemany('''
                    INSERT OR IGNORE INTO registro_faltas (matricula, data_falta)
                    VALUES (?, ?)
                ''', data_tuples)
                logger.info(f"{len(data_tuples)} faltas processadas e salvas no banco ({data_hoje}).")
        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar faltas do dia: {e}")

    def buscar_alunos_para_disparo(self, data_hoje):
        """
        Gera o conjunto completo de dados (JOIN) para o disparo das mensagens,
        filtrando apenas aqueles que ainda NÃO receberam notificação hoje.
        :param data_hoje: Data no formato YYYY-MM-DD
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # A query agora verifica na tabela 'notifications' para evitar duplicidade no FRONT-END
                cursor.execute('''
                    SELECT 
                        ac.matricula, 
                        ac.nome as nome_aluno, 
                        ac.turma, 
                        COALESCE(NULLIF(ac.telefone_responsavel, ''), ac.telefone_celular) as telefone_responsavel
                    FROM registro_faltas rf
                    INNER JOIN alunos_contatos ac ON rf.matricula = ac.matricula
                    WHERE rf.data_falta = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM notifications n
                        WHERE n.student_name = ac.nome 
                        AND n.guardian_phone = COALESCE(NULLIF(ac.telefone_responsavel, ''), ac.telefone_celular)
                        AND n.date_sent = rf.data_falta
                    )
                ''', (data_hoje,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar dados para disparo: {e}")
            return []

    def limpar_registros_antigos(self, dias=15):
        """
        Remove registros da tabela registro_faltas mais antigos que o limite de dias.
        Mantém o banco de dados leve e evita crescimento infinito.
        """
        try:
            # Calcula a data limite (hoje - 15 dias)
            limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM registro_faltas WHERE data_falta < ?', (limite,))
                if cursor.rowcount > 0:
                    logger.info(f"🧹 Faxina no Banco: {cursor.rowcount} registros de faltas antigos (antes de {limite}) foram removidos.")
        except sqlite3.Error as e:
            logger.error(f"❌ Erro ao realizar limpeza de registros antigos: {e}")