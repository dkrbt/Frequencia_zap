import streamlit as st
import pandas as pd
import sys
import os

from backend_processor.db_importer import process_excel, process_xml, extract_data_for_db
from database.db_handler import DBHandler

st.set_page_config(page_title="Importador Escolar", layout="wide")

st.sidebar.title("⚙️ Controle do Sistema")
st.sidebar.write("Gerencie e importe a base de dados de alunos via XML ou Excel.")
if st.sidebar.button("🛑 Encerrar Servidor"):
    st.sidebar.warning("Feche esta tela/aba de navegador. O servidor deve ser encerrado gerencialmente pelo host, e não brutalmente.")

st.title("📚 Importação de Dados Escolares (XML/XLSX)")
st.write("Faça o upload da tabela XML ou planilha XLSX. O sistema consolidará os dados e removerá CPFs para adequação à LGPD.")

uploaded_file = st.file_uploader(
    "Selecione sua tabela XML ou planilha XLSX", 
    type=['xml', 'xlsx'], 
    accept_multiple_files=False
)

if uploaded_file:
    try:
        with st.spinner("Processando dados do arquivo em background..."):
            if uploaded_file.name.lower().endswith('.xml'):
                final_df = process_xml(uploaded_file)
            else:
                final_df = process_excel(uploaded_file)
            
        st.subheader("📝 Revisão de Dados Consolidados")
        st.info("💡 Revise a tabela abaixo. Clique em qualquer célula para editá-la ao vivo antes da gravação.")
        
        edited_df = st.data_editor(final_df, width="stretch", num_rows="dynamic")
        
        if st.button("💾 Salvar no Banco de Dados", type="primary"):
            try:
                db_handler = DBHandler()
                data_list = extract_data_for_db(edited_df)
                if data_list:
                    db_handler.upsert_students(data_list)
                    st.success(f"✅ {len(data_list)} Registros consolidados com sucesso via UPSERT no banco de dados!")
                else:
                    st.warning("Nenhum registro com matrícula válida encontrado para salvar.")
            except Exception as e:
                st.error(f"Falha ao salvar no banco de dados: {e}")
                
    except Exception as e:
        st.error(f"Erro crítico ao processar o arquivo: {e}")