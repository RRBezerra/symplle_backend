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
    """Health check com informações de segurança e i18n"""
    try:
        # Verificar conexão com banco
        db.session.execute(db.text('SELECT 1'))
        
        health_data = {
            'status': 'healthy',
            'version': '1.0.0-jwt-i18n-src',
            'database': 'connected',
            'security': 'jwt-enabled',
            'i18n': I18N_AVAILABLE,
            'current_locale': getattr(g, 'locale', 'en_US') if I18N_AVAILABLE else 'en_US',
            'features': ['JWT Auth', 'Security Headers'] + (['i18n/L10n'] if I18N_AVAILABLE else []),
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
                'message': 'System healthy (basic mode)'
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
    if I18N_AVAILABLE:
        return jsonify(i18n_utils.format_api_response({
            'app': _('app.name'),
            'message': _('app.welcome'),
            'version': '1.0.0-i18n-src',
            'main_location': 'src/',
            'endpoints': {
                'auth': '/api/auth',
                'i18n': '/api/i18n',
                'health': '/health'
            }
        }, _('app.welcome')))
    else:
        return jsonify({
            "message": "Symplle API is running with JWT!",
            "version": "1.0.0-basic-src",
            "main_location": "src/",
            "i18n": "not available"
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

if __name__ == '__main__':
    print("\n🚀 SYMPLLE API STARTING...")
    print(f"📁 Main location: src/")
    print(f"🌍 i18n Support: {'✅ PT-BR, EN-US, ES-ES' if I18N_AVAILABLE else '❌ Not available'}")
    print(f"🗄️  Database: {db_path}")
    print(f"🔐 CORS Enabled")
    print(f"📱 API Version: v1.0.0-i18n-src")
    
    if I18N_AVAILABLE:
        print("\n📋 NOVOS ENDPOINTS i18n:")
        print("   GET  /api/i18n/info        - Informações i18n")
        print("   POST /api/i18n/change-locale - Mudar idioma")
        print("   GET  /api/i18n/demo        - Demo i18n/L10n")
        print("\n🌐 Teste mudar idioma:")
        print("   curl -X POST http://localhost:5000/api/i18n/change-locale \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"locale\": \"pt_BR\"}'")
    
    print("\n✨ READY! Server starting on http://localhost:5000")
    print("   Execute de: src/ directory")
    print("\n")
    
    with app.app_context():
        db.create_all()  # Criar tabelas no banco de dados
    app.run(host='0.0.0.0', port=5000, debug=True)