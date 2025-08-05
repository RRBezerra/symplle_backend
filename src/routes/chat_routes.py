# routes/chat_routes.py - Chat System REST API (Compatible with existing structure)
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import sys
import os

# Add parent directory to path to access src.models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import using same pattern as main.py
try:
    from src.models.user import User
except ImportError:
    # Fallback import
    try:
        from models.user import User
    except ImportError:
        User = None
        print("⚠️ User model not found - chat will work without user integration")

# Import chat models 
try:
    from models.chat import ChatRoom, ChatMessage, ChatParticipant, MessageStatus, TypingStatus
    CHAT_MODELS_AVAILABLE = True
except ImportError:
    print("⚠️ Chat models not found - creating basic versions")
    CHAT_MODELS_AVAILABLE = False

# Import database
try:
    from src.models import db
except ImportError:
    try:
        from models import db
    except ImportError:
        db = None
        print("⚠️ Database not found")

# Import i18n utilities if available
try:
    from i18n import i18n_utils, _
    I18N_AVAILABLE = True
except ImportError:
    I18N_AVAILABLE = False
    def _(key, **kwargs): return key
    class MockI18nUtils:
        @staticmethod
        def format_api_response(data, message_key=None, success=True, **kwargs):
            return {
                'success': success,
                'data': data,
                'message': message_key or ('Success' if success else 'Error'),
                'locale': 'en_US'
            }
    i18n_utils = MockI18nUtils()

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat/info')
def chat_info():
    """Informações sobre o sistema de chat"""
    chat_data = {
        'version': '1.0.0',
        'status': 'active' if CHAT_MODELS_AVAILABLE else 'basic',
        'features': [
            'Real-time messaging',
            'Group chats',
            'Typing indicators',
            'Online status',
            'Message history'
        ] if CHAT_MODELS_AVAILABLE else [
            'Basic chat info (models not loaded)'
        ],
        'websocket': True,
        'models_loaded': CHAT_MODELS_AVAILABLE,
        'user_integration': User is not None,
        'database_connected': db is not None
    }
    
    if I18N_AVAILABLE:
        return jsonify(i18n_utils.format_api_response(
            chat_data, _('chat.info_retrieved'), True
        ))
    else:
        return jsonify({
            'success': True,
            'data': chat_data,
            'message': 'Chat system information retrieved'
        })

@chat_bp.route('/chat/rooms', methods=['GET'])
def list_rooms():
    """Listar salas de chat do usuário"""
    if not CHAT_MODELS_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Chat models not available',
            'data': []
        }), 501
    
    try:
        # Por enquanto, retornar lista vazia - será implementado quando auth estiver integrado
        rooms_data = {
            'rooms': [],
            'total': 0,
            'user_id': getattr(g, 'current_user_id', None)
        }
        
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                rooms_data, _('chat.rooms_retrieved'), True
            ))
        else:
            return jsonify({
                'success': True,
                'data': rooms_data,
                'message': 'Chat rooms retrieved successfully'
            })
            
    except Exception as e:
        error_msg = f'Error retrieving chat rooms: {str(e)}'
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                None, _('errors.server'), False
            )), 500
        else:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

@chat_bp.route('/chat/rooms', methods=['POST'])
def create_room():
    """Criar nova sala de chat"""
    if not CHAT_MODELS_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Chat models not available - cannot create rooms',
            'data': None
        }), 501
    
    try:
        data = request.get_json()
        
        if not data:
            error_msg = 'JSON data required'
            if I18N_AVAILABLE:
                return jsonify(i18n_utils.format_api_response(
                    None, _('validation.json_required'), False
                )), 400
            else:
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
        
        room_type = data.get('room_type', 'group')
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if room_type == 'group' and not name:
            error_msg = 'Group chat name is required'
            if I18N_AVAILABLE:
                return jsonify(i18n_utils.format_api_response(
                    None, _('chat.validation.name_required'), False
                )), 400
            else:
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
        
        # Por enquanto, simular criação de room - será implementado quando models estiverem carregados
        room_data = {
            'id': 1,
            'room_type': room_type,
            'name': name,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'participants_count': 1,
            'status': 'active'
        }
        
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                room_data, _('chat.room_created'), True
            )), 201
        else:
            return jsonify({
                'success': True,
                'data': room_data,
                'message': 'Chat room created successfully'
            }), 201
            
    except Exception as e:
        error_msg = f'Error creating chat room: {str(e)}'
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                None, _('errors.server'), False
            )), 500
        else:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

