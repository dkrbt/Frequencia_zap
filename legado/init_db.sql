-- Tabelas do sistema convertidas para o padrão SQLite
CREATE TABLE IF NOT EXISTS responsaveis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    responsavel_id INTEGER REFERENCES responsaveis(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS logs_envio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER REFERENCES alunos(id),
    data_envio TEXT NOT NULL,
    UNIQUE(aluno_id, data_envio)
);

-- NOVA TABELA: Importação de Dados dos Alunos via CSV
CREATE TABLE IF NOT EXISTS alunos_contatos (
    matricula TEXT PRIMARY KEY,
    ponto_id TEXT UNIQUE,
    nome TEXT,
    nascimento TEXT,
    turno TEXT,
    turma TEXT,
    telefone_responsavel TEXT,
    celular TEXT
);