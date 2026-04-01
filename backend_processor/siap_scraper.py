import requests
from bs4 import BeautifulSoup
import logging
import os
import re
import json

# Configuração de logging básica
logger = logging.getLogger(__name__)

class SIAPScraper:
    def __init__(self):
        self.login_url = "https://siap.educacao.go.gov.br/login.aspx"
        self.session = requests.Session()
        # User-agent padrão para evitar bloqueios simples
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def _get_hidden_value(self, soup, field_name):
        """Extrai o valor de um campo hidden do ASP.NET com segurança."""
        tag = soup.find("input", {"name": field_name})
        return tag.get("value", "") if tag else ""


    def login_siap(self, usuario, senha):
        """
        Realiza o login no portal SIAP automatizando o bypass de CAPTCHA 
        e a captura de estados do ASP.NET WebForms.
        """
        try:
            logger.info("Iniciando tentativa de login no portal SIAP...")
            
            # 1. GET inicial para capturar tokens de segurança e o Captcha
            response = self.session.get(self.login_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 2. Extração de tokens ASP.NET (campos hidden) com segurança
            viewstate = self._get_hidden_value(soup, "__VIEWSTATE")
            viewstate_gen = self._get_hidden_value(soup, "__VIEWSTATEGENERATOR")
            event_validation = self._get_hidden_value(soup, "__EVENTVALIDATION")
            
            # 3. Captura do CAPTCHA (Texto dentro do span id='lblCaptcha')
            captcha_span = soup.find("span", {"id": "lblCaptcha"})
            if not captcha_span:
                logger.error("Elemento lblCaptcha não encontrado na página.")
                return None
            
            captcha_text = captcha_span.text.strip()
            logger.info(f"Bypass de Captcha detectado: {captcha_text}")

            # 4. Montagem do Payload de Login
            payload = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstate_gen,
                "__EVENTVALIDATION": event_validation,
                "txtLogin": usuario,
                "txtSenha": senha,
                "txtCaptcha": captcha_text,
                "btnLogon": "Entrar"
            }

            # 5. Execução do POST (Login)
            post_response = self.session.post(self.login_url, data=payload, timeout=30)
            post_response.raise_for_status()
            
            # 6. Verificação de Sucesso
            if "login.aspx" not in post_response.url.lower() or "Principal.aspx" in post_response.text:
                logger.info("✅ Login no SIAP realizado com sucesso!")
                return self.session
            else:
                soup_error = BeautifulSoup(post_response.text, 'lxml')
                error_msg = soup_error.find("span", {"id": "lblErro"}) 
                msg = error_msg.text if error_msg else "Credenciais Inválidas ou Erro Desconhecido"
                logger.warning(f"❌ Falha no login SIAP: {msg}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro de conexão/rede com o Portal SIAP: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado no módulo SIAP Scraper: {e}")
            return None

    def acessar_pagina_frequencia(self):
        """Acessa a página de Frequência Diária e retorna BeautifulSoup e HTML bruto."""
        url = "https://siap.educacao.go.gov.br/FrequenciaDiaria.aspx"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            logger.info("✅ Página de Frequência Diária acessada.")
            return soup, response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao acessar Frequência Diária: {e}")
            return None, None

    def extrair_turmas_preenchidas(self, soup):
        """Extrai turmas que já tiveram chamada feita hoje."""
        turmas = []
        if not soup:
            return turmas
        
        divs = soup.find_all("div", class_="listaTurmas")
        for div in divs:
            classes = div.get("class", [])
            if not ("dentroPrazo" in classes or "foraDoPrazo" in classes):
                continue
            codigo = div.get("data-codigoturma")
            nome_span = div.find("span")
            nome = nome_span.text.strip() if nome_span else ""
            
            onclick = div.get("onclick", "")
            match = re.search(r"__doPostBack\('([^']+)'\s*,\s*'([^']+)'\)", onclick)
            if match:
                event_target = match.group(1)
                event_argument = match.group(2)
            else:
                event_target = "ctl00$cphFuncionalidade$ControleFrequencia"
                event_argument = codigo
                
            turmas.append({
                "nome_turma": nome,
                "event_target": event_target,
                "event_argument": event_argument
            })
        logger.info(f"🔎 Encontradas {len(turmas)} turmas preenchidas para abertura.")
        return turmas

    def abrir_turma_do_postback(self, turma_info, html_anterior):
        """Simula o __doPostBack para abrir a página da turma."""
        soup_prev = BeautifulSoup(html_anterior, "lxml")
        viewstate = self._get_hidden_value(soup_prev, "__VIEWSTATE")
        viewstate_gen = self._get_hidden_value(soup_prev, "__VIEWSTATEGENERATOR")
        event_validation = self._get_hidden_value(soup_prev, "__EVENTVALIDATION")
        
        payload = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_gen,
            "__EVENTVALIDATION": event_validation,
            "__EVENTTARGET": turma_info["event_target"],
            "__EVENTARGUMENT": turma_info["event_argument"]
        }
        url = "https://siap.educacao.go.gov.br/FrequenciaDiaria.aspx"
        try:
            response = self.session.post(url, data=payload, timeout=30)
            response.raise_for_status()
            html = response.text
            
            os.makedirs("debug_html", exist_ok=True)
            debug_path = os.path.join("debug_html", f"debug_turma_{turma_info['nome_turma']}.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"✅ Turma {turma_info['nome_turma']} aberta e salva em {debug_path}.")
            return BeautifulSoup(html, "lxml"), html
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Falha ao abrir turma {turma_info['nome_turma']}: {e}")
            return None, None

    def extrair_faltas_da_turma(self, html_turma):
        """Extrai lista de alunos faltosos, ignorando faltas justificadas (Atestados)."""
        try:
            soup = BeautifulSoup(html_turma, "lxml")
            
            # Passo 1: Construir dicionário de alunos
            alunos_dict = {}
            lista_alunos = soup.find("div", class_="listaDeAlunos")
            if lista_alunos:
                for item in lista_alunos.find_all("div", class_="item"):
                    matricula_raw = item.get("data-matricula")
                    nome_div = item.find("div", class_="aluno")
                    if matricula_raw and nome_div:
                        matricula = re.sub(r'\D', '', matricula_raw)
                        nome_bruto = nome_div.get_text(strip=True)
                        nome_limpo = nome_bruto.split(".", 1)[-1].strip() if "." in nome_bruto else nome_bruto
                        alunos_dict[matricula] = nome_limpo

            # Passo 2: Verificar faltas baseado apenas em ausente e classe CSS
            faltosos = []
            lista_freq = soup.find("div", class_="listaDeFrequencias")
            if lista_freq:
                for item in lista_freq.find_all("div", class_="item"):
                    matricula_raw = item.get("data-matricula")
                    ausente = item.get("data-ausente")
                    classes = item.get("class", [])
                    
                    if matricula_raw and ausente == "True":
                        matricula = re.sub(r'\D', '', matricula_raw)
                        nome = alunos_dict.get(matricula, "")
                        
                        # Regra Simplificada e Infalível:
                        # Se ausente=True e NÃO tem 'justificada' na classe -> Adiciona como faltoso
                        if "justificada" in classes:
                            logger.info(f"✓ Aluno {nome} ({matricula}) ignorado: Falta com atestado justificada.")
                        else:
                            faltosos.append({"matricula": matricula, "nome": nome, "status": "Faltou"})
                            
            return faltosos
        except Exception as e:
            logger.error(f"❌ Erro ao extrair faltas da turma: {e}")
            return []

# Função de compatibilidade exigida pelo app.py
def login_siap(usuario, senha):
    scraper = SIAPScraper()
    return scraper.login_siap(usuario, senha)

if __name__ == "__main__":
    # Exemplo de uso para testes locais no terminal
    usuario = os.getenv("SIAP_USER")
    senha = os.getenv("SIAP_PASS")
    if not usuario or not senha:
        logger.error("Variáveis de ambiente SIAP_USER e SIAP_PASS não definidas.")
    else:
        scraper = SIAPScraper()
        if scraper.login_siap(usuario, senha):
            soup, html = scraper.acessar_pagina_frequencia()
            if soup:
                turmas = scraper.extrair_turmas_preenchidas(soup)
                for turma in turmas:
                    soup_turma, html_turma = scraper.abrir_turma_do_postback(turma, html)
                    if html_turma:
                        faltas = scraper.extrair_faltas_da_turma(html_turma)
                        if faltas:
                            logger.info(f"Faltas encontradas na turma {turma['nome_turma']}:")
                            print(json.dumps(faltas, indent=2, ensure_ascii=False))
                        else:
                            logger.info(f"Nenhuma falta regular na turma {turma['nome_turma']}.")
        else:
            logger.error("Login falhou, abortando fluxo.")