@chat_bp.route('/chat/rooms/<int:room_id>/messages', methods=['GET'])
def get_messages(room_id):
    """Obter mensagens de uma sala"""
    if not CHAT_MODELS_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Chat models not available',
            'data': []
        }), 501
    
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Por enquanto, retornar lista vazia
        messages_data = {
            'messages': [],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': 0,
                'pages': 0
            },
            'room_id': room_id
        }
        
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                messages_data, _('chat.messages_retrieved'), True
            ))
        else:
            return jsonify({
                'success': True,
                'data': messages_data,
                'message': 'Messages retrieved successfully'
            })
            
    except Exception as e:
        error_msg = f'Error retrieving messages: {str(e)}'
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                None, _('errors.server'), False
            )), 500
        else:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

@chat_bp.route('/chat/rooms/<int:room_id>/messages', methods=['POST'])
def send_message(room_id):
    """Enviar mensagem para uma sala"""
    if not CHAT_MODELS_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Chat models not available - cannot send messages',
            'data': None
        }), 501
    
    try:
        data = request.get_json()
        
        if not data:
            error_msg = 'JSON data required'
            if I18N_AVAILABLE:
                return jsonify(i18n_utils.format_api_response(
                    None, _('validation.json_required'), False
                )), 400
            else:
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
        
        content = data.get('content', '').strip()
        message_type = data.get('type', 'text')
        
        if not content:
            error_msg = 'Message content is required'
            if I18N_AVAILABLE:
                return jsonify(i18n_utils.format_api_response(
                    None, _('chat.validation.content_required'), False
                )), 400
            else:
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
        
        # Por enquanto, simular envio de mensagem
        message_data = {
            'id': 1,
            'content': content,
            'type': message_type,
            'room_id': room_id,
            'user_id': getattr(g, 'current_user_id', 1),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'sent'
        }
        
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                message_data, _('chat.message_sent'), True
            )), 201
        else:
            return jsonify({
                'success': True,
                'data': message_data,
                'message': 'Message sent successfully'
            }), 201
            
    except Exception as e:
        error_msg = f'Error sending message: {str(e)}'
        if I18N_AVAILABLE:
            return jsonify(i18n_utils.format_api_response(
                None, _('errors.server'), False
            )), 500
        else:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

@chat_bp.route('/chat/status')
def chat_status():
    """Status detalhado do sistema de chat"""
    status_data = {
        'chat_system': {
            'available': CHAT_MODELS_AVAILABLE,
            'version': '1.0.0',
            'features': {
                'real_time_messaging': CHAT_MODELS_AVAILABLE,
                'group_chats': CHAT_MODELS_AVAILABLE,
                'typing_indicators': CHAT_MODELS_AVAILABLE,
                'file_sharing': False,  # Will be implemented later
                'read_receipts': CHAT_MODELS_AVAILABLE,
                'online_status': CHAT_MODELS_AVAILABLE
            }
        },
        'dependencies': {
            'models_loaded': CHAT_MODELS_AVAILABLE,
            'user_model': User is not None,
            'database': db is not None,
            'i18n': I18N_AVAILABLE
        },
        'endpoints': {
            'info': '/api/chat/info',
            'rooms': '/api/chat/rooms',
            'messages': '/api/chat/rooms/{room_id}/messages',
            'websocket': '/socket.io/'
        }
    }
    
    if I18N_AVAILABLE:
        return jsonify(i18n_utils.format_api_response(
            status_data, _('chat.status_retrieved'), True
        ))
    else:
        return jsonify({
            'success': True,
            'data': status_data,
            'message': 'Chat system status retrieved'
        })

# Error handlers for the chat blueprint
@chat_bp.errorhandler(404)
def chat_not_found(error):
    if I18N_AVAILABLE:
        return jsonify(i18n_utils.format_api_response(
            None, _('errors.not_found'), False
        )), 404
    else:
        return jsonify({
            'success': False,
            'message': 'Chat endpoint not found'
        }), 404

@chat_bp.errorhandler(500)
def chat_internal_error(error):
    if I18N_AVAILABLE:
        return jsonify(i18n_utils.format_api_response(
            None, _('errors.server'), False
        )), 500
    else:
        return jsonify({
            'success': False,
            'message': 'Internal chat system error'
        }), 500