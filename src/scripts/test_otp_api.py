import os
import sys
import requests
import json

# Adicionar o diretório pai ao path para poder importar os módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_otp_endpoints():
    """
    Script para testar os endpoints de OTP do backend.
    Este script deve ser executado com o servidor Flask rodando.
    """
    base_url = "http://localhost:5000/api"
    
    # Testar o endpoint de envio de OTP
    print("\n=== Testando o endpoint de envio de OTP ===")
    
    # Número de telefone para teste (formato internacional)
    phone_number = "+5511999999999"
    
    # Dados para a requisição
    data = {
        "phone": phone_number  # Alterado para "phone" para corresponder ao esperado pelo backend
    }
    
    try:
        # Enviar a requisição POST para o endpoint de envio de OTP
        # Alterado para usar o endpoint correto /send-otp
        response = requests.post(f"{base_url}/send-otp", json=data)
        
        # Imprimir o status code e a resposta
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                print(f"Resposta: {json.dumps(response.json(), indent=2)}")
                success = response.json().get('success', False)
            except:
                print("Resposta não é um JSON válido")
                success = False
        else:
            print(f"Resposta: {response.text}")
            success = False
            
        if response.status_code == 200 and success:
            print("\n✅ Teste de envio de OTP bem-sucedido!")
            
            # Simular a verificação do OTP
            # Em um cenário real, o usuário receberia o código por SMS
            # Aqui, vamos usar um código fixo para teste
            print("\n=== Testando o endpoint de verificação de OTP ===")
            
            # Obter o código OTP do log do servidor (apenas para teste)
            print("\nPor favor, verifique o log do servidor Flask e insira o código OTP gerado:")
            print("(Ou use 123456 para teste em modo de desenvolvimento)")
            otp_code = input("Código OTP: ") or "123456"
            
            # Dados para a requisição de verificação
            verify_data = {
                "phone": phone_number,  # Alterado para "phone" para corresponder ao esperado pelo backend
                "code": otp_code  # Alterado para "code" para corresponder ao esperado pelo backend
            }
            
            # Enviar a requisição POST para o endpoint de verificação de OTP
            # Alterado para usar o endpoint correto /verify-otp
            verify_response = requests.post(f"{base_url}/verify-otp", json=verify_data)
            
            # Imprimir o status code e a resposta
            print(f"Status Code: {verify_response.status_code}")
            
            if verify_response.status_code == 200:
                try:
                    print(f"Resposta: {json.dumps(verify_response.json(), indent=2)}")
                    verify_success = verify_response.json().get('success', False)
                except:
                    print("Resposta não é um JSON válido")
                    verify_success = False
            else:
                print(f"Resposta: {verify_response.text}")
                verify_success = False
            
            if verify_response.status_code == 200 and verify_success:
                print("\n✅ Teste de verificação de OTP bem-sucedido!")
            else:
                print("\n❌ Teste de verificação de OTP falhou.")
        else:
            print("\n❌ Teste de envio de OTP falhou.")
    
    except Exception as e:
        print(f"\n❌ Erro ao testar os endpoints de OTP: {str(e)}")
        print("Certifique-se de que o servidor Flask está rodando e acessível.")

if __name__ == "__main__":
    test_otp_endpoints()
