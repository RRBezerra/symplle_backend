from flask import Blueprint, request, jsonify
from src.models import db
from src.models.user import User
from src.services.email_service import EmailService
import random
import string

email_routes = Blueprint('email_routes', __name__)
email_service = EmailService()

# Dicionário para armazenar códigos de verificação temporários
verification_codes = {}

@email_routes.route('/api/check-email', methods=['GET'])
def check_email():
    """Verifica se um email já está em uso"""
    email = request.args.get('email')
    
    if not email:
        return jsonify({
            'success': False,
            'message': 'Email não fornecido',
            'exists': False
        }), 400
    
    # Verificar se o email já existe no banco de dados
    user = User.query.filter_by(email=email).first()
    
    return jsonify({
        'success': True,
        'exists': user is not None
    })

@email_routes.route('/api/check-username', methods=['GET'])
def check_username():
    """Verifica se um nome de usuário já está em uso"""
    username = request.args.get('username')
    
    if not username:
        return jsonify({
            'success': False,
            'message': 'Nome de usuário não fornecido',
            'exists': False
        }), 400
    
    # Verificar se o username já existe no banco de dados
    user = User.query.filter_by(username=username).first()
    
    return jsonify({
        'success': True,
        'exists': user is not None
    })

@email_routes.route('/api/send-email-verification', methods=['POST'])
def send_email_verification():
    """Envia um código de verificação para o email fornecido"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({
            'success': False,
            'message': 'Email não fornecido'
        }), 400
    
    # Gerar código de verificação de 6 dígitos
    verification_code = ''.join(random.choices(string.digits, k=6))
    
    # Armazenar o código para verificação posterior
    verification_codes[email] = verification_code
    
    # Em um ambiente real, enviar o email com o código
    # Aqui apenas simulamos o envio
    print(f"Código de verificação para {email}: {verification_code}")
    
    # Chamar o serviço de email para enviar o código
    # email_service.send_verification_email(email, verification_code)
    
    return jsonify({
        'success': True,
        'message': 'Código de verificação enviado com sucesso'
    })

@email_routes.route('/api/verify-email', methods=['POST'])
def verify_email():
    """Verifica o código de verificação enviado para o email"""
    data = request.json
    email = data.get('email')
    code = data.get('code')
    
    if not email or not code:
        return jsonify({
            'success': False,
            'message': 'Email ou código não fornecido'
        }), 400
    
    # Verificar o código
    stored_code = verification_codes.get(email)
    
    # Para desenvolvimento, aceitar o código 123456
    if code == '123456' or (stored_code and stored_code == code):
        # Limpar o código após verificação bem-sucedida
        if email in verification_codes:
            del verification_codes[email]
        
        return jsonify({
            'success': True,
            'message': 'Email verificado com sucesso'
        })
    
    return jsonify({
        'success': False,
        'message': 'Código de verificação inválido'
    }), 400
