# SUBSTITUA o conteúdo do seu main.py POR ESTE (versão simplificada)

import os
import sys
import i18n
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_migrate import Migrate
from i18n import i18n_utils


# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models import db
from src.routes.countries_routes import countries_bp
from src.routes.otp_routes import otp_bp
from src.routes.email_routes import email_routes
from src.routes.profile_routes import profile_bp

# Import do middleware auth (simplificado)
try:
    from middleware.auth_middleware import auth_service, init_auth_middleware
except ImportError:
    print("⚠️ Auth middleware não encontrado - criando versão básica")
    
    # Versão básica do auth_service
    import jwt
    import bcrypt
    from datetime import datetime, timedelta, timezone
    
    class SimpleAuthService:
        def __init__(self):
            self.secret_key = 'symplle_jwt_secret_dev'
            self.algorithm = 'HS256'
        
        def hash_password(self, password: str) -> str:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        def verify_password(self, password: str, hashed: str) -> bool:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
        def generate_token(self, user_id: int, email: str) -> str:
            payload = {
                'user_id': user_id,
                'email': email,
                'exp': datetime.now(timezone.utc) + timedelta(hours=24),
                'iat': datetime.now(timezone.utc)
            }
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    auth_service = SimpleAuthService()
    
    def init_auth_middleware(app):
        @app.before_request
        def load_user():
            g.current_user = None
        print("🔐 Auth middleware básico inicializado")

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)  # Habilitar CORS para permitir requisições do Flutter
app.config['SECRET_KEY'] = 'symplle_secret_key_change_in_production'

# Configuração do banco de dados SQLite
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../../symplle.db'
import os
# Caminho absoluto garantido
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'symplle.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
print(f"🗄️ Banco configurado em: {db_path}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Inicializar middleware de segurança
init_auth_middleware(app)

# Registrar blueprints existentes
app.register_blueprint(countries_bp, url_prefix='/api')
app.register_blueprint(otp_bp)
app.register_blueprint(email_routes)
app.register_blueprint(profile_bp, url_prefix='/api')

# === ROTAS JWT SIMPLIFICADAS ===

@app.route('/api/auth/register', methods=['POST'])
def jwt_register():
    """Registro usando JWT - versão simplificada"""
    try:
        from src.models.user import User
        
        data = request.json
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        
        if not all([email, password, username]):
            return jsonify({
                'success': False,
                'message': 'Email, senha e username são obrigatórios'
            }), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email ou username já está em uso'
            }), 400
        
        # Criar novo usuário
        password_hash = auth_service.hash_password(password)
        
        new_user = User(
            username=username,
            email=email,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone')
        )
        
        # Adicionar campos de segurança se existirem
        if hasattr(new_user, 'password_hash'):
            new_user.password_hash = password_hash
        if hasattr(new_user, 'is_active'):
            new_user.is_active = True
        
        db.session.add(new_user)
        db.session.commit()
        
        # Gerar token
        token = auth_service.generate_token(new_user.id, new_user.email)
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'token': token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Erro no registro: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def jwt_login():
    """Login usando JWT - versão simplificada"""
    try:
        from src.models.user import User
        
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Credenciais inválidas'
            }), 401
        
        # Verificar senha
        if not hasattr(user, 'password_hash') or not user.password_hash:
            # Usuário antigo sem senha - primeiro login
            user.password_hash = auth_service.hash_password(password)
            db.session.commit()
        else:
            if not auth_service.verify_password(password, user.password_hash):
                return jsonify({
                    'success': False,
                    'message': 'Credenciais inválidas'
                }), 401
        
        # Gerar token
        token = auth_service.generate_token(user.id, user.email)
        
        # Atualizar último login se campo existir
        if hasattr(user, 'last_login'):
            user.last_login = db.func.now()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'token': token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check com informações de segurança"""
    try:
        # Verificar conexão com banco
        db.session.execute(db.text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0-jwt',
            'database': 'connected',
            'security': 'jwt-enabled',
            'features': ['JWT Auth', 'Security Headers']
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': 'Database connection failed'
        }), 500

@app.route('/')
def index():
    return jsonify({"message": "Symplle API is running with JWT!"})

@app.route('/api/create-profile', methods=['POST'])
def create_profile():
    """Criar/atualizar perfil do usuário"""
    try:
        from src.models.user import User
        
        data = request.json
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name', '')
        
        if not email or not username:
            return jsonify({
                'success': False,
                'message': 'Email e username são obrigatórios'
            }), 400
        
        # Buscar usuário existente
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Atualizar usuário existente
            user.first_name = first_name
            user.last_name = last_name
            # Marcar como verificado
            user.email_verified = True
            user.phone_verified = True
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Perfil atualizado com sucesso',
                'user': user.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
            
    except Exception as e:
        print(f"Erro ao criar perfil: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/users', methods=['POST'])
def create_user_alt():
    """Endpoint alternativo para criar usuário"""
    try:
        from src.models.user import User
        
        data = request.json
        username = data.get('username')
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        
        if not username or not email:
            return jsonify({
                'success': False,
                'message': 'Username e email são obrigatórios'
            }), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            # Atualizar usuário existente
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            if phone:
                existing_user.phone = phone
            existing_user.email_verified = True
            existing_user.phone_verified = True
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Usuário atualizado com sucesso',
                'user': existing_user.to_dict()
            }), 201
        else:
            # Criar novo usuário
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            
            # Marcar como verificado
            new_user.email_verified = True
            new_user.phone_verified = True
            
            db.session.add(new_user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user': new_user.to_dict()
            }), 201
            
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Criar tabelas no banco de dados
    app.run(host='0.0.0.0', port=5000, debug=True)