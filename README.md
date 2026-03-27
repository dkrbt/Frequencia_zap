# Frequencia_zap
Aplicação modular para automação de presença escolar.

## Estrutura
- `app.py`: Interface gráfica interativa (Streamlit) para upload de arquivos XML e Excel contendo a frequência dos alunos e tratamento da LGPD.
- `main.py`: Orquestrador principal da automação, que varre o banco local e dispara as mensagens.
- `services/`: Módulos para integração com APIs externas (escola e WhatsApp/Evolution API).
- `core/`: Lógica de processamento com Pandas para tratamento de dados.
- `database/`: Gerenciamento do banco SQLite (`DBHandler`) integrado e seguro.
- `backend_processor/`: Ferramentas robustas para importação inteligente (db_importer) lendo de arquivos XLS/XML.
- `config.py`: Configurações via variáveis de ambiente.
- `docker-compose.yml`: Script de containerização do Evolution API e PostgreSQL para estabilidade do disparo do WhatsApp.
- `legado/`: Diretório deversionamento antigo (scripts JS velhos, códigos de conexão obsoletos). Mantido para histórico referencial e testes isolados.

## Instalação
1. Crie seu ambiente virtual `python -m venv .venv` e ative-o.
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure os contêineres e banco: `docker-compose up -d`
4. Configure as variáveis de ambiente em um arquivo `.env` com base no `.env.example`.
5. Execute a interface web: `streamlit run app.py`

## Logs
Logs das operações de background e integrações são salvos em `logs/app.log` por padrão.