# src/routes/upload_routes.py
"""
Upload Routes para Symplle
Endpoints básicos para upload de arquivos
VERSÃO SIMPLIFICADA - SEM DEPENDÊNCIAS EXTERNAS
"""

import os
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# ✅ Criar blueprint (SEMPRE PRESENTE)
upload_bp = Blueprint('upload', __name__)

# Configurações básicas
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Criar diretório de uploads se não existir
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'avatars'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'posts'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'documents'), exist_ok=True)

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Obtém tamanho do arquivo"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

@upload_bp.route('/api/upload/info', methods=['GET'])
def upload_info():
    """Informações sobre o sistema de upload"""
    try:
        info_data = {
            'upload_system': 'active',
            'version': '1.0.0-basic',
            'max_file_size': f"{MAX_FILE_SIZE // (1024*1024)}MB",
            'allowed_extensions': list(ALLOWED_EXTENSIONS),
            'supported_categories': ['avatars', 'posts', 'documents'],
            'upload_directory': UPLOAD_DIR
        }
        
        return jsonify({
            "success": True,
            "message": "Upload system information",
            "data": info_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@upload_bp.route('/api/upload/avatar', methods=['POST'])
def upload_avatar():
    """Upload básico de avatar"""
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "No file provided"
            }), 400
        
        file = request.files['file']
        user_id = request.form.get('user_id', '1')
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Verificar tamanho
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "message": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
            }), 400
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        unique_filename = f"user_{user_id}_avatar_{filename}"
        file_path = os.path.join(UPLOAD_DIR, 'avatars', unique_filename)
        
        file.save(file_path)
        
        # URL para acessar o arquivo
        file_url = f"/uploads/avatars/{unique_filename}"
        
        response_data = {
            'user_id': int(user_id),
            'avatar_url': file_url,
            'filename': unique_filename,
            'file_size': file_size,
            'file_path': file_path
        }
        
        return jsonify({
            "success": True,
            "message": "Avatar uploaded successfully",
            "data": response_data
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Upload error: {str(e)}"
        }), 500

@upload_bp.route('/api/upload/document', methods=['POST'])
def upload_document():
    """Upload básico de documento"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "No file provided"
            }), 400
        
        file = request.files['file']
        user_id = request.form.get('user_id', '1')
        doc_type = request.form.get('document_type', 'general')
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Verificar tamanho
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "message": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
            }), 400
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        unique_filename = f"user_{user_id}_{doc_type}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, 'documents', unique_filename)
        
        file.save(file_path)
        
        # URL para acessar o arquivo
        file_url = f"/uploads/documents/{unique_filename}"
        
        response_data = {
            'user_id': int(user_id),
            'document_url': file_url,
            'document_type': doc_type,
            'filename': unique_filename,
            'file_size': file_size,
            'file_path': file_path
        }
        
        return jsonify({
            "success": True,
            "message": "Document uploaded successfully",
            "data": response_data
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Upload error: {str(e)}"
        }), 500

@upload_bp.route('/api/upload/post-image', methods=['POST'])
def upload_post_image():
    """Upload básico de imagem para post"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "No file provided"
            }), 400
        
        file = request.files['file']
        user_id = request.form.get('user_id', '1')
        post_id = request.form.get('post_id', 'new')
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Verificar tamanho
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "message": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
            }), 400
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        unique_filename = f"user_{user_id}_post_{post_id}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, 'posts', unique_filename)
        
        file.save(file_path)
        
        # URL para acessar o arquivo
        file_url = f"/uploads/posts/{unique_filename}"
        
        response_data = {
            'user_id': int(user_id),
            'post_id': post_id,
            'image_url': file_url,
            'filename': unique_filename,
            'file_size': file_size,
            'file_path': file_path
        }
        
        return jsonify({
            "success": True,
            "message": "Post image uploaded successfully",
            "data": response_data
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Upload error: {str(e)}"
        }), 500

@upload_bp.route('/api/upload/files/<int:user_id>', methods=['GET'])
def list_user_files(user_id):
    """Lista arquivos de um usuário"""
    try:
        category = request.args.get('category', 'all')
        
        user_files = []
        
        # Procurar arquivos do usuário em todas as categorias
        categories = ['avatars', 'posts', 'documents'] if category == 'all' else [category]
        
        for cat in categories:
            cat_path = os.path.join(UPLOAD_DIR, cat)
            if os.path.exists(cat_path):
                for filename in os.listdir(cat_path):
                    if filename.startswith(f"user_{user_id}_"):
                        file_path = os.path.join(cat_path, filename)
                        file_stats = os.stat(file_path)
                        
                        user_files.append({
                            'filename': filename,
                            'category': cat,
                            'file_size': file_stats.st_size,
                            'url': f"/uploads/{cat}/{filename}",
                            'created_at': file_stats.st_mtime
                        })
        
        return jsonify({
            "success": True,
            "message": "User files retrieved",
            "data": {
                'user_id': user_id,
                'category': category,
                'files_count': len(user_files),
                'files': user_files
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

# Servir arquivos estáticos
@upload_bp.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve arquivos enviados"""
    try:
        # Dividir caminho para obter categoria e nome do arquivo
        path_parts = filename.split('/')
        if len(path_parts) >= 2:
            category = path_parts[0]
            file_name = '/'.join(path_parts[1:])
            category_path = os.path.join(UPLOAD_DIR, category)
            
            if os.path.exists(os.path.join(category_path, file_name)):
                return send_from_directory(category_path, file_name)
        
        # Fallback: servir diretamente do uploads
        return send_from_directory(UPLOAD_DIR, filename)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "File not found"
        }), 404