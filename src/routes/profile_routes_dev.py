from flask import Blueprint, request, jsonify
from src.models import db
from src.models.user import User
import random
import string
import os
from werkzeug.utils import secure_filename

profile_routes = Blueprint('profile_routes', __name__)

# Configuração para upload de imagens
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_routes.route('/api/create-profile', methods=['POST'])
def create_profile():
    """Cria o perfil do usuário com nome e foto"""
    
    # Verificar se é um formulário multipart (com imagem) ou JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Formulário multipart
        email = request.form.get('email')
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Verificar se há arquivo de imagem
        profile_image_path = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Gerar nome único para o arquivo
                unique_filename = f"{username}_{random.randint(1000, 9999)}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                profile_image_path = f"/uploads/{unique_filename}"
    else:
        # JSON
        data = request.json
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        profile_image_path = None
    
    # Validar dados obrigatórios
    if not all([email, username, first_name, last_name]):
        return jsonify({
            'success': False,
            'message': 'Dados incompletos para criação do perfil'
        }), 400
    
    try:
        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Atualizar usuário existente
            existing_user.username = username
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            if profile_image_path:
                existing_user.profile_image = profile_image_path
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Perfil atualizado com sucesso',
                'user_id': existing_user.id
            })
        
        # Criar novo usuário
        new_user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            profile_image=profile_image_path
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Perfil criado com sucesso',
            'user_id': new_user.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao criar perfil: {str(e)}'
        }), 500
