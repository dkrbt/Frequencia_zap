import requests
import json
import base64

# Configurações do seu docker-compose.yml
API_URL = "http://localhost:8090"
API_KEY = "d" 
INSTANCE_NAME = "Leo TESTE" # Nome da instância (pode ser qualquer um)
NUMERO_DESTINO = "556199794997"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

def criar_instancia():
    print(f"Criando instância '{INSTANCE_NAME}'...")
    url = f"{API_URL}/instance/create"
    payload = {
        "instanceName": INSTANCE_NAME,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS"
    }
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in (200, 201):
        print("✅ Instância criada com sucesso!")
        data = response.json()
        
        # Muitas vezes o retorno traz o QR code em Base64 para você escanear
        if "qrcode" in data:
            print("\n🚨 Acesse o painel web em http://localhost:8090 para ler o QRCode")
            print("Ou leia o QR no app se houver integração no painel.")
        else:
            print(data)
    else:
        print(f"❌ Falha ao criar instância (Talvez ela já exista). Código: {response.status_code}")
        print(response.text)

def enviar_mensagem():
    print(f"\nEnviando mensagem para {NUMERO_DESTINO}...")
    url = f"{API_URL}/message/sendText/{INSTANCE_NAME}"
    payload = {
        "number": NUMERO_DESTINO,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "text": "Olá! Esta é uma mensagem de teste do sistema sendo conectada via Evolution API 🚀"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in (200, 201):
        print("✅ Mensagem enviada com sucesso!")
        print("Resposta da Evolution API:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("❌ Erro ao enviar a mensagem. Verifique se o seu celular já está conectado e autorizado na API.")
        print(f"Detalhes: {response.text}")

if __name__ == "__main__":
    print("=" * 40)
    print(" EVOLUTION API TESTER ".center(40))
    print("=" * 40)
    print("\nLembrete: Para enviar uma mensagem o seu WhatsApp precisa estar conectado à instância!")
    print("\n1. Criar a Instância (para escanear o QRCode e conectar)")
    print("2. Enviar a Mensagem de Teste")
    print("3. Sair\n")
    
    opcao = input("O que deseja fazer? (1, 2 ou 3): ")
    
    if opcao == '1':
        criar_instancia()
    elif opcao == '2':
        enviar_mensagem()
    else:
        print("Saindo...")
