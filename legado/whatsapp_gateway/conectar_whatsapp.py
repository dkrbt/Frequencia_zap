import requests
import json
import os
import time

BASE_URL = "http://localhost:8090"
API_KEY = "senha_super_secreta_cedom_2026"
INSTANCE_NAME = "cedom_bot"

headers = {"apikey": API_KEY, "Content-Type": "application/json"}

def salvar_html_qrcode(base64_str):
    if not base64_str or base64_str == "data:image/png;base64,":
        print("❌ QR Code inválido recebido.")
        return False
    
    if not base64_str.startswith("data:image"):
        base64_str = f"data:image/png;base64,{base64_str}"
    
    html_path = "qrcode_escola.html"
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>QR Code WhatsApp</title>
<style>body{{font-family:Arial;text-align:center;margin-top:40px;background:#f4f4f4;}}
.container{{background:white;padding:40px;border-radius:12px;display:inline-block;box-shadow:0 4px 20px rgba(0,0,0,0.1);}}
img{{max-width:320px;border:3px solid #ddd;padding:10px;border-radius:8px;}}</style>
</head>
<body>
<div class="container">
<h2>📱 Escaneie o QR Code com o WhatsApp</h2>
<p>WhatsApp → Aparelhos Conectados → Conectar Aparelho</p>
<img src="{base64_str}" alt="QR Code"/>
<p><strong>Aguarde até aparecer "Conectado".</strong></p>
</div>
</body></html>"""
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n✅ QR Code salvo em: {os.path.abspath(html_path)}")
    print("👉 Abra esse arquivo no navegador e escaneie com o celular.")
    return True

def iniciar_conexao():
    print(f"🔄 Processando instância '{INSTANCE_NAME}'...")

    # Primeiro tenta deletar se existir (evita 403)
    try:
        requests.delete(f"{BASE_URL}/instance/delete/{INSTANCE_NAME}", headers={"apikey": API_KEY})
        print("🗑️ Instância antiga removida (se existia).")
        time.sleep(5)
    except:
        pass

    # Cria a instância
    payload = {
        "instanceName": INSTANCE_NAME,
        "token": "token_sistema_escola",
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS"
    }

    try:
        response = requests.post(f"{BASE_URL}/instance/create", headers=headers, json=payload, timeout=30)
        print(f"Status criação: {response.status_code}")

        try:
            dados = response.json()
        except:
            dados = response.text

        # Tenta extrair QR Code da criação
        if isinstance(dados, dict):
            base64_qr = dados.get("base64") or dados.get("qrcode", {}).get("base64")
            if base64_qr and salvar_html_qrcode(base64_qr):
                return

        # Se não pegou na criação, tenta o endpoint connect várias vezes
        print("⚠️ Tentando obter QR Code via /connect (pode demorar)...")
        for i in range(8):  # tenta até 8 vezes
            time.sleep(4 if i > 0 else 2)
            try:
                res = requests.get(f"{BASE_URL}/instance/connect/{INSTANCE_NAME}", headers={"apikey": API_KEY})
                data = res.json() if res.text else {}
                
                print(f"Tentativa {i+1}: {data}")
                
                base64_qr = None
                if isinstance(data, dict):
                    base64_qr = data.get("base64") or data.get("qrcode", {}).get("base64") or data.get("data", {}).get("qrcode", {}).get("base64")
                
                if base64_qr and base64_qr != "" and "count" not in str(base64_qr).lower():
                    if salvar_html_qrcode(base64_qr):
                        return
            except:
                pass
        
        print("❌ Não consegui obter o QR Code após várias tentativas.")
        print("Verifique os logs do Docker ou tente acessar o Dashboard da Evolution API diretamente.")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    iniciar_conexao()