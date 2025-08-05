# src/main.py - Symplle API com i18n integrado (versão para src/)
import os
import sys

# 🌍 AJUSTADO: Importar sistema i18n (main.py está em src/)
try:
    from i18n import init_app as init_i18n, i18n_utils, _, format_currency, format_date
    I18N_AVAILABLE = True
    print("✅ Sistema i18n carregado com sucesso!")
except ImportError:
    print("⚠️  Sistema i18n não encontrado - funcionando sem localização")
    I18N_AVAILABLE = False
    # Fallbacks para funcionar sem i18n
    def _(key, **kwargs): return key
    def format_currency(amount, currency=None): return f"${amount}"
    def format_date(date, format_type='medium'): return str(date)
    class MockI18nUtils:
        @staticmethod
        def format_api_response(data, message_key=None, success=True, **kwargs):
            return {
                'success': success,
                'data': data,
                'message': message_key or ('Success' if success else 'Error'),
                'locale': 'en_US'
            }
        @staticmethod
        def set_locale_context(): pass
    i18n_utils = MockI18nUtils()

from flask import Flask, jsonify, request, g, session, send_from_directory
from datetime import datetime
from flask_cors import CORS
from flask_migrate import Migrate

# 💬 CHAT SYSTEM: Importações mínimas necessárias
try:
    from flask_socketio import SocketIO
    CHAT_AVAILABLE = True
    print("✅ Flask-SocketIO carregado - Chat System disponível!")
except ImportError:
    print("⚠️ Flask-SocketIO não encontrado - Chat System indisponível")
    CHAT_AVAILABLE = False
    SocketIO = None

# AJUSTADO: Caminhos para imports (main.py está em src/)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # Pasta pai para acessar raiz

from src.models import db
from src.routes.countries_routes import countries_bp
from src.routes.upload_routes import upload_bp
from src.routes.otp_routes import otp_bp
from src.routes.email_routes import email_routes
from src.routes.profile_routes import profile_bp
from routes.posts_routes import posts_bp
#from routes.timeline_routes import timeline_bp

# 💬 CHAT SYSTEM: Importar rotas e eventos do chat (opcional)
if CHAT_AVAILABLE:
    try:
        from routes.chat_routes import chat_bp
        print("✅ Chat routes carregados!")
        try:
            from events.chat_events import register_chat_events
            print("✅ Chat events carregados!")
        except ImportError:
            print("⚠️ Chat events não encontrados - continuando só com REST API")
            register_chat_events = None
    except ImportError as e:
        print(f"⚠️ Chat routes não encontrados: {e} - continuando sem chat")
        CHAT_AVAILABLE = False
        chat_bp = None
        register_chat_events = None

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

# 🌍 ADICIONAR: Configurações i18n
app.config['DEFAULT_LOCALE'] = 'en_US'
app.config['SUPPORTED_LOCALES'] = ['pt_BR', 'en_US', 'es_ES']

CORS(app)  # Habilitar CORS para permitir requisições do Flutter
app.config['SECRET_KEY'] = 'symplle_secret_key_change_in_production'

# AJUSTADO: Configuração do banco de dados SQLite (main.py em src/)
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'symplle.db')  # Pasta pai
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
print(f"🗄️ Banco configurado em: {db_path}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# 💬 CHAT SYSTEM: Inicializar SocketIO se disponível
if CHAT_AVAILABLE and SocketIO:
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=True
    )
    print("✅ SocketIO inicializado para Chat System!")
    
    # Registrar eventos do chat se disponível
    if register_chat_events:
        try:
            register_chat_events(socketio)
            print("✅ Chat events registrados!")
        except Exception as e:
            print(f"⚠️ Erro ao registrar chat events: {e}")
    else:
        print("⚠️ Chat events não disponíveis - SocketIO funcionando sem chat events")
else:
    socketio = None
    print("⚠️ SocketIO não disponível - Chat System desabilitado")

# 🌍 ADICIONAR: Inicializar sistema i18n
if I18N_AVAILABLE:
    init_i18n(app)
    print("🌍 Sistema i18n inicializado com suporte a: PT-BR, EN-US, ES-ES")

