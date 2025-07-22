import os
import requests
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

class SMSService:
    """
    Serviço para envio de SMS usando Twilio ou outro provedor.
    Esta classe abstrai a implementação específica do provedor de SMS.
    """
    
    def __init__(self):
        """
        Inicializa o serviço de SMS com as credenciais do provedor.
        """
        # Twilio credentials
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Modo de simulação (para desenvolvimento sem custos)
        self.simulation_mode = os.getenv('SMS_SIMULATION_MODE', 'True').lower() == 'false'
    
    def send_sms(self, to_number, message):
        """
        Envia uma mensagem SMS para o número especificado.
        
        Args:
            to_number (str): Número de telefone do destinatário (formato E.164: +XXXXXXXXXXXX)
            message (str): Conteúdo da mensagem a ser enviada
            
        Returns:
            dict: Resultado do envio com status e detalhes
        """
        
        print(f"Credenciais Twilio: SID={self.twilio_account_sid}, Token={'*'*10}, From={self.twilio_phone_number}")
        print(f"Simulation Mode: {self.simulation_mode}")


        # Modo de simulação (para desenvolvimento)
        if self.simulation_mode:
            print(f"[SIMULAÇÃO SMS] Para: {to_number}, Mensagem: {message}")
            return {
                'success': True,
                'provider': 'simulation',
                'message': 'SMS simulado enviado com sucesso'
            }
        
        # Verificar se as credenciais do Twilio estão configuradas
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
            print("Erro: Credenciais do Twilio não configuradas. Verifique as variáveis de ambiente.")
            return {
                'success': False,
                'provider': 'twilio',
                'message': 'Credenciais do provedor não configuradas'
            }
        
        # Enviar SMS usando Twilio
        try:
            # Importar apenas quando necessário para evitar dependência desnecessária em modo de simulação
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message = client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_number
            )
            
            return {
                'success': True,
                'provider': 'twilio',
                'message_sid': message.sid,
                'status': message.status
            }
            
        except ImportError:
            return {
                'success': False,
                'provider': 'twilio',
                'message': 'Biblioteca Twilio não instalada. Execute: pip install twilio'
            }
        except Exception as e:
            return {
                'success': False,
                'provider': 'twilio',
                'message': f'Erro ao enviar SMS: {str(e)}'
            }
    
    def send_otp(self, to_number, otp_code):
        """
        Envia um código OTP via SMS.
        
        Args:
            to_number (str): Número de telefone do destinatário
            otp_code (str): Código OTP a ser enviado
            
        Returns:
            dict: Resultado do envio
        """
        message = f"Seu código de verificação SYMPLLE é: {otp_code}. Válido por 10 minutos."
        return self.send_sms(to_number, message)
