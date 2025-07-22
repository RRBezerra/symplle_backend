# src/middleware/auth_middleware.py
"""
Authentication Middleware para Symplle - FASE 1
JWT + segurança mantendo 100% compatibilidade
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
import bcrypt

class AuthService:
    """Serviço de autenticação enterprise-ready"""
    
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'symplle_jwt_secret_dev_change_in_production')
        self.algorithm = 'HS256'
        self.token_expiry = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
        
    def hash_password(self, password: str) -> str:
        """Hash password usando bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verificar password contra hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, user_id: int, email: str) -> str:
        """Gerar JWT token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expiry),
            'iat': datetime.now(timezone.utc),
            'iss': 'symplle-api'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> dict:
        """Decodificar JWT token"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise ValueError('Token expirado')
        except jwt.InvalidTokenError:
            raise ValueError('Token inválido')

# Instância global do serviço
auth_service = AuthService()

def token_required(f):
    """Decorator para rotas que precisam de autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN"
            except IndexError:
                return jsonify({
                    'success': False,
                    'message': 'Formato de token inválido'
                }), 401
        
        # Se token não fornecido, continuar (compatibilidade)
        if not token:
            g.current_user = None
            return f(*args, **kwargs)
        
        try:
            # Decodificar token
            payload = auth_service.decode_token(token)
            # Simular usuário (por enquanto, sem acessar banco)
            g.current_user = {'id': payload['user_id'], 'email': payload['email']}
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
        except Exception:
            return jsonify({
                'success': False,
                'message': 'Erro interno de autenticação'
            }), 500
            
        return f(*args, **kwargs)
    
    return decorated

def init_auth_middleware(app):
    """Inicializar middleware de autenticação na app Flask"""
    
    @app.before_request
    def load_user():
        g.current_user = None
    
    # Headers de segurança
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    print("🔐 Auth Middleware inicializado com sucesso!")