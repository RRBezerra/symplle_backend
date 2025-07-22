from flask import Blueprint, request, jsonify
from src.models import db
from src.models.user import User
from src.services.email_service import EmailService
import random
import string
import os

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
    
    # Verificar modo de desenvolvimento
    dev_mode = os.getenv('DEV_MODE', 'true').lower() == 'true'
    
    if dev_mode:
        # Modo de desenvolvimento - apenas simular
        print(f"[EMAIL ROUTES - DEV MODE] Código de verificação para {email}: {verification_code}")
        return jsonify({
            'success': True,
            'message': 'Código de verificação enviado com sucesso (modo dev)',
            'dev_code': verification_code  # Apenas para desenvolvimento
        })
    else:
        # Modo de produção - enviar email real
        email_sent = email_service.send_verification_email(email, verification_code)
        
        if email_sent:
            return jsonify({
                'success': True,
                'message': 'Código de verificação enviado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Falha ao enviar email de verificação'
            }), 500

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
    
    # Verificar modo de desenvolvimento
    dev_mode = os.getenv('DEV_MODE', 'true').lower() == 'true'
    
    # Para desenvolvimento, aceitar o código 123456
    if dev_mode and code == '123456':
        # Limpar o código após verificação bem-sucedida
        if email in verification_codes:
            del verification_codes[email]
        
        return jsonify({
            'success': True,
            'message': 'Email verificado com sucesso (modo dev)'
        })
    
    # Verificação normal
    if stored_code and stored_code == code:
        # Limpar o código após verificação bem-sucedida
        del verification_codes[email]
        
        return jsonify({
            'success': True,
            'message': 'Email verificado com sucesso'
        })
    
    return jsonify({
        'success': False,
        'message': 'Código de verificação inválido'
    }), 400

@email_routes.route('/api/set-production-mode', methods=['POST'])
def set_production_mode():
    """Endpoint para ativar modo de produção"""
    try:
        # Ativar modo de produção no serviço de email
        email_service.set_production_mode()
        
        # Definir variável de ambiente
        os.environ['DEV_MODE'] = 'false'
        
        return jsonify({
            'success': True,
            'message': 'Modo de produção ativado - emails reais serão enviados'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao ativar modo de produção: {str(e)}'
        }), 500

@email_routes.route('/api/set-dev-mode', methods=['POST'])
def set_dev_mode():
    """Endpoint para ativar modo de desenvolvimento"""
    try:
        # Ativar modo de desenvolvimento no serviço de email
        email_service.set_dev_mode()
        
        # Definir variável de ambiente
        os.environ['DEV_MODE'] = 'true'
        
        return jsonify({
            'success': True,
            'message': 'Modo de desenvolvimento ativado - emails serão simulados'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao ativar modo de desenvolvimento: {str(e)}'
        }), 500

