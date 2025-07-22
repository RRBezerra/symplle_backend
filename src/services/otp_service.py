from src.models import db
from src.services.sms_service import SMSService
import random
import string

class OTPService:
    """Serviço para gerenciamento de OTP com integração Twilio real"""
    
    def __init__(self):
        self.sms_service = SMSService()
        # Dicionário para armazenar códigos temporários (em produção, usar Redis ou banco)
        self.verification_codes = {}
        
        # Flag para modo de desenvolvimento
        self.dev_mode = False  # Alterar para False em produção
    
    def generate_otp(self) -> str:
        """Gera um código OTP de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_otp(self, phone_number: str) -> bool:
        """
        Envia código OTP via SMS
        
        Args:
            phone_number (str): Número de telefone no formato internacional
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            # Gerar código OTP
            otp_code = self.generate_otp()
            
            if self.dev_mode:
                # Modo de desenvolvimento - apenas simula o envio
                print(f"[OTP SERVICE - DEV MODE] Simulando envio de SMS para: {phone_number}")
                print(f"[OTP SERVICE - DEV MODE] Código OTP: {otp_code}")
                
                # Armazenar código para verificação
                self.verification_codes[phone_number] = otp_code
                return True
            
            # Modo de produção - envio real via Twilio
            return self._send_real_sms(phone_number, otp_code)
            
        except Exception as e:
            print(f"[OTP SERVICE] Erro ao enviar OTP: {e}")
            return False
    
    def _send_real_sms(self, phone_number: str, otp_code: str) -> bool:
        """
        Envia SMS real usando Twilio
        """
        try:
            message_body = f"Seu código de verificação SYMPLLE é: {otp_code}. Este código expira em 10 minutos."
            
            success = self.sms_service.send_sms(phone_number, message_body)
            
            if success:
                # Armazenar código para verificação
                self.verification_codes[phone_number] = otp_code
                print(f"[OTP SERVICE] SMS enviado com sucesso para: {phone_number}")
                return True
            else:
                print(f"[OTP SERVICE] Falha ao enviar SMS para: {phone_number}")
                return False
                
        except Exception as e:
            print(f"[OTP SERVICE] Erro ao enviar SMS real: {e}")
            return False
    
    def verify_otp(self, phone_number: str, code: str) -> bool:
        """
        Verifica se o código OTP está correto
        
        Args:
            phone_number (str): Número de telefone
            code (str): Código OTP fornecido pelo usuário
            
        Returns:
            bool: True se o código estiver correto, False caso contrário
        """
        try:
            stored_code = self.verification_codes.get(phone_number)
            
            # Em modo dev, aceitar código padrão 123456
            if self.dev_mode and code == '123456':
                return True
            
            # Verificar código armazenado
            if stored_code and stored_code == code:
                # Remover código após verificação bem-sucedida
                del self.verification_codes[phone_number]
                return True
            
            return False
            
        except Exception as e:
            print(f"[OTP SERVICE] Erro ao verificar OTP: {e}")
            return False
    
    def set_production_mode(self):
        """Ativa o modo de produção (envio real via Twilio)"""
        self.dev_mode = False
        print("[OTP SERVICE] Modo de produção ativado - usando Twilio")
    
    def set_dev_mode(self):
        """Ativa o modo de desenvolvimento (simulação de envio)"""
        self.dev_mode = True
        print("[OTP SERVICE] Modo de desenvolvimento ativado - simulando envio")