# 🌍 ADICIONAR: Middleware para configurar locale antes de cada request
@app.before_request
def before_request():
    """Configurar locale e autenticação antes de cada request"""
    
    # 1. 🌍 Configurar locale baseado no request
    if I18N_AVAILABLE:
        # Primeiro tentar carregar da sessão
        saved_locale = session.get('locale')
        if saved_locale:
            from i18n import set_locale
            set_locale(saved_locale)
            g.locale = saved_locale
            print(f"🌍 Loaded from session: {saved_locale}")
        else:
            i18n_utils.set_locale_context()
            print(f"🌍 Auto-detected: {getattr(g, 'locale', 'en_US')}")
    
    # 2. 🔐 Configuração de usuário atual
    g.current_user = None
    
    # Log do request para debug
    if request.endpoint:
        locale = getattr(g, 'locale', 'en_US') if I18N_AVAILABLE else 'en_US'
        print(f"📝 {request.method} {request.path} | Locale: {locale}")

# 🌍 ADICIONAR: Headers de resposta com locale
@app.after_request
def after_request(response):
    """Adicionar headers de segurança e locale"""
    # Headers de segurança
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # 🌍 Header com locale atual
    if I18N_AVAILABLE:
        try:
            from i18n import get_locale
            current_locale = get_locale()
            response.headers['Content-Language'] = current_locale
            print(f"📡 Content-Language: {current_locale}")  # Debug
        except:
            if hasattr(g, 'locale'):
                response.headers['Content-Language'] = g.locale
            else:
                response.headers['Content-Language'] = 'en_US'
    
    return response

# Inicializar middleware de segurança
init_auth_middleware(app)

# Registrar blueprints existentes
app.register_blueprint(countries_bp, url_prefix='/api')
app.register_blueprint(otp_bp)
app.register_blueprint(email_routes)
app.register_blueprint(profile_bp, url_prefix='/api')
app.register_blueprint(upload_bp)
app.register_blueprint(posts_bp)
#app.register_blueprint(timeline_bp)

# 💬 CHAT SYSTEM: Registrar blueprint do chat se disponível
if CHAT_AVAILABLE and chat_bp:
    try:
        app.register_blueprint(chat_bp, url_prefix='/api')
        print("✅ Chat blueprint registrado em /api/chat/*")
    except Exception as e:
        print(f"⚠️ Erro ao registrar chat blueprint: {e}")
else:
    print("⚠️ Chat blueprint não disponível")

# 🌍 ADICIONAR: Rotas específicas do sistema i18n
@app.route('/api/i18n/info')
def i18n_info():
    """Informações sobre internacionalização disponível"""
    if not I18N_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Sistema i18n não disponível',
            'available': False
        })
    
    from datetime import datetime
    return jsonify(i18n_utils.format_api_response({
        'current_locale': getattr(g, 'locale', 'en_US'),
        'supported_locales': [
            {'code': 'pt_BR', 'name': 'Português (Brasil)', 'flag': '🇧🇷'},
            {'code': 'en_US', 'name': 'English (US)', 'flag': '🇺🇸'},
            {'code': 'es_ES', 'name': 'Español (España)', 'flag': '🇪🇸'}
        ],
        'date_formats': {
            'short': format_date(datetime.now(), 'short'),
            'medium': format_date(datetime.now(), 'medium'),
            'long': format_date(datetime.now(), 'long')
        },
        'currency_examples': {
            'amount': 1234.56,
            'formatted': format_currency(1234.56)
        },
        'sample_translations': {
            'welcome': _('app.welcome'),
            'login': _('auth.login.title'),
            'success': _('common.ok'),
            'cancel': _('common.cancel')
        }
    }, 'i18n.info_retrieved'))

