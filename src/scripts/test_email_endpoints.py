#!/usr/bin/env python3

import requests
import json

# Configuração da API
base_url = "http://localhost:5000/api"

def test_email_endpoints():
    """Testa todos os endpoints relacionados a email"""
    
    print("=== Testando endpoints de Email ===")
    
    # Dados de teste
    test_email = "teste@exemplo.com"
    test_username = "usuario_teste"
    test_code = "123456"
    
    try:
        # 1. Testar verificação de disponibilidade de email
        print(f"\n1. Testando verificação de email: {test_email}")
        response = requests.get(f"{base_url}/check-email?email={test_email}")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email disponível: {not data.get('exists', True)}")
        else:
            print(f"❌ Erro na verificação de email: {response.text}")
        
        # 2. Testar verificação de disponibilidade de username
        print(f"\n2. Testando verificação de username: {test_username}")
        response = requests.get(f"{base_url}/check-username?username={test_username}")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Username disponível: {not data.get('exists', True)}")
        else:
            print(f"❌ Erro na verificação de username: {response.text}")
        
        # 3. Testar envio de código de verificação de email
        print(f"\n3. Testando envio de verificação de email para: {test_email}")
        data = {"email": test_email}
        response = requests.post(f"{base_url}/send-email-verification", json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Código enviado com sucesso: {result.get('message', 'N/A')}")
        else:
            print(f"❌ Erro no envio de verificação: {response.text}")
        
        # 4. Testar verificação de código de email
        print(f"\n4. Testando verificação de código: {test_code}")
        data = {"email": test_email, "code": test_code}
        response = requests.post(f"{base_url}/verify-email", json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Código verificado: {result.get('message', 'N/A')}")
        else:
            print(f"❌ Erro na verificação de código: {response.text}")
            
        print("\n=== Teste de endpoints de Email concluído ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: Certifique-se de que o servidor Flask está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_email_endpoints()

