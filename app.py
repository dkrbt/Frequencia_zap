import streamlit as st
import pandas as pd
import os
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from backend_processor.db_importer import process_excel, process_xml, extract_data_for_db
from backend_processor.siap_scraper import login_siap, SIAPScraper
from database.db_handler import DBHandler
from core.processor import Processor
from services.school_api import SchoolAPI
from services.whatsapp_engine import WhatsAppEngine
from config import ADMIN_PASSWORD, EVOLUTION_API_URL, EVOLUTION_API_TOKEN, EVOLUTION_INSTANCE

# Configurações iniciais
st.set_page_config(page_title="Frequencia_zap - Hub", layout="wide", page_icon="📝")

# --- SISTEMA DE AUTENTICAÇÃO ---
def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔐 Acesso Restrito - CEDOM")
    placeholder = st.empty()
    
    with placeholder.form("login"):
        password = st.text_input("Digite a senha administrativa", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if password == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Senha inválida.")
    return False

if not check_password():
    st.stop()

# --- INICIALIZAÇÃO DE COMPONENTES ---
db_handler = DBHandler()
school_api = SchoolAPI()
whatsapp_engine = WhatsAppEngine()
processor = Processor(db_handler)

# --- FUNÇÕES DE STATUS ---
def get_evolution_status():
    try:
        url = f"{EVOLUTION_API_URL.rstrip('/')}/instance/connectionState/{EVOLUTION_INSTANCE}"
        headers = {"apikey": EVOLUTION_API_TOKEN}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            status = response.json().get("instance", {}).get("state", "UNKNOWN")
            return status
        return "DESCONECTADO"
    except:
        return "OFFLINE"

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🚀 Frequencia_zap")
st.sidebar.markdown(f"**Instância:** `{EVOLUTION_INSTANCE}`")


# Status do SIAP na Sidebar
if 'siap_session' in st.session_state and st.session_state['siap_session']:
    st.sidebar.success("🌐 SIAP: Conectado")
    if st.sidebar.button("🔌 Deslogar SIAP"):
        st.session_state['siap_session'] = None
        st.rerun()
else:
    st.sidebar.warning("🌐 SIAP: Desconectado")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menu Principal",
    ["📊 Dashboard & Status", "📥 Importar Alunos (XML/XLSX)", "🌐 Portal SIAP (Login)", "📲 Disparar Faltas", "📑 Histórico de Envios"]
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout Geral"):
    st.session_state["password_correct"] = False
    st.rerun()

# --- PÁGINA: DASHBOARD ---
if menu == "📊 Dashboard & Status":
    st.title("📊 Painel de Controle")
    
    col1, col2, col3 = st.columns(3)
    
    evo_status = get_evolution_status()
    
    with col1:
        st.metric("WhatsApp Status", evo_status.upper())
        if evo_status != "open":
            st.warning("⚠️ O WhatsApp não está conectado!")
    
    with col2:
        try:
            with sqlite3.connect(db_handler.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM alunos_contatos").fetchone()[0]
            st.metric("Alunos Cadastrados", count)
        except:
            st.metric("Alunos Cadastrados", "0")

    with col3:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with sqlite3.connect(db_handler.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM notifications WHERE date_sent = ?", (today,)).fetchone()[0]
            st.metric("Enviados Hoje", count)
        except:
            st.metric("Enviados Hoje", "0")

    st.markdown("---")
    st.subheader("⚙️ Configurações Atuais")
    st.code(f"URL API: {EVOLUTION_API_URL}\nInstância: {EVOLUTION_INSTANCE}", language="bash")

# --- PÁGINA: IMPORTAÇÃO ---
elif menu == "📥 Importar Alunos (XML/XLSX)":
    st.title("📥 Importação de Base de Alunos")
    st.write("Suba os arquivos XML ou Excel da escola para atualizar os telefones dos responsáveis.")
    
    uploaded_file = st.file_uploader("Selecione o arquivo", type=['xml', 'xlsx'])
    
    if uploaded_file:
        try:
            with st.spinner("Processando arquivo..."):
                if uploaded_file.name.lower().endswith('.xml'):
                    final_df = process_xml(uploaded_file)
                else:
                    final_df = process_excel(uploaded_file)
                
            st.subheader("📝 Revisão Manual")
            edited_df = st.data_editor(final_df, width="stretch", num_rows="dynamic")
            
            if st.button("💾 Gravar no Banco de Dados", type="primary"):
                data_list = extract_data_for_db(edited_df)
                if data_list:
                    db_handler.upsert_students(data_list)
                    st.success(f"✅ {len(data_list)} registros atualizados!")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# --- PÁGINA: PORTAL SIAP (LOGIN) ---
elif menu == "🌐 Portal SIAP (Login)":
    st.title("🌐 Acesso ao Portal SIAP")
    st.write("Entre com suas credenciais do SIAP para habilitar funções automáticas. **Nenhuma senha será salva.**")

    if 'siap_session' in st.session_state and st.session_state['siap_session']:
        st.success("✅ Você já está logado no SIAP!")
        if st.button("Tentar Novo Login"):
            st.session_state['siap_session'] = None
            st.rerun()
    else:
        with st.form("siap_login_form"):
            user_siap = st.text_input("Usuário (CPF)", placeholder="Apenas números")
            pass_siap = st.text_input("Senha do SIAP", type="password")
            submit_siap = st.form_submit_button("Realizar Login Automatizado", use_container_width=True)

            if submit_siap:
                if not user_siap or not pass_siap:
                    st.error("Preencha todos os campos.")
                else:
                    with st.spinner("Conectando ao SIAP e resolvendo CAPTCHA..."):
                        session = login_siap(user_siap, pass_siap)
                        if session:
                            st.session_state['siap_session'] = session
                            st.success("✅ Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Falha no login. Verifique seu usuário, senha ou se o portal está instável.")

# --- PÁGINA: DISPARAR FALTAS ---
elif menu == "📲 Disparar Faltas":
    st.title("📲 Gerenciador de Disparos")
    st.write("Verifique quem faltou hoje e confirme o envio da mensagem.")

    today_val = datetime.now().strftime('%Y-%m-%d')
    
    # 🔄 AUTO-LOAD: Se o estado está vazio, tenta carregar do banco de dados
    if 'absences_to_send' not in st.session_state:
        df_db = processor.carregar_e_formatar_faltas_do_banco(today_val)
        if not df_db.empty:
            st.session_state['absences_to_send'] = df_db
            st.session_state['today_date'] = today_val
            st.toast("⚡ Faltas já registradas hoje foram carregadas do banco!", icon="ℹ️")
    st.subheader("📡 Origem dos Dados")
    col_api, col_siap = st.columns(2)
    
    with col_api:
        if st.button("🔌 Buscar via API da Escola", use_container_width=True):
            with st.spinner("Consultando API da Escola..."):
                today = datetime.now().strftime('%Y-%m-%d')
                attendance_data = school_api.get_attendance_data(date=today)
                
                if not attendance_data:
                    st.error("Erro ao obter dados da API. Verifique a conexão.")
                else:
                    absences_df = processor.process_attendance(attendance_data)
                    if absences_df.empty:
                        st.success("✅ Nenhuma falta nova detectada pela API!")
                    else:
                        st.session_state['absences_to_send'] = absences_df
                        st.session_state['today_date'] = today
                        st.rerun()

    with col_siap:
        if st.button("⛏️ Minerador SIAP (Automatizado)", type="primary", use_container_width=True):
            if 'siap_session' not in st.session_state or not st.session_state['siap_session']:
                st.error("⚠️ Você não está logado no SIAP. Vá na aba 'Portal SIAP' primeiro.")
            else:
                with st.status("⛏️ Minerando dados no SIAP...", expanded=True) as status:
                    scraper = SIAPScraper()
                    scraper.session = st.session_state['siap_session']
                    
                    status.write("📡 Acessando página de frequência diária...")
                    soup, html_base = scraper.acessar_pagina_frequencia()
                    if not soup:
                        st.error("Falha ao acessar página de frequência.")
                    else:
                        turmas = scraper.extrair_turmas_preenchidas(soup)
                        if not turmas:
                            status.update(label="ℹ️ Nenhuma turma encontrada.", state="complete")
                            st.info("Nenhuma turma com chamada lançada foi encontrada no SIAP hoje.")
                        else:
                            all_faltas = []
                            for i, turma in enumerate(turmas):
                                status.write(f"📂 Abrindo turma: {turma['nome_turma']}...")
                                _, html_turma = scraper.abrir_turma_do_postback(turma, html_base)
                                if html_turma:
                                    faltas = scraper.extrair_faltas_da_turma(html_turma)
                                    all_faltas.extend(faltas)
                            
                            if all_faltas:
                                status.write("⚙️ Cruzando dados com a base de contatos...")
                                absences_df = processor.processar_faltas_e_gerar_mensagens(all_faltas)
                                st.session_state['absences_to_send'] = absences_df
                                st.session_state['today_date'] = datetime.now().strftime('%Y-%m-%d')
                                status.update(label="✅ Mineração Concluída!", state="complete")
                                st.rerun()
                            else:
                                status.update(label="✅ Finalizado sem faltas.", state="complete")
                                st.success("Mineração concluída. Nenhuma falta real detectada.")

    if 'absences_to_send' in st.session_state:
        df = st.session_state['absences_to_send'].reset_index(drop=True)
        st.subheader(f"📋 {len(df)} Alunos Faltosos")
        
        # Garantir limpeza para o editor
        df_display = df.copy()
        df_display.insert(0, "Enviar?", True)
        
        edited_selection = st.data_editor(
            df_display, 
            hide_index=True, 
            disabled=["student_name", "guardian_phone", "message", "matricula", "turma"],
            width="stretch",
            key="absence_editor"
        )
        
        if st.button("🚀 Confirmar e Enviar Agora", use_container_width=True):
            to_send = edited_selection[edited_selection["Enviar?"] == True]
            if to_send.empty:
                st.warning("Selecione pelo menos um aluno.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                
                for i, (_, row) in enumerate(to_send.iterrows()):
                    status_text.text(f"Enviando para {row['student_name']}...")
                    
                    if not db_handler.check_sent_today(row['student_name'], row['guardian_phone'], st.session_state['today_date']):
                        if whatsapp_engine.send_notification(row['guardian_phone'], row['message']):
                            db_handler.log_sent(row['student_name'], row['guardian_phone'], st.session_state['today_date'])
                            success_count += 1
                    
                    progress_bar.progress((i + 1) / len(to_send))
                
                status_text.empty()  # Limpa o texto "Enviando para..."
                st.success(f"🎊 Finalizado! {success_count} mensagens enviadas.")
                
                # Remove a tabela da memória
                del st.session_state['absences_to_send']
                
                # Dá um pequeno tempo e atualiza a tela
                import time
                time.sleep(2.5)
                st.rerun()

# --- PÁGINA: HISTÓRICO ---
elif menu == "📑 Histórico de Envios":
    st.title("📑 Histórico Recente")
    try:
        with sqlite3.connect(db_handler.db_path) as conn:
            hist_df = pd.read_sql_query(
                "SELECT student_name as Aluno, guardian_phone as Telefone, date_sent as Data FROM notifications ORDER BY id DESC LIMIT 100", 
                conn
            )
        if hist_df.empty:
            st.info("O histórico está vazio.")
        else:
            st.dataframe(hist_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# Floating button to open Evolution manager
st.markdown(
    """
    <style>
    .floating-btn {
        position: fixed;
        width: 56px;
        height: 56px;
        bottom: 24px;
        right: 24px;
        background-color: #25D366;
        color: white;
        border-radius: 50%;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        font-size: 24px;
        line-height: 56px;
        cursor: pointer;
        z-index: 1000;
    }
    </style>
    <a href="http://localhost:8081/manager" target="_blank" class="floating-btn">📲</a>
    """,
    unsafe_allow_html=True,
)