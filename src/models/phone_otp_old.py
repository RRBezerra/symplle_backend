from src.models import db
from datetime import datetime, timedelta, timezone
import random
import string

class PhoneOTP(db.Model):
    """
    Modelo para armazenar códigos OTP (One-Time Password) para verificação de telefone.
    """
    __tablename__ = "phone_otps"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)

    def __init__(self, phone_number, expiration_minutes=10):
        """
        Inicializa um novo código OTP para o número de telefone fornecido.
        
        Args:
            phone_number (str): Número de telefone com código do país (ex: +5511999999999)
            expiration_minutes (int): Tempo de validade do código em minutos
        """
        self.phone_number = phone_number
        self.otp_code = self._generate_otp()
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(minutes=expiration_minutes)
        self.verified = False
        self.attempts = 0

    def _generate_otp(self, length=6):
        """
        Gera um código OTP numérico aleatório.
        
        Args:
            length (int): Comprimento do código OTP
            
        Returns:
            str: Código OTP gerado
        """
        return ''.join(random.choices(string.digits, k=length))

    def is_valid(self):
        """
        Verifica se o código OTP ainda é válido (não expirou e não foi verificado).
        
        Returns:
            bool: True se o código for válido, False caso contrário
        """
        return not self.verified and datetime.now(timezone.utc) <= self.expires_at

    def verify(self, code):
        """
        Verifica se o código fornecido corresponde ao código OTP armazenado.
        
        Args:
            code (str): Código OTP fornecido pelo usuário
            
        Returns:
            bool: True se o código for válido, False caso contrário
        """
        self.attempts += 1
        
        # Verificar se o código já foi usado ou expirou
        if self.verified or datetime.now(timezone.utc) > self.expires_at:
            return False
        
        # Verificar se o código corresponde
        if self.otp_code == code:
            self.verified = True
            return True
            
        return False

    @classmethod
    def generate_for_phone(cls, phone_number, expiration_minutes=10):
        """
        Gera um novo código OTP para o número de telefone fornecido.
        Se já existir um código válido, invalida-o e cria um novo.
        
        Args:
            phone_number (str): Número de telefone com código do país
            expiration_minutes (int): Tempo de validade do código em minutos
            
        Returns:
            PhoneOTP: Nova instância de PhoneOTP
        """
        # Invalidar códigos anteriores para este número
        previous_otps = cls.query.filter_by(
            phone_number=phone_number,
            verified=False
        ).all()
        
        for otp in previous_otps:
            otp.verified = True
        
        # Criar novo código OTP
        new_otp = cls(phone_number, expiration_minutes)
        
        # Adicionar à sessão e commit
        db.session.add(new_otp)
        db.session.commit()
        
        return new_otp

    def to_dict(self):
        """
        Converte o objeto para um dicionário (para serialização JSON).
        Não inclui o código OTP por razões de segurança.
        
        Returns:
            dict: Representação em dicionário do objeto
        """
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "verified": self.verified,
            "attempts": self.attempts
        }
