from flask import Blueprint, request, jsonify
from src.models import db
from src.models.user import User
from src.models.phone_otp import PhoneOTP
import random
import string

otp_bp = Blueprint('otp_routes', __name__)

# Dicionário para armazenar códigos OTP temporários
otp_codes = {}

@otp_bp.route('/api/check-phone', methods=['GET'])
def check_phone():
    """Verifica se um número de telefone já está em uso"""
    phone = request.args.get('phone')
    
    if not phone:
        return jsonify({
            'success': False,
            'message': 'Número de telefone não fornecido',
            'exists': False
        }), 400
    
    # Verificar se o telefone já existe no banco de dados
    user = User.query.filter_by(phone=phone).first()
    
    return jsonify({
        'success': True,
        'exists': user is not None
    })

@otp_bp.route('/api/send-otp', methods=['POST'])
def send_otp():
    """Envia um código OTP para o número de telefone fornecido"""
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({
            'success': False,
            'message': 'Número de telefone não fornecido'
        }), 400
    
    # Gerar código OTP de 6 dígitos
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Armazenar o código para verificação posterior
    otp_codes[phone] = otp_code
    
    # Em um ambiente real, enviar o SMS com o código
    # Aqui apenas simulamos o envio
    print(f"Código OTP para {phone}: {otp_code}")
    
    try:
        # Salvar o OTP no banco de dados
        phone_otp = PhoneOTP(
            phone_number=phone
        )
        
        db.session.add(phone_otp)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Código OTP enviado com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar código OTP: {str(e)}'
        }), 500

@otp_bp.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Verifica o código OTP enviado para o número de telefone"""
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        return jsonify({
            'success': False,
            'message': 'Número de telefone ou código não fornecido'
        }), 400
    
    # Verificar o código
    stored_code = otp_codes.get(phone)
    
    # Para desenvolvimento, aceitar o código 123456
    if code == '123456' or (stored_code and stored_code == code):
        # Limpar o código após verificação bem-sucedida
        if phone in otp_codes:
            del otp_codes[phone]
        
        try:
            # Atualizar o status de verificação no banco de dados
            phone_otp = PhoneOTP.query.filter_by(phone=phone).order_by(PhoneOTP.created_at.desc()).first()
            
            if phone_otp:
                phone_otp.verified = True
                db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Código OTP verificado com sucesso'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Erro ao verificar código OTP: {str(e)}'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'Código OTP inválido'
    }), 400
