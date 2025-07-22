# src/routes/timeline_routes.py
"""
Rotas específicas para Timeline personalizada
Endpoints: timeline principal, trending, descobrir
"""

from flask import Blueprint, request, jsonify, g

# ✅ CORRIGIDO: Imports absolutos
from services.timeline_service import timeline_service

# Import de auth - com fallback se não existir
try:
    from middleware.auth_middleware import auth_required
    AUTH_AVAILABLE = True
except ImportError:
    # Fallback: decorator que não faz nada por enquanto
    def auth_required(f):
        def decorated_function(*args, **kwargs):
            # Simular usuário logado para testes
            from flask import g
            class MockUser:
                id = 1
                username = "test_user"
            g.current_user = MockUser()
            return f(*args, **kwargs)
        return decorated_function
    AUTH_AVAILABLE = False
    print("⚠️ Auth middleware não encontrado - usando mock para desenvolvimento")

# Import i18n
try:
    from i18n import i18n_utils, _
    I18N_AVAILABLE = True
except ImportError:
    I18N_AVAILABLE = False
    def _(text, **kwargs): return text.format(**kwargs) if kwargs else text
    def i18n_utils_format_api_response(data, message, success):
        return {"success": success, "message": message, "data": data}
    class i18n_utils:
        @staticmethod
        def format_api_response(data, message, success):
            return {"success": success, "message": message, "data": data}

# Criar blueprint
timeline_bp = Blueprint('timeline', __name__)

@timeline_bp.route('/api/timeline', methods=['GET'])
@auth_required
def get_timeline():
    """
    Timeline personalizada do usuário
    Query params:
    - algorithm: smart|chronological|popular (default: smart)
    - limit: número de posts (default: 20, max: 100)
    - offset: pular posts (paginação)
    """
    try:
        user_id = g.current_user.id
        
        # Parâmetros
        algorithm = request.args.get('algorithm', 'smart')
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Gerar timeline
        timeline_data = timeline_service.get_user_timeline(
            user_id=user_id,
            limit=limit,
            offset=offset,
            algorithm=algorithm
        )
        
        return jsonify(i18n_utils.format_api_response(
            timeline_data, _('timeline.success'), True
        ) if I18N_AVAILABLE else {
            "success": True,
            "message": "Timeline loaded successfully",
            "data": timeline_data
        }), 200
        
    except Exception as e:
        return jsonify(i18n_utils.format_api_response(
            None, _('posts.error.unexpected', error=str(e)), False
        ) if I18N_AVAILABLE else {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500

@timeline_bp.route('/api/timeline/trending', methods=['GET'])
@auth_required
def get_trending():
    """
    Posts em alta (trending)
    Query params:
    - limit: número de posts (default: 10, max: 50)
    """
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Buscar trending posts
        trending_data = timeline_service.get_trending_posts(limit=limit)
        
        return jsonify(i18n_utils.format_api_response(
            trending_data, _('timeline.success'), True
        ) if I18N_AVAILABLE else {
            "success": True,
            "message": "Trending posts loaded successfully",
            "data": trending_data
        }), 200
        
    except Exception as e:
        return jsonify(i18n_utils.format_api_response(
            None, _('posts.error.unexpected', error=str(e)), False
        ) if I18N_AVAILABLE else {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500

@timeline_bp.route('/api/timeline/algorithms', methods=['GET'])
def get_timeline_algorithms():
    """
    Lista de algoritmos disponíveis para timeline
    """
    try:
        algorithms = {
            'smart': {
                'name': _('timeline.algorithms.smart') if I18N_AVAILABLE else 'Smart Timeline',
                'description': 'Algoritmo inteligente baseado em relevância e engajamento',
                'factors': ['engagement', 'recency', 'content_type', 'author_relevance']
            },
            'chronological': {
                'name': _('timeline.algorithms.chronological') if I18N_AVAILABLE else 'Chronological',
                'description': 'Ordem cronológica (mais recente primeiro)',
                'factors': ['created_at']
            },
            'popular': {
                'name': _('timeline.algorithms.popular') if I18N_AVAILABLE else 'Popular',
                'description': 'Posts com mais curtidas e comentários',
                'factors': ['likes_count', 'comments_count', 'shares_count']
            }
        }
        
        return jsonify(i18n_utils.format_api_response(
            {'algorithms': algorithms}, _('timeline.success'), True
        ) if I18N_AVAILABLE else {
            "success": True,
            "message": "Timeline algorithms retrieved",
            "data": {'algorithms': algorithms}
        }), 200
        
    except Exception as e:
        return jsonify(i18n_utils.format_api_response(
            None, _('posts.error.unexpected', error=str(e)), False
        ) if I18N_AVAILABLE else {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500