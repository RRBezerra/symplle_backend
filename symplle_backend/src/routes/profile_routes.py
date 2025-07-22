# Implementação de Popup de Confirmação no Signup Screen

from flask import Blueprint, request, jsonify
from src.models import db
from src.models.user import User

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/users', methods=['POST'])
def create_user():
    """Criar um novo usuário"""
    try:
        data = request.json
        
        # Validar dados obrigatórios
        required_fields = ['username', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} é obrigatório'
                }), 400
        
        # Verificar se email já existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email já está em uso'
            }), 400
        
        # Verificar se username já existe
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({
                'success': False,
                'message': 'Username já está em uso'
            }), 400
        
        # Criar novo usuário
        new_user = User(
            username=data['username'],
            email=data['email'],
            phone=data.get('phone'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            profile_image=data.get('profile_image')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@profile_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Atualizar dados do usuário"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
        
        data = request.json
        
        # Atualizar campos permitidos
        allowed_fields = ['first_name', 'last_name', 'profile_image', 'phone']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Marcar email como verificado se fornecido
        if data.get('email_verified'):
            user.email_verified = True
        
        # Marcar telefone como verificado se fornecido
        if data.get('phone_verified'):
            user.phone_verified = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário atualizado com sucesso',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@profile_bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Obter dados do usuário"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@profile_bp.route('/create-profile', methods=['POST'])
def create_profile():
    """Criar/atualizar perfil do usuário - endpoint para compatibilidade"""
    try:
        data = request.json
        print(f"📝 create-profile chamado com dados: {data}")
        
        # Validar dados obrigatórios
        email = data.get('email')
        username = data.get('username') 
        first_name = data.get('first_name')
        last_name = data.get('last_name', '')
        
        if not email or not username:
            return jsonify({
                'success': False,
                'message': 'Email e username são obrigatórios'
            }), 400
        
        # Buscar usuário existente por email
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Atualizar usuário existente
            print(f"👤 Atualizando perfil do usuário: {user.username}")
            
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
                
            # Marcar como verificado
            user.email_verified = True
            user.phone_verified = True
            
            db.session.commit()
            
            print(f"✅ Perfil atualizado com sucesso para: {user.username}")
            return jsonify({
                'success': True,
                'message': 'Perfil atualizado com sucesso',
                'user': user.to_dict()
            })
        else:
            # Usuário não encontrado - criar novo
            print(f"➕ Criando novo usuário: {username}")
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            
            # Marcar como verificado
            new_user.email_verified = True
            new_user.phone_verified = True
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ Novo usuário criado: {username}")
            return jsonify({
                'success': True,
                'message': 'Perfil criado com sucesso',
                'user': new_user.to_dict()
            })
        
    except Exception as e:
        print(f"❌ Erro ao criar/atualizar perfil: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