@app.route('/api/i18n/change-locale', methods=['POST'])
def change_locale():
    """Trocar idioma da aplicação"""
    if not I18N_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Sistema i18n não disponível'
        }), 400
    
    try:        
        from i18n import set_locale
        
        data = request.get_json()
        new_locale = data.get('locale', '').strip()
        
        if not new_locale:
            return jsonify(i18n_utils.format_api_response(
                None, 'Locale é obrigatório', False
            )), 400
        
        # Validar locale
        supported = ['pt_BR', 'en_US', 'es_ES']
        if new_locale not in supported:
            return jsonify(i18n_utils.format_api_response(
                None, f'Locale não suportado. Use: {", ".join(supported)}', False
            )), 400
        
        # Definir novo locale
        set_locale(new_locale)
        g.locale = new_locale
        i18n_utils.set_locale_context(new_locale)
        session['locale'] = new_locale
        
        return jsonify(i18n_utils.format_api_response({
            'locale': new_locale,
            'message': _('settings.language.changed_success'),
            'examples': {
                'welcome': _('app.welcome'),
                'login': _('auth.login.title'),
                'date': format_date(datetime.now(), 'medium'),
                'currency': format_currency(1234.56)
            }
        }, 'Idioma alterado com sucesso'))
        
    except Exception as e:
        return jsonify(i18n_utils.format_api_response(
            None, f'Erro ao alterar idioma: {str(e)}', False
        )), 500

@app.route('/api/i18n/demo')
def i18n_demo():
    """Demonstração das funcionalidades de i18n/L10n"""
    if not I18N_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Sistema i18n não disponível',
            'demo': 'Sistema funcionando em modo básico'
        })
    
    from datetime import datetime
    
    # ✅ OBTER LOCALE ATUAL CORRETAMENTE
    try:
        from i18n import get_locale
        current_locale = get_locale()
    except:
        current_locale = getattr(g, 'locale', 'en_US')
    
    # ✅ GARANTIR QUE O LOCALE ESTÁ ATIVO
    if hasattr(g, 'locale') and g.locale:
        current_locale = g.locale
    
    print(f"🎭 Demo usando locale: {current_locale}")  # Debug
    
    demo_data = {
        'current_locale': current_locale,
        'translations': {
            'app_name': _('app.name'),
            'welcome_message': _('app.welcome'),
            'login_title': _('auth.login.title'),
            'success_message': _('auth.login.success', username='Demo User'),
            'save_button': _('common.save'),
            'cancel_button': _('common.cancel')
        },
        'formatting': {
            'date_now': format_date(datetime.now(), 'medium'),
            'currency_example': format_currency(1234.56),
            'relative_time': 'Formato implementado'
        }
    }
    
    return jsonify(i18n_utils.format_api_response(
        demo_data, 'Demo data retrieved successfully'
    ))

# === ROTAS JWT COM i18n ===

@app.route('/api/auth/register', methods=['POST'])
def jwt_register():
    """Registro usando JWT com mensagens localizadas"""
    try:
        from src.models.user import User
        
        data = request.json
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        
        if not all([email, password, username]):
            return jsonify(i18n_utils.format_api_response(
                None, _('auth.validation.fields_required'), False
            )), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return jsonify(i18n_utils.format_api_response(
                None, _('auth.validation.user_exists'), False
            )), 400
        
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
        
        return jsonify(i18n_utils.format_api_response({
            'token': token,
            'user': new_user.to_dict()
        }, _('auth.signup.success'), True)), 201
        
    except Exception as e:
        print(f"Erro no registro: {e}")
        db.session.rollback()
        return jsonify(i18n_utils.format_api_response(
            None, _('errors.server'), False
        )), 500

