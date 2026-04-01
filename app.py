import streamlit as st
import pandas as pd
import os
import logging
import sqlite3
import requests
import subprocess
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importações do projeto
from backend_processor.db_importer import process_excel, process_xml, extract_data_for_db
from backend_processor.siap_scraper import login_siap, SIAPScraper
from core.db_handler import DBHandler
from core.processor import Processor
from services.school_api import SchoolAPI
from services.whatsapp_engine import WhatsAppEngine
from config import ADMIN_PASSWORD, EVOLUTION_API_URL, EVOLUTION_API_TOKEN, EVOLUTION_INSTANCE

# ====================== CONFIGURAÇÃO INICIAL ======================
st.set_page_config(
    page_title="Mamãe Coruja • Hub",
    layout="wide",
    page_icon="icon/mamae_coruja.ico",
    initial_sidebar_state="expanded"
)

load_dotenv()

# ====================== ESTILOS GLOBAIS (DESIGN PREMIUM) ======================
st.markdown("""
    <style>
    /* Fundo e Container Principal */
    .stApp {
        background-color: #f4f7f6;
    }
    
    /* Cabeçalhos */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }

    /* Cards de Métricas Estilizados */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Botão Flutuante */
    .floating-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 65px;
        height: 65px;
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white !important;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        z-index: 9999;
        text-decoration: none;
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .floating-btn:hover {
        transform: scale(1.1) rotate(5deg);
    }
    
    /* Inputs de Login */
    .stTextInput input {
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ====================== SISTEMA DE AUTENTICAÇÃO ======================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "api_token" not in st.session_state:
    st.session_state["api_token"] = None

def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; color:#1e3a8a; font-size:3rem;'>🔐 Mamãe Coruja</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#64748b; margin-top:-10px;'>Acesso Restrito ao Sistema</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("### Identificação Administrativa")
            with st.form("login_form"):
                password = st.text_input("Senha Mestra", type="password", placeholder="Digite sua senha")
                submit = st.form_submit_button("Entrar no Hub", use_container_width=True, type="primary")
                
                if submit:
                    if password == ADMIN_PASSWORD:
                        st.session_state["authenticated"] = True
                        st.session_state["api_token"] = EVOLUTION_API_TOKEN
                        st.success("✅ Acesso autorizado! Carregando infraestrutura...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta. Verifique suas credenciais.")

if not st.session_state["authenticated"]:
    login_screen()
    st.stop()

# ====================== INICIALIZAÇÃO DE COMPONENTES ======================
db_handler = DBHandler()
school_api = SchoolAPI()
whatsapp_engine = WhatsAppEngine()
processor = Processor(db_handler)

def get_evolution_status():
    try:
        url = f"{EVOLUTION_API_URL.rstrip('/')}/instance/connectionState/{EVOLUTION_INSTANCE}"
        headers = {"apikey": st.session_state["api_token"]}
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            return response.json().get("instance", {}).get("state", "UNKNOWN")
        return "DESCONECTADO"
    except:
        return "OFFLINE"

# ====================== SIDEBAR E NAVEGAÇÃO ======================
with st.sidebar:
    st.markdown("<div style='text-align:center;'><h2 style='margin-bottom:0;'>🚀 Mamãe Coruja</h2><p style='color:#64748b; font-size:0.8rem;'>v2.5 Stable Edition</p></div>", unsafe_allow_html=True)
    st.markdown(f"**Instância Ativa:** `{EVOLUTION_INSTANCE}`")
    
    st.divider()
    
    # SIAP Status Connection
    if 'siap_session' in st.session_state and st.session_state['siap_session']:
        st.success("🌐 **Portal SIAP:** Conectado")
        if st.button("🔌 Encerrar Sessão SIAP", use_container_width=True, type="secondary"):
            st.session_state['siap_session'] = None
            st.rerun()
    else:
        st.warning("🌐 **Portal SIAP:** Desconectado")
    
    st.divider()
    
    menu = st.radio(
        "Navegação do Hub",
        options=[
            "📊 Dashboard & Status", 
            "📥 Importação de Base", 
            "🌐 Login do Portal SIAP", 
            "📲 Disparo Automático", 
            "📑 Histórico Geral", 
            "🚨 Encerrar Sistema"
        ]
    )
    
    st.divider()
    if st.button("🚪 Logout Geral", type="primary", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["api_token"] = None
        st.rerun()

# ====================== PÁGINA: DASHBOARD ======================
if menu == "📊 Dashboard & Status":
    st.markdown('<h1 class="main-header">Painel de Controle</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Monitoramento de infraestrutura e base de dados</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    evo_status = get_evolution_status()
    
    with col1:
        st.metric("Status do WhatsApp", evo_status.upper(), delta="Online" if evo_status == "open" else "Offline", delta_color="normal")
        if evo_status != "open":
            st.error("⚠️ O WhatsApp está offline! Conecte no Manager.")
    
    with col2:
        try:
            with sqlite3.connect(db_handler.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM alunos_contatos").fetchone()[0]
            st.metric("Alunos Cadastrados", f"{count:,}")
        except:
            st.metric("Alunos Cadastrados", "0")

    with col3:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with sqlite3.connect(db_handler.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM notifications WHERE date_sent = ?", (today,)).fetchone()[0]
            st.metric("Notificações Hoje", count)
        except:
            st.metric("Notificações Hoje", "0")

    st.divider()
    st.subheader("⚙️ Atributos de Conexão")
    st.code(f"URL API: {EVOLUTION_API_URL}\nInstância: {EVOLUTION_INSTANCE}\nToken: [OCULTO POR SEGURANÇA]", language="bash")

# ====================== PÁGINA: IMPORTAÇÃO ======================
elif menu == "📥 Importação de Base":
    st.markdown('<h1 class="main-header">Importação de Alunos</h1>', unsafe_allow_html=True)
    st.write("Carregue arquivos XML ou Planilhas (XLSX) para sincronizar os contatos dos responsáveis.")
    
    uploaded_file = st.file_uploader("Arraste o arquivo aqui", type=['xml', 'xlsx'])
    
    if uploaded_file:
        try:
            with st.spinner("Lendo estrutura de dados..."):
                if uploaded_file.name.lower().endswith('.xml'):
                    final_df = process_xml(uploaded_file)
                else:
                    final_df = process_excel(uploaded_file)
                
            st.subheader("📝 Validação de Dados")
            edited_df = st.data_editor(final_df, use_container_width=True, num_rows="dynamic")
            
            if st.button("💾 Sincronizar com Banco de Dados", type="primary", use_container_width=True):
                data_list = extract_data_for_db(edited_df)
                if data_list:
                    db_handler.upsert_students(data_list)
                    st.success(f"✅ Sucesso! {len(data_list)} registros foram atualizados na base.")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

# ====================== PÁGINA: PORTAL SIAP ======================
elif menu == "🌐 Login do Portal SIAP":
    st.markdown('<h1 class="main-header">Portal SIAP</h1>', unsafe_allow_html=True)
    st.info("💡 A senha não é armazenada. O login é temporário e expira ao fechar o Hub.")

    if 'siap_session' in st.session_state and st.session_state['siap_session']:
        st.success("✅ Sessão do SIAP encontra-se ativa e pronta para mineração!")
        if st.button("Refazer Login (Limpar Sessão)"):
            st.session_state['siap_session'] = None
            st.rerun()
    else:
        with st.form("siap_login_form"):
            col_u, col_p = st.columns(2)
            with col_u: user_siap = st.text_input("CPF / Usuário", placeholder="Apenas números")
            with col_p: pass_siap = st.text_input("Senha SIAP", type="password")
            submit_siap = st.form_submit_button("🔨 Validar Acesso ao Portal", use_container_width=True, type="primary")

            if submit_siap:
                if not user_siap or not pass_siap:
                    st.error("Preencha as credenciais.")
                else:
                    with st.spinner("Autenticando e resolvendo protocolos de segurança..."):
                        session = login_siap(user_siap, pass_siap)
                        if session:
                            st.session_state['siap_session'] = session
                            st.success("✅ Autenticação realizada!")
                            st.rerun()
                        else:
                            st.error("❌ Falha no login. Verifique se o portal SIAP está online.")

# ====================== PÁGINA: DISPARO AUTOMÁTICO ======================
elif menu == "📲 Disparo Automático":
    st.markdown('<h1 class="main-header">Gerenciador de Faltas</h1>', unsafe_allow_html=True)
    st.write("Identifique as ausências do dia no SIAP e dispare as mensagens automáticas.")

    today_val = datetime.now().strftime('%Y-%m-%d')
    
    # Auto-load do banco
    if 'absences_to_send' not in st.session_state:
        df_db = processor.carregar_e_formatar_faltas_do_banco(today_val)
        if not df_db.empty:
            st.session_state['absences_to_send'] = df_db
            st.session_state['today_date'] = today_val

    st.subheader("🚀 Ações de Captura")
    col_api, col_siap = st.columns(2)
    
    with col_api:
        if st.button("📡 Consulta via API da Escola", use_container_width=True):
            with st.spinner("Cruzando dados na nuvem..."):
                attendance_data = school_api.get_attendance_data(date=today_val)
                if not attendance_data:
                    st.error("API indisponível no momento.")
                else:
                    absences_df = processor.process_attendance(attendance_data)
                    if absences_df.empty: st.success("Nenhuma falta nova hoje.")
                    else:
                        st.session_state['absences_to_send'] = absences_df
                        st.session_state['today_date'] = today_val
                        st.rerun()

    with col_siap:
        if st.button("⛏️ Iniciar Mineração no SIAP", type="primary", use_container_width=True):
            if 'siap_session' not in st.session_state or not st.session_state['siap_session']:
                st.error("⚠️ Portal SIAP desconectado. Faça o login primeiro.")
            else:
                with st.status("⛏️ Minerando frequência escolar...", expanded=True) as status:
                    scraper = SIAPScraper()
                    scraper.session = st.session_state['siap_session']
                    
                    status.write("Acessando área de frequência...")
                    soup, html_base = scraper.acessar_pagina_frequencia()
                    if soup:
                        turmas = scraper.extrair_turmas_preenchidas(soup)
                        if turmas:
                            all_faltas = []
                            for turma in turmas:
                                status.write(f"Vistoriando turma: {turma['nome_turma']}...")
                                _, html_turma = scraper.abrir_turma_do_postback(turma, html_base)
                                if html_turma:
                                    all_faltas.extend(scraper.extrair_faltas_da_turma(html_turma))
                            
                            if all_faltas:
                                status.write("Cruzando com base de dados local...")
                                absences_df = processor.processar_faltas_e_gerar_mensagens(all_faltas)
                                st.session_state['absences_to_send'] = absences_df
                                st.session_state['today_date'] = today_val
                                status.update(label="✅ Varredura Concluída!", state="complete")
                                st.rerun()
                            else:
                                status.update(label="✅ Finalizado (Zero Ausências)", state="complete")
                        else:
                            status.update(label="ℹ️ Nenhuma chamada lançada hoje.", state="complete")
                    else:
                        st.error("Portal SIAP parou de responder.")

    if 'absences_to_send' in st.session_state:
        df = st.session_state['absences_to_send'].reset_index(drop=True)
        st.subheader(f"📋 Alunos Identificados ({len(df)})")
        
        df_display = df.copy()
        df_display.insert(0, "Enviar?", True)
        
        edited_selection = st.data_editor(
            df_display, 
            hide_index=True, 
            disabled=["student_name", "guardian_phone", "message", "matricula", "turma"],
            use_container_width=True,
            key="absence_editor"
        )
        
        if st.button("🚀 Confirmar Envio de Mensagens", use_container_width=True, type="primary"):
            to_send = edited_selection[edited_selection["Enviar?"] == True]
            if not to_send.empty:
                progress = st.progress(0)
                status_text = st.empty()
                success_count = 0
                
                for i, (_, row) in enumerate(to_send.iterrows()):
                    status_text.text(f"Enviando: {row['student_name']}...")
                    if not db_handler.check_sent_today(row['student_name'], row['guardian_phone'], st.session_state['today_date']):
                        if whatsapp_engine.send_notification(row['guardian_phone'], row['message']):
                            db_handler.log_sent(row['student_name'], row['guardian_phone'], st.session_state['today_date'])
                            success_count += 1
                    progress.progress((i + 1) / len(to_send))
                
                st.success(f"🎊 {success_count} mensagens enviadas com sucesso!")
                del st.session_state['absences_to_send']
                time.sleep(2)
                st.rerun()

# ====================== PÁGINA: HISTÓRICO ======================
elif menu == "📑 Histórico Geral":
    st.markdown('<h1 class="main-header">Relatórios de Envio</h1>', unsafe_allow_html=True)
    try:
        with sqlite3.connect(db_handler.db_path) as conn:
            hist_df = pd.read_sql_query(
                "SELECT student_name as Aluno, guardian_phone as Telefone, date_sent as Data, time_sent as Hora FROM notifications ORDER BY id DESC LIMIT 200", 
                conn
            )
        if not hist_df.empty:
            st.dataframe(hist_df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
    except Exception as e:
        st.error(f"Erro ao ler banco: {e}")

# ====================== PÁGINA: ENCERRAR ======================
elif menu == "🚨 Encerrar Sistema":
    st.markdown('<h1 class="main-header">Finalização</h1>', unsafe_allow_html=True)
    st.warning("⚠️ Isso encerrará a API do WhatsApp e este painel imediatamente.")
    
    if st.checkbox("Confirmo o desligamento total do sistema para hoje."):
        if st.button("🔴 DESLIGAR AGORA", type="primary", use_container_width=True):
            st.status("Desligando...")
            subprocess.run(["docker-compose", "down"], check=False)
            time.sleep(2)
            os._exit(0)

# ====================== BOTÃO FLUTUANTE ======================
st.markdown(
    """
    <a href="http://localhost:8081/manager" target="_blank" class="floating-btn" title="Configurar WhatsApp">
        📲
    </a>
    """,
    unsafe_allow_html=True,
)