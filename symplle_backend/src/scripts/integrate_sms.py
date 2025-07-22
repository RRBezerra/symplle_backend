import os
from src.services.sms_service import SMSService
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Criar uma instância do serviço de SMS
sms_service = SMSService()

def update_otp_routes():
    """
    Atualiza o arquivo de rotas OTP para integrar com o serviço de SMS.
    Este script deve ser executado após criar o serviço de SMS.
    """
    # Caminho para o arquivo de rotas OTP
    otp_routes_path = os.path.join(os.path.dirname(__file__), '..', 'routes', 'otp_routes.py')
    
    # Verificar se o arquivo existe
    if not os.path.exists(otp_routes_path):
        print(f"Erro: Arquivo {otp_routes_path} não encontrado.")
        return False
    
    # Ler o conteúdo atual do arquivo
    with open(otp_routes_path, 'r') as file:
        content = file.read()
    
    # Verificar se o serviço de SMS já está importado
    if 'from src.services.sms_service import SMSService' in content:
        print("O serviço de SMS já está integrado às rotas OTP.")
        return True
    
    # Adicionar a importação do serviço de SMS
    import_line = 'from flask import Blueprint, request, jsonify\n'
    new_import = 'from flask import Blueprint, request, jsonify\nfrom src.services.sms_service import SMSService\n'
    content = content.replace(import_line, new_import)
    
    # Adicionar a inicialização do serviço de SMS
    blueprint_line = 'otp_bp = Blueprint(\'otp\', __name__)\n'
    new_blueprint = 'otp_bp = Blueprint(\'otp\', __name__)\n\n# Inicializar o serviço de SMS\nsms_service = SMSService()\n'
    content = content.replace(blueprint_line, new_blueprint)
    
    # Atualizar o método de envio de OTP para usar o serviço de SMS
    old_print_line = '        print(f"Código OTP para {phone_number}: {otp.otp_code}")'
    new_sms_code = '''        # Enviar o código OTP via SMS
        sms_result = sms_service.send_otp(phone_number, otp.otp_code)
        
        # Log para desenvolvimento
        print(f"Código OTP para {phone_number}: {otp.otp_code}")
        print(f"Resultado do envio de SMS: {sms_result}")
        
        # Se estiver em modo de produção, não mostrar o código no log
        # if not sms_service.simulation_mode:
        #     print(f"SMS enviado para {phone_number}")'''
    
    content = content.replace(old_print_line, new_sms_code)
    
    # Escrever o conteúdo atualizado no arquivo
    with open(otp_routes_path, 'w') as file:
        file.write(content)
    
    print(f"Arquivo {otp_routes_path} atualizado com sucesso!")
    return True

if __name__ == "__main__":
    update_otp_routes()
