import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    """Serviço para envio de emails de verificação com configuração real de SMTP"""
    
    def __init__(self):
        # Configurações de email para produção
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@symplle.com')
        
        # Flag para modo de desenvolvimento
        self.dev_mode = os.getenv('DEV_MODE', 'true').lower() == 'true'
    
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
            if self.dev_mode:
                # Modo de desenvolvimento - apenas simula o envio
                print(f"[EMAIL SERVICE - DEV MODE] Simulando envio de email para: {to_email}")
                print(f"[EMAIL SERVICE - DEV MODE] Código de verificação: {verification_code}")
                print(f"[EMAIL SERVICE - DEV MODE] Email enviado com sucesso!")
                return True
            
            # Modo de produção - envio real
            return self._send_real_email(to_email, verification_code)
            
        except Exception as e:
            print(f"[EMAIL SERVICE] Erro ao enviar email: {e}")
            return False
    
    def _send_real_email(self, to_email: str, verification_code: str) -> bool:
        """
        Envia email real usando SMTP
        """
        try:
            # Validar configurações
            if not self.email_user or not self.email_password:
                print("[EMAIL SERVICE] Configurações de email não encontradas")
                return False
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "SYMPLLE - Código de Verificação"
            
            # Corpo do email em texto simples
            text_body = f"""
Olá!

Seu código de verificação para o SYMPLLE é: {verification_code}

Este código expira em 10 minutos.

Se você não solicitou este código, ignore este email.

Atenciosamente,
Equipe SYMPLLE
            """
            
            # Corpo do email em HTML
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                  <h2 style="color: #333; text-align: center;">SYMPLLE</h2>
                  <div style="background-color: white; padding: 30px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333;">Código de Verificação</h3>
                    <p style="color: #666; font-size: 16px;">Olá!</p>
                    <p style="color: #666; font-size: 16px;">Seu código de verificação para o SYMPLLE é:</p>
                    <div style="text-align: center; margin: 30px 0;">
                      <span style="background-color: #007bff; color: white; padding: 15px 30px; font-size: 24px; font-weight: bold; border-radius: 5px; letter-spacing: 3px;">{verification_code}</span>
                    </div>
                    <p style="color: #666; font-size: 14px;">Este código expira em 10 minutos.</p>
                    <p style="color: #666; font-size: 14px;">Se você não solicitou este código, ignore este email.</p>
                  </div>
                  <p style="color: #999; font-size: 12px; text-align: center;">
                    Atenciosamente,<br>
                    Equipe SYMPLLE
                  </p>
                </div>
              </body>
            </html>
            """
            
            # Anexar ambas as versões
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Conectar ao servidor SMTP e enviar
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            print(f"[EMAIL SERVICE] Email enviado com sucesso para: {to_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL SERVICE] Erro ao enviar email real: {e}")
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
            if self.dev_mode:
                print(f"[EMAIL SERVICE - DEV MODE] Simulando envio de email de boas-vindas para: {to_email}")
                print(f"[EMAIL SERVICE - DEV MODE] Usuário: {username}")
                print(f"[EMAIL SERVICE - DEV MODE] Email de boas-vindas enviado com sucesso!")
                return True
            
            # Implementar envio real de email de boas-vindas
            return self._send_welcome_email_real(to_email, username)
            
        except Exception as e:
            print(f"[EMAIL SERVICE] Erro ao enviar email de boas-vindas: {e}")
            return False
    
    def _send_welcome_email_real(self, to_email: str, username: str) -> bool:
        """
        Envia email de boas-vindas real
        """
        try:
            if not self.email_user or not self.email_password:
                return False
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Bem-vindo ao SYMPLLE!"
            
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                  <h2 style="color: #333; text-align: center;">Bem-vindo ao SYMPLLE!</h2>
                  <div style="background-color: white; padding: 30px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333;">Olá, {username}!</h3>
                    <p style="color: #666; font-size: 16px;">Parabéns! Sua conta no SYMPLLE foi criada com sucesso.</p>
                    <p style="color: #666; font-size: 16px;">Agora você pode:</p>
                    <ul style="color: #666; font-size: 16px;">
                      <li>Conectar-se com amigos e família</li>
                      <li>Compartilhar momentos especiais</li>
                      <li>Descobrir conteúdo interessante</li>
                      <li>Participar de conversas</li>
                    </ul>
                    <div style="text-align: center; margin: 30px 0;">
                      <a href="#" style="background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Começar a usar</a>
                    </div>
                  </div>
                  <p style="color: #999; font-size: 12px; text-align: center;">
                    Obrigado por escolher o SYMPLLE!<br>
                    Equipe SYMPLLE
                  </p>
                </div>
              </body>
            </html>
            """
            
            part = MIMEText(html_body, 'html')
            msg.attach(part)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            print(f"[EMAIL SERVICE] Email de boas-vindas enviado para: {to_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL SERVICE] Erro ao enviar email de boas-vindas: {e}")
            return False
    
    def set_production_mode(self):
        """Ativa o modo de produção (envio real de emails)"""
        self.dev_mode = False
        print("[EMAIL SERVICE] Modo de produção ativado")
    
    def set_dev_mode(self):
        """Ativa o modo de desenvolvimento (simulação de envio)"""
        self.dev_mode = True
        print("[EMAIL SERVICE] Modo de desenvolvimento ativado")

