import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    """Serviço para envio de emails de verificação"""
    
    def __init__(self):
        # Configurações de email (para desenvolvimento, apenas simula o envio)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@symplle.com')
    
    def send_verification_email(self, to_email: str, verification_code: str) -> bool:
        """
        Envia um email de verificação com o código fornecido
        
        Args:
            to_email (str): Email de destino
            verification_code (str): Código de verificação de 6 dígitos
            
        Returns:
            bool: True se o email foi enviado com sucesso, False caso contrário
        """
        try:
            # Para desenvolvimento, apenas simula o envio
            print(f"[EMAIL SERVICE] Simulando envio de email para: {to_email}")
            print(f"[EMAIL SERVICE] Código de verificação: {verification_code}")
            print(f"[EMAIL SERVICE] Email enviado com sucesso!")
            
            # Em produção, descomente o código abaixo para envio real
            """
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "SYMPLLE - Código de Verificação"
            
            # Corpo do email
            body = f'''
            Olá!
            
            Seu código de verificação para o SYMPLLE é: {verification_code}
            
            Este código expira em 10 minutos.
            
            Se você não solicitou este código, ignore este email.
            
            Atenciosamente,
            Equipe SYMPLLE
            '''
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Conectar ao servidor SMTP e enviar
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            """
            
            return True
            
        except Exception as e:
            print(f"[EMAIL SERVICE] Erro ao enviar email: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        Envia um email de boas-vindas após o registro
        
        Args:
            to_email (str): Email de destino
            username (str): Nome de usuário
            
        Returns:
            bool: True se o email foi enviado com sucesso, False caso contrário
        """
        try:
            # Para desenvolvimento, apenas simula o envio
            print(f"[EMAIL SERVICE] Simulando envio de email de boas-vindas para: {to_email}")
            print(f"[EMAIL SERVICE] Usuário: {username}")
            print(f"[EMAIL SERVICE] Email de boas-vindas enviado com sucesso!")
            
            return True
            
        except Exception as e:
            print(f"[EMAIL SERVICE] Erro ao enviar email de boas-vindas: {e}")
            return False