@app.route('/api/auth/login', methods=['POST'])
def jwt_login():
    """Login usando JWT com mensagens localizadas"""
    try:
        from src.models.user import User
        
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify(i18n_utils.format_api_response(
                None, _('auth.validation.email_password_required'), False
            )), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify(i18n_utils.format_api_response(
                None, _('auth.login.error'), False
            )), 401
        
        # Verificar senha
        if not hasattr(user, 'password_hash') or not user.password_hash:
            # Usuário antigo sem senha - primeiro login
            user.password_hash = auth_service.hash_password(password)
            db.session.commit()
        else:
            if not auth_service.verify_password(password, user.password_hash):
                return jsonify(i18n_utils.format_api_response(
                    None, _('auth.login.error'), False
                )), 401
        
        # Gerar token
        token = auth_service.generate_token(user.id, user.email)
        
        # Atualizar último login se campo existir
        if hasattr(user, 'last_login'):
            user.last_login = db.func.now()
            db.session.commit()
        
        return jsonify(i18n_utils.format_api_response({
            'token': token,
            'user': user.to_dict()
        }, _('auth.login.success', username=user.first_name or user.username), True))
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify(i18n_utils.format_api_response(
            None, _('errors.server'), False
        )), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check com informações de segurança, i18n e chat"""
    try:
        # Verificar conexão com banco
        db.session.execute(db.text('SELECT 1'))
        
        # Features disponíveis
        features = ['JWT Auth', 'Security Headers']
        if I18N_AVAILABLE:
            features.append('i18n/L10n')
        if CHAT_AVAILABLE:
            features.extend(['Real-time Chat', 'WebSocket'])
        
        health_data = {
            'status': 'healthy',
            'version': '1.0.0-jwt-i18n-chat-src',
            'database': 'connected',
            'security': 'jwt-enabled',
            'i18n': I18N_AVAILABLE,
            'chat_system': CHAT_AVAILABLE,
            'current_locale': getattr(g, 'locale', 'en_US') if I18N_AVAILABLE else 'en_US',
            'features': features,
            'main_location': 'src/'
        }
        
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                health_data, _('health.status_healthy'), True
            ))
        else:
            return jsonify({
                'success': True,
                'data': health_data,
                'message': 'System healthy'
            })
            
    except Exception as e:
        error_data = {
            'status': 'unhealthy',
            'error': 'Database connection failed'
        }
        
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                error_data, _('health.status_unhealthy'), False
            )), 500
        else:
            return jsonify({
                'success': False,
                'data': error_data,
                'message': 'System unhealthy'
            }), 500

@app.route('/')
def index():
    """Página inicial com informações localizadas"""
    endpoints = {
        'auth': '/api/auth',
        'i18n': '/api/i18n',
        'health': '/health'
    }
    
    # Adicionar endpoint do chat se disponível
    if CHAT_AVAILABLE:
        endpoints['chat'] = '/api/chat'
        endpoints['websocket'] = '/socket.io/'
    
    if I18N_AVAILABLE:
        return jsonify(i18n_utils.format_api_response({
            'app': _('app.name'),
            'message': _('app.welcome'),
            'version': '1.0.0-i18n-chat-src',
            'main_location': 'src/',
            'chat_system': CHAT_AVAILABLE,
            'endpoints': endpoints
        }, _('app.welcome')))
    else:
        return jsonify({
            "message": "Symplle API is running with JWT!",
            "version": "1.0.0-basic-chat-src",
            "main_location": "src/",
            "i18n": "not available",
            "chat_system": CHAT_AVAILABLE,
            "endpoints": endpoints
        })

@app.route('/api/create-profile', methods=['POST'])
def create_profile():
    """Criar/atualizar perfil do usuário com mensagens localizadas"""
    try:
        from src.models.user import User
        
        data = request.json
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name', '')
        
        if not email or not username:
            return jsonify(i18n_utils.format_api_response(
                None, _('profile.validation.email_username_required'), False
            )), 400
        
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
            
            return jsonify(i18n_utils.format_api_response(
                {'user': user.to_dict()}, _('profile.updated'), True
            ))
        else:
            return jsonify(i18n_utils.format_api_response(
                None, _('errors.not_found'), False
            )), 404
            
    except Exception as e:
        print(f"Erro ao criar perfil: {e}")
        db.session.rollback()
        return jsonify(i18n_utils.format_api_response(
            None, _('errors.server'), False
        )), 500

@app.route('/api/users', methods=['POST'])
def create_user_alt():
    """Endpoint alternativo para criar usuário com mensagens localizadas"""
    try:
        from src.models.user import User
        
        data = request.json
        username = data.get('username')
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        
        if not username or not email:
            return jsonify(i18n_utils.format_api_response(
                None, _('auth.validation.username_email_required'), False
            )), 400
        
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
            
            return jsonify(i18n_utils.format_api_response(
                {'user': existing_user.to_dict()}, _('profile.updated'), True
            )), 201
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
            
            return jsonify(i18n_utils.format_api_response(
                {'user': new_user.to_dict()}, _('auth.signup.success'), True
            )), 201
            
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        db.session.rollback()
        return jsonify(i18n_utils.format_api_response(
            None, _('errors.server'), False
        )), 500

# Servir arquivos estáticos de upload
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve arquivos enviados"""
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_from_directory(upload_dir, filename)

@app.route('/api/create-tables', methods=['POST'])
def create_tables():
    """Endpoint temporário para criar tabelas de posts"""
    try:
        from models.post import Post, Like, Comment
        db.create_all()
        return jsonify({
            "success": True,
            "message": "Tables created successfully",
            "tables": ["posts", "likes", "comments"]
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error creating tables: {str(e)}"
        }), 500

@app.route('/chat-test')
def chat_test():
    """Página de teste do sistema de chat"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Symplle Chat System - WebSocket Test</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status {
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            font-weight: bold;
        }
        .connected { background: rgba(76, 175, 80, 0.3); }
        .disconnected { background: rgba(244, 67, 54, 0.3); }
        .info { background: rgba(33, 150, 243, 0.3); }
        
        .test-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            margin: 5px;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        button:active {
            transform: translateY(0);
        }
        
        input, textarea {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 16px;
        }
        
        #messages {
            height: 300px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .message {
            margin: 8px 0;
            padding: 8px 12px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-left: 4px solid #4CAF50;
        }
        
        .timestamp {
            font-size: 0.8em;
            opacity: 0.7;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        
        @media (max-width: 600px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Symplle Chat System Test</h1>
        
        <div id="connectionStatus" class="status disconnected">
            ❌ Disconnected
        </div>
        
        <div class="test-section">
            <h3>📡 Connection Tests</h3>
            <div class="grid">
                <button onclick="connect()">🔌 Connect</button>
                <button onclick="disconnect()">❌ Disconnect</button>
                <button onclick="ping()">🏓 Ping Server</button>
                <button onclick="getServerInfo()">ℹ️ Server Info</button>
            </div>
        </div>
        
        <div class="test-section">
            <h3>🏠 Room Tests</h3>
            <input type="number" id="roomId" placeholder="Room ID" value="1">
            <input type="text" id="username" placeholder="Username" value="TestUser">
            <div class="grid">
                <button onclick="joinRoom()">👥 Join Room</button>
                <button onclick="leaveRoom()">👋 Leave Room</button>
                <button onclick="getRoomInfo()">📋 Room Info</button>
                <button onclick="startTyping()">⌨️ Start Typing</button>
            </div>
        </div>
        
        <div class="test-section">
            <h3>💬 Message Tests</h3>
            <textarea id="messageContent" placeholder="Type your message here..." rows="3">Hello from Symplle Chat System! 🚀</textarea>
            <button onclick="sendMessage()" style="width: 100%; margin: 10px 0;">📤 Send Message</button>
        </div>
        
        <div class="test-section">
            <h3>📨 Messages & Events</h3>
            <div id="messages"></div>
            <button onclick="clearMessages()" style="background: linear-gradient(45deg, #f44336, #d32f2f);">🗑️ Clear Messages</button>
        </div>
    </div>

    <script>
        let socket = null;
        
        function addMessage(type, content, data = null) {
            const messages = document.getElementById('messages');
            const timestamp = new Date().toLocaleTimeString();
            const message = document.createElement('div');
            message.className = 'message';
            
            let dataStr = data ? `\\n📊 Data: ${JSON.stringify(data, null, 2)}` : '';
            message.innerHTML = `
                <strong>${type}:</strong> ${content}${dataStr}
                <div class="timestamp">⏰ ${timestamp}</div>
            `;
            
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function updateStatus(connected, message) {
            const status = document.getElementById('connectionStatus');
            status.className = `status ${connected ? 'connected' : 'disconnected'}`;
            status.textContent = `${connected ? '✅' : '❌'} ${message}`;
        }
        
        function connect() {
            if (socket && socket.connected) {
                addMessage('⚠️ Warning', 'Already connected');
                return;
            }
            
            socket = io();
            
            socket.on('connect', () => {
                addMessage('🔌 Connected', 'Successfully connected to Symplle Chat System!');
                updateStatus(true, 'Connected to Chat System');
            });
            
            socket.on('disconnect', () => {
                addMessage('❌ Disconnected', 'Disconnected from server');
                updateStatus(false, 'Disconnected');
            });
            
            socket.on('status', (data) => {
                addMessage('📡 Status', 'Server status received', data);
            });
            
            socket.on('pong', (data) => {
                addMessage('🏓 Pong', 'Server responded to ping', data);
            });
            
            socket.on('room_joined', (data) => {
                addMessage('👥 Room Joined', 'Successfully joined room', data);
            });
            
            socket.on('room_left', (data) => {
                addMessage('👋 Room Left', 'Left room successfully', data);
            });
            
            socket.on('user_joined', (data) => {
                addMessage('👤 User Joined', `${data.username} joined the room`, data);
            });
            
            socket.on('user_left', (data) => {
                addMessage('👤 User Left', `${data.username} left the room`, data);
            });
            
            socket.on('new_message', (data) => {
                addMessage('💬 New Message', `${data.username}: ${data.content}`, data);
            });
            
            socket.on('message_sent', (data) => {
                addMessage('✅ Message Sent', 'Message delivered successfully', data);
            });
            
            socket.on('user_typing', (data) => {
                const action = data.typing ? 'started' : 'stopped';
                addMessage('⌨️ Typing', `${data.username} ${action} typing`, data);
            });
            
            socket.on('room_info', (data) => {
                addMessage('📋 Room Info', 'Room information received', data);
            });
            
            socket.on('error', (data) => {
                addMessage('❌ Error', 'Server error received', data);
            });
        }
        
        function disconnect() {
            if (socket) {
                socket.disconnect();
                socket = null;
                updateStatus(false, 'Manually disconnected');
                addMessage('❌ Disconnected', 'Manually disconnected from server');
            }
        }
        
        function ping() {
            if (!socket || !socket.connected) {
                addMessage('❌ Error', 'Not connected to server');
                return;
            }
            
            socket.emit('ping');
            addMessage('🏓 Ping', 'Sent ping to server');
        }
        
        function joinRoom() {
            if (!socket || !socket.connected) {
                addMessage('❌ Error', 'Not connected to server');
                return;
            }
            
            const roomId = document.getElementById('roomId').value;
            const username = document.getElementById('username').value;
            
            if (!roomId || !username) {
                addMessage('❌ Error', 'Please enter room ID and username');
                return;
            }
            
            socket.emit('join_room', {
                room_id: parseInt(roomId),
                username: username
            });
            
            addMessage('👥 Joining', `Attempting to join room ${roomId} as ${username}`);
        }
        
        function leaveRoom() {
            if (!socket || !socket.connected) {
                addMessage('❌ Error', 'Not connected to server');
                return;
            }
            
            const roomId = document.getElementById('roomId').value;
            const username = document.getElementById('username').value;
            
            socket.emit('leave_room', {
                room_id: parseInt(roomId),
                username: username
            });
            
            addMessage('👋 Leaving', `Leaving room ${roomId}`);
        }
        
        function sendMessage() {
            if (!socket || !socket.connected) {
                addMessage('❌ Error', 'Not connected to server');
                return;
            }
            
            const roomId = document.getElementById('roomId').value;
            const username = document.getElementById('username').value;
            const content = document.getElementById('messageContent').value;
            
            if (!roomId || !username || !content) {
                addMessage('❌ Error', 'Please fill all fields');
                return;
            }
            
            socket.emit('send_message', {
                room_id: parseInt(roomId),
                username: username,
                content: content,
                type: 'text'
            });
            
            addMessage('📤 Sending', `Sending message to room ${roomId}: "${content}"`);
        }
        
        function startTyping() {
            if (!socket || !socket.connected) {
                addMessage('❌ Error', 'Not connected to server');
                return;
            }
            
            const roomId = document.getElementById('roomId').value;
            const username = document.getElementById('username').value;
            
            socket.emit('typing_start', {
                room_id: parseInt(roomId),
                username: username
            });
            
            addMessage('⌨️ Typing', 'Started typing indicator');
            
            // Stop typing after 3 seconds
            setTimeout(() => {
                socket.emit('typing_stop', {
                    room_id: parseInt(roomId),
                    username: username
                });
                addMessage('⌨️ Typing', 'Stopped typing indicator');
            }, 3000);
        }
        
        function getRoomInfo() {
            if (!socket || !socket.connected) {
                addMessage('❌ Error', 'Not connected to server');
                return;
            }
            
            const roomId = document.getElementById('roomId').value;
            
            socket.emit('get_room_info', {
                room_id: parseInt(roomId)
            });
            
            addMessage('📋 Requesting', `Getting info for room ${roomId}`);
        }
        
        function clearMessages() {
            document.getElementById('messages').innerHTML = '';
        }
        
        function getServerInfo() {
            // Test REST API endpoints
            fetch('/api/chat/info')
                .then(response => response.json())
                .then(data => {
                    addMessage('ℹ️ Server Info', 'Chat system information', data);
                })
                .catch(error => {
                    addMessage('❌ Error', 'Failed to get server info', error);
                });
        }
        
        // Auto-connect on page load
        window.onload = function() {
            addMessage('🚀 Welcome', 'Symplle Chat System WebSocket Test Page loaded');
            addMessage('💡 Tip', 'Click "Connect" to start testing the chat system');
        };
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print("\n🚀 SYMPLLE API STARTING...")
    print(f"📁 Main location: src/")
    print(f"🌍 i18n Support: {'✅ PT-BR, EN-US, ES-ES' if I18N_AVAILABLE else '❌ Not available'}")
    print(f"💬 Chat System: {'✅ Real-time chat available' if CHAT_AVAILABLE else '❌ Not available'}")
    print(f"🗄️  Database: {db_path}")
    print(f"🔐 CORS Enabled")
    print(f"📱 API Version: v1.0.0-i18n-chat-src")
    
    if I18N_AVAILABLE:
        print("\n📋 ENDPOINTS i18n:")
        print("   GET  /api/i18n/info        - Informações i18n")
        print("   POST /api/i18n/change-locale - Mudar idioma")
        print("   GET  /api/i18n/demo        - Demo i18n/L10n")
    
    if CHAT_AVAILABLE:
        print("\n💬 ENDPOINTS Chat System:")
        print("   GET  /api/chat/info        - Informações chat")
        print("   POST /api/chat/rooms       - Criar room")
        print("   GET  /api/chat/rooms       - Listar rooms")
        print("   WS   /socket.io/           - WebSocket connection")
        
        print("\n🧪 Teste chat API:")
        print("   curl http://localhost:5000/api/chat/info")
    
    if I18N_AVAILABLE:
        print("\n🌐 Teste mudar idioma:")
        print("   curl -X POST http://localhost:5000/api/i18n/change-locale \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"locale\": \"pt_BR\"}'")
    
    print("\n✨ READY! Server starting on http://localhost:5000")
    print("   Execute de: src/ directory")
    print("\n")
    
    with app.app_context():
        db.create_all()  # Criar tabelas no banco de dados
    
    # 💬 CHAT SYSTEM: Usar socketio.run se disponível, senão app.run
    if CHAT_AVAILABLE and socketio:
        print("🚀 Starting with SocketIO support...")
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    else:
        print("🚀 Starting without SocketIO support...")
        app.run(host='0.0.0.0', port=5000, debug=True)