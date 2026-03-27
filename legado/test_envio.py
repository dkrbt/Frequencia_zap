import urllib.request
import urllib.parse
import json
import sys

# Configurações do Evolution API
API_KEY = 'senha_super_secreta_cedom_2026'
BASE_URL = 'http://localhost:8090'

# A pessoa pode ter o 9 ou não ter o 9
NUMBER_WITHOUT_9 = '556182197941'
NUMBER_WITH_9 = '5561982197941'

print("⏳ Buscando instâncias conectadas no Evolution API...")

try:
    req = urllib.request.Request(f'{BASE_URL}/instance/fetchInstances', headers={'apikey': API_KEY})
    with urllib.request.urlopen(req) as response:
        instances = json.loads(response.read().decode())
        if not instances:
            sys.exit("Nenhuma instância conectada.")
            
        inst = instances[0]
        instance_name = inst.get('name') or inst.get('instanceName') or inst.get('instance', {}).get('instanceName')
        safe_instance_name = urllib.parse.quote(instance_name)
        
        print("\nVamos disparar para as duas variações do número (com e sem o '9')...")
        for num in [NUMBER_WITHOUT_9, NUMBER_WITH_9]:
            send_url = f'{BASE_URL}/message/sendText/{safe_instance_name}'
            data = {
                "number": num,
                "text": "🤖 *Verificação Final (Teste de API)*\n\nSe esta mensagem chegou, localizamos a rota exata do seu número no WhatsApp!"
            }
            
            print(f"Disparando para {num}...")
            req_send = urllib.request.Request(send_url, data=json.dumps(data).encode('utf-8'), headers={'apikey': API_KEY, 'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req_send) as res_send:
                    res_raw = res_send.read().decode()
                    print(f"Sucesso na API para {num}: {res_raw[:100]}...")
            except Exception as e:
                print(f"Falha na API para {num}: {e}")

except Exception as e:
    print(f"\n❌ Erro durante a operação: {e}")
