# Frequencia_zap 📝🚀
Modular application for school attendance automation, integrated with the SIAP portal and WhatsApp (via Evolution API).

---

## 🇺🇸 English Version

### 🌟 Key Features
- **SIAP Miner**: Fully automated web scraper for the SIAP portal (Goiás State). Handles login, CAPTCHA bypass, and data extraction from all teacher-filled classes of the day.
- **Smart Data Hub**: Integrates students' attendance from multiple sources (API, XML, XLSX, and SIAP) into a local SQLite database.
- **WhatsApp Integration**: Sends automated missing student notifications to parents using Evolution API with reliable message delivery.
- **Local Privacy**: Database, contact info, and logs are kept locally to ensure student data privacy and security.
- **Automated Cleanup**: The system maintains 15 days of historical data, automatically cleaning older records to keep the database lightweight.
- **Security First**: Audited with Bandit and protected against SQL Injection and XXE. No hardcoded secrets.

### 📂 Structure
- `app.py`: Streamlit-based Web Interface for data visualization, review, and manual triggers.
- `backend_processor/`: 
    - `siap_scraper.py`: The heart of the SIAP automation.
    - `db_importer.py`: Smart importer for physical school files.
- `database/`: `db_handler.py` manages local SQLite persistence.
- `core/`: Business logic, message formatting, and data cross-referencing.
- `services/`: API connectors for WhatsApp (Evolution) and School services.
- `launcher.py`: Orchestrator that starts Docker (API) and the Streamlit app together.
- `debug_html/`: Folder containing logs of the scraped SIAP pages for transparency.

### ⚙️ Quick Start (Windows)
1. **Initial Setup**: Run `CONFIGURAR_SISTEMA.bat` to create the virtual environment and install dependencies.
2. **Environment**: Create a `.env` file with your credentials (SIAP, Evolution API, Admin Password).
3. **Launch**: Run `INICIAR_FREQUENCIA_ZAP.bat` to start all services (Docker + Web UI).

---

## 🇧🇷 Versão em Português

### 🌟 Funcionalidades Principais
- **Minerador SIAP**: Scraper totalmente automatizado para o portal SIAP (Goiás). Realiza login, bypass de CAPTCHA e extração de faltas de todas as turmas do dia.
- **Hub de Dados Inteligente**: Cruza faltas de diversas fontes (API, XML, XLSX e SIAP) com o banco de dados físico de contatos.
- **Integração WhatsApp**: Disparo automático de notificações para os responsáveis via Evolution API.
- **Privacidade Local**: Banco de dados, contatos e logs são mantidos localmente, garantindo a segurança dos dados dos alunos.
- **Limpeza Automática**: Mantém 15 dias de histórico, removendo registros antigos para manter o sistema sempre rápido.
- **Segurança**: Auditado com Bandit e protegido contra SQL Injection e XXE. Sem senhas expostas no código.

### 📂 Estrutura do Projeto
- `app.py`: Interface Web (Streamlit) para visualização, revisão e disparo manual.
- `backend_processor/`: 
    - `siap_scraper.py`: O coração da automação com o portal SIAP.
    - `db_importer.py`: Importação inteligente de planilhas e XMLs escolares.
- `database/`: `db_handler.py` gerencia a persistência SQLite local.
- `core/`: Lógica de negócios, formatação de mensagens e cruzamento de dados.
- `launcher.py`: Orquestrador que liga o Docker (API) e o Streamlit simultaneamente.
- `debug_html/`: Pasta com os registros das páginas mineradas do SIAP para conferência.

### ⚙️ Como Iniciar (Windows)
1. **Configuração Inicial**: Execute `CONFIGURAR_SISTEMA.bat` para criar o ambiente virtual e instalar as bibliotecas.
2. **Ambiente**: Crie um arquivo `.env` com suas credenciais (SIAP, Evolution API, Senha Adm).
3. **Execução**: Use o `INICIAR_FREQUENCIA_ZAP.bat` para abrir todo o sistema com um clique (Docker + Interface Web).

---

## 🔒 Security
Operation is strictly local. All external calls (WhatsApp/SIAP) are made over secure sessions with timeouts. For a production-ready security audit, use `python -m bandit -r . -x .venv`.

## 📜 Logs
Operational logs are available at `logs/app.log`.