import pandas as pd
import sqlite3
import re

def clean_phone(phone):
    if pd.isna(phone):
        return phone
    phone_str = str(phone).strip()
    if phone_str == '':
        return None
    phone_clean = re.sub(r'[()\-\s]', '', phone_str)
    if len(phone_clean) == 11 and phone_clean.isdigit():
        return '55' + phone_clean
    if phone_clean.isdigit():
        return phone_clean
    return phone_clean

def _ensure_unique_columns(columns):
    seen = {}
    unique_cols = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            unique_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            unique_cols.append(col)
    return unique_cols

def clean_dataframe(df_dados):
    """
    Função auxiliar para padronização final do dataframe
    antes de preparar para o banco.
    """
    # Mapeamentos extras para garantir que cairão em colunas aceitas
    rename_mapping = {
        'aluno': 'nome_aluno',
        'nome_do_aluno': 'nome_aluno',
        'data_nascimento': 'nascimento',
        'data ': 'nascimento',
        'telefone_responsavel': 'telefone_responsavel',  # sem acento se sanitizador rodou
        'telefone_celular': 'telefone_celular',
        'ra': 'matricula',
        'id_aluno': 'matricula',
        'registro': 'matricula',
        'codigo': 'matricula'
    }
    df_dados.rename(columns=rename_mapping, inplace=True)
    
    for col in list(df_dados.columns):
        if 'data' in col and col != 'nascimento':
            df_dados.rename(columns={col: 'nascimento'}, inplace=True)
            break
            
    cpf_cols = [col for col in df_dados.columns if 'cpf' in col.lower()]
    if cpf_cols:
        df_dados.drop(columns=cpf_cols, inplace=True, errors='ignore')
        
    if 'matricula' in df_dados.columns:
        df_dados.dropna(subset=['matricula'], inplace=True)
        # Limpa a matrícula deixando apenas números
        df_dados['matricula'] = df_dados['matricula'].astype(str).str.replace(r'\D', '', regex=True)
        df_dados = df_dados[df_dados['matricula'].str.strip() != '']
        
    phone_cols = [col for col in df_dados.columns if any(k in col.lower() for k in ['telefone', 'celular', 'whatsapp'])]
    for col in phone_cols:
        df_dados[col] = df_dados[col].apply(clean_phone)
        
    return df_dados

def process_xml(file):
    """
    Processa um arquivo XML físico contendo dados dos alunos.
    """
    # Usando o Pandas para extrair os dados diretamente do XML
    # Assumimos uma estrutura básica bidimensional (tabela no XML)
    try:
        df = pd.read_xml(file)
    except Exception as e:
        raise ValueError(f"Falha ao processar o XML: {e}")
        
    cabecalhos = df.columns.astype(str).str.strip().str.lower()
    # Remove acentos para facilitar mapeamento
    cabecalhos = cabecalhos.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    cabecalhos = cabecalhos.str.replace(r'\s+', '_', regex=True)
    df.columns = _ensure_unique_columns(cabecalhos.tolist())
    
    df = clean_dataframe(df)
    
    if 'turno' not in df.columns:
        df['turno'] = None
    if 'turma' not in df.columns:
        df['turma'] = None
        
    return df

def process_excel(file):
    """
    Processa o XLSX (Mantido por compatibilidade e exigências de posição geométrica da versão anterior).
    """
    all_sheets = pd.read_excel(file, sheet_name=None, header=None)
    consolidated_dfs = []
    
    for sheet_name, df_aba in all_sheets.items():
        if df_aba.empty or len(df_aba) < 3:
            continue
            
        try:
            turno = str(df_aba.iloc[0, 0]).strip() if df_aba.shape[1] > 0 else None
            turma = str(df_aba.iloc[0, 1]).strip() if df_aba.shape[1] > 1 else None
            
            cabecalhos = df_aba.iloc[1].astype(str).str.strip().str.lower()
            cabecalhos = cabecalhos.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
            cabecalhos = cabecalhos.str.replace(r'\s+', '_', regex=True)
            cabecalhos = _ensure_unique_columns(cabecalhos.tolist())
            
            df_dados = df_aba.iloc[2:].copy()
            df_dados.columns = cabecalhos
            df_dados.reset_index(drop=True, inplace=True)
            
            df_dados = clean_dataframe(df_dados)
            
            df_dados['turno'] = turno
            df_dados['turma'] = turma
            
            if not df_dados.empty:
                consolidated_dfs.append(df_dados)
                
        except Exception as e:
            raise ValueError(f"Erro ao processar a aba '{sheet_name}': {str(e)}")
            
    if not consolidated_dfs:
        raise ValueError("Nenhuma aba com dados válidos foi encontrada.")
        
    return pd.concat(consolidated_dfs, ignore_index=True)


def extract_data_for_db(df):
    """
    Gera a lista de tuplas para UPSERT com campos fixos garantidos.
    (Whitelist strategy para prevenir Injeção de SQL)
    """
    data_list = []
    for _, row in df.iterrows():
        row_dict = {k: v for k, v in row.items() if pd.notna(v)}
        
        # Mapping para compatibilidade (nome/nome_aluno)
        if 'nome_aluno' in row_dict and 'nome' not in row_dict:
            row_dict['nome'] = row_dict['nome_aluno']
            
        if 'matricula' not in row_dict:
            continue
            
        aluno_tupla = (
            re.sub(r'\D', '', str(row_dict.get('matricula'))),
            str(row_dict.get('nome', '')),
            str(row_dict.get('nascimento', '')),
            str(row_dict.get('telefone_responsavel', '')),
            str(row_dict.get('telefone_celular', '')),
            str(row_dict.get('turno', '')),
            str(row_dict.get('turma', ''))
        )
        data_list.append(aluno_tupla)
        
    return data_list