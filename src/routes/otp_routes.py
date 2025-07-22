from flask import Blueprint, request, jsonify
from src.models import db
from src.models.user import User
from src.models.phone_otp import PhoneOTP
from src.services.otp_service import OTPService
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
    
    try:
        # Salvar o OTP no banco de dados
        # O construtor espera 'phone_number' e gera o código internamente.
        phone_otp = PhoneOTP(phone_number=phone)
        
        # Recuperar o código gerado pelo modelo para usar/enviar
        generated_otp_code = phone_otp.otp_code
        print(f"Código OTP gerado e salvo para {phone}: {generated_otp_code}")
        
        # Atualizar o dicionário temporário (se ainda for necessário)
        otp_codes[phone] = generated_otp_code
        
        db.session.add(phone_otp)
        db.session.commit()
        
         # Use o OTPService para enviar o SMS        
        otp_service = OTPService()
        success = otp_service.send_otp(phone)

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
    
    print(f"Recebida solicitação de verificação OTP - Telefone: {phone}, Código: {code}")
    
    if not phone or not code:
        print(f"Erro: Telefone ou código não fornecido")
        return jsonify({
            'success': False,
            'message': 'Número de telefone ou código não fornecido'
        }), 400
    
    try:
        # Buscar o código OTP mais recente do banco de dados
        phone_otp = PhoneOTP.query.filter_by(phone_number=phone).order_by(PhoneOTP.created_at.desc()).first()
        
        print(f"OTP encontrado no banco: {phone_otp}")
        
        # Verificar se o código é válido (123456 para desenvolvimento ou código do banco)
        if code == '123456' or (phone_otp and phone_otp.otp_code == code and phone_otp.is_valid()):
            print(f"Código OTP válido para o telefone {phone}")
            
            # Atualizar o status de verificação no banco de dados
            if phone_otp:
                phone_otp.verified = True
                db.session.commit()
                print(f"Status de verificação atualizado no banco de dados")
            
            # Limpar o código do dicionário temporário (se existir)
            if phone in otp_codes:
                del otp_codes[phone]
                print(f"Código removido do dicionário temporário")
            
            return jsonify({
                'success': True,
                'message': 'Código OTP verificado com sucesso'
            })
        else:
            # Verificar por que o código é inválido
            if not phone_otp:
                print(f"Erro: Nenhum OTP encontrado para o telefone {phone}")
            elif not phone_otp.is_valid():
                print(f"Erro: OTP expirado para o telefone {phone}")
            else:
                print(f"Erro: Código OTP incorreto para o telefone {phone}. Esperado: {phone_otp.otp_code}, Recebido: {code}")
            
            return jsonify({
                'success': False,
                'message': 'Código OTP inválido ou expirado'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao verificar código OTP: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar código OTP: {str(e)}'
        }), 500
