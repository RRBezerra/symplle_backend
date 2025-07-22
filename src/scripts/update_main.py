import os
import sys

# Adicionar o diretório pai ao path para poder importar os módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import db
from src.models.country import Country
from src.models.phone_otp import PhoneOTP
from src.routes.countries_routes import countries_bp
from src.routes.otp_routes import otp_bp

def update_main_py():
    """
    Atualiza o arquivo main.py para registrar o blueprint de OTP
    e garantir que todas as tabelas sejam criadas no banco de dados.
    """
    main_py_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
    
    # Verificar se o arquivo existe
    if not os.path.exists(main_py_path):
        print(f"Erro: Arquivo {main_py_path} não encontrado.")
        return False
    
    # Ler o conteúdo atual do arquivo
    with open(main_py_path, 'r') as file:
        content = file.read()
    
    # Verificar se o blueprint de OTP já está registrado
    if 'from src.routes.otp_routes import otp_bp' in content:
        print("O blueprint de OTP já está registrado no main.py.")
        return True
    
    # Adicionar a importação do blueprint de OTP
    import_line = 'from src.routes.countries_routes import countries_bp'
    new_import = 'from src.routes.countries_routes import countries_bp\nfrom src.routes.otp_routes import otp_bp'
    content = content.replace(import_line, new_import)
    
    # Adicionar o registro do blueprint de OTP
    register_line = 'app.register_blueprint(countries_bp, url_prefix=\'/api\')'
    new_register = 'app.register_blueprint(countries_bp, url_prefix=\'/api\')\napp.register_blueprint(otp_bp, url_prefix=\'/api\')'
    content = content.replace(register_line, new_register)
    
    # Adicionar a importação do modelo PhoneOTP
    import_model_line = 'from src.models.country import Country'
    new_import_model = 'from src.models.country import Country\nfrom src.models.phone_otp import PhoneOTP'
    
    if import_model_line in content:
        content = content.replace(import_model_line, new_import_model)
    else:
        # Se não encontrar a linha exata, adicionar após a importação do db
        db_import_line = 'from src.database import db'
        new_db_import = 'from src.database import db\nfrom src.models.country import Country\nfrom src.models.phone_otp import PhoneOTP'
        content = content.replace(db_import_line, new_db_import)
    
    # Escrever o conteúdo atualizado no arquivo
    with open(main_py_path, 'w') as file:
        file.write(content)
    
    print(f"Arquivo {main_py_path} atualizado com sucesso!")
    return True

if __name__ == "__main__":
    update_main_py()
    print("\nPara testar o sistema OTP, siga estes passos:")
    print("1. Reinicie o servidor Flask: python src/main.py")
    print("2. Execute o script de teste: python src/scripts/test_otp_api.py")
    print("3. Verifique os logs do servidor para ver o código OTP gerado")
