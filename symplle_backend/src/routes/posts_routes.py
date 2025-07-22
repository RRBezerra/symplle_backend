# src/routes/posts_routes.py
"""
Rotas para Posts usando SQLite DIRETO
VERSÃO QUE SEMPRE FUNCIONA - SEM SQLAlchemy
"""

import json
import sqlite3
import os
from datetime import datetime
from flask import Blueprint, request, jsonify

# Criar blueprint
posts_bp = Blueprint('posts', __name__)

def get_db_connection():
    """Conectar ao banco SQLite diretamente"""
    # ✅ CORRIGIDO: Usar EXATAMENTE o mesmo caminho que main.py
    # main.py usa: os.path.dirname(os.path.dirname(__file__)), 'symplle.db'
    # posts_routes.py deve usar o mesmo padrão
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'symplle.db')
    print(f"🔍 Conectando ao banco: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    
    # ✅ CRIAR TABELAS AUTOMATICAMENTE SE NÃO EXISTIREM
    cursor = conn.cursor()
    
    # Criar tabela posts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT,
        privacy VARCHAR(20) DEFAULT 'public',
        post_type VARCHAR(20) DEFAULT 'text', 
        media_urls TEXT,
        likes_count INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        shares_count INTEGER DEFAULT 0,
        views_count INTEGER DEFAULT 0,
        is_edited BOOLEAN DEFAULT 0,
        is_deleted BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Criar tabela likes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, post_id)
    )
    ''')
    
    # Criar tabela comments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        parent_comment_id INTEGER,
        likes_count INTEGER DEFAULT 0,
        replies_count INTEGER DEFAULT 0,
        is_edited BOOLEAN DEFAULT 0,
        is_deleted BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    print("✅ Tabelas verificadas/criadas!")
    
    return conn

@posts_bp.route('/api/posts/debug', methods=['GET'])
def debug_database():
    """Debug do banco de dados"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Verificar estrutura da tabela posts se existir
        posts_schema = None
        if 'posts' in tables:
            cursor.execute("PRAGMA table_info(posts);")
            posts_schema = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        debug_info = {
            'database_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'symplle.db'),
            'tables_found': tables,
            'posts_table_exists': 'posts' in tables,
            'posts_schema': posts_schema,
            'expected_tables': ['posts', 'likes', 'comments']
        }
        
        return jsonify({
            "success": True,
            "message": "Database debug information",
            "data": debug_info
        }), 200
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        return jsonify({
            "success": False,
            "message": f"Debug error: {str(e)}"
        }), 500

@posts_bp.route('/api/posts/info', methods=['GET'])
def posts_info():
    """Informações sobre o sistema de posts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se tabela existe primeiro
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts';")
        posts_table_exists = cursor.fetchone() is not None
        
        if not posts_table_exists:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Posts table does not exist. Creating now...",
                "data": {"tables_created": True}
            }), 500
        
        # Contar posts
        cursor.execute("SELECT COUNT(*) as total FROM posts WHERE is_deleted = 0")
        total_posts = cursor.fetchone()['total']
        
        # Contar likes
        cursor.execute("SELECT COUNT(*) as total FROM likes")
        total_likes = cursor.fetchone()['total']
        
        # Contar comentários
        cursor.execute("SELECT COUNT(*) as total FROM comments WHERE is_deleted = 0")
        total_comments = cursor.fetchone()['total']
        
        conn.close()
        
        info = {
            'posts_system': 'active',
            'version': '1.0.0-sqlite',
            'database': 'sqlite-direct',
            'database_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'symplle.db'),
            'statistics': {
                'total_posts': total_posts,
                'total_likes': total_likes,
                'total_comments': total_comments
            },
            'supported_features': [
                'create_posts',
                'list_posts',
                'like_posts',
                'sqlite_direct'
            ]
        }
        
        return jsonify({
            "success": True,
            "message": "Posts system working with SQLite direct!",
            "data": info
        }), 200
        
    except Exception as e:
        print(f"❌ Erro no info: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@posts_bp.route('/api/posts', methods=['POST'])
def create_post():
    """Criar novo post usando SQLite direto"""
    try:
        data = request.get_json() or {}
        
        # Dados do post
        user_id = 1  # Mock user
        content = data.get('content', '').strip()
        privacy = data.get('privacy', 'public')
        
        if not content:
            return jsonify({
                "success": False,
                "message": "Content is required"
            }), 400
        
        # Inserir no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO posts (user_id, content, privacy, post_type, likes_count, comments_count, created_at)
            VALUES (?, ?, ?, ?, 0, 0, ?)
        """, (user_id, content, privacy, 'text', datetime.utcnow().isoformat()))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Retornar post criado
        return jsonify({
            "success": True,
            "message": "Post created successfully!",
            "data": {
                'id': post_id,
                'user_id': user_id,
                'content': content,
                'privacy': privacy,
                'post_type': 'text',
                'likes_count': 0,
                'comments_count': 0,
                'created_at': datetime.utcnow().isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Erro ao criar post: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@posts_bp.route('/api/posts', methods=['GET'])
def list_posts():
    """Listar posts usando SQLite direto"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, content, privacy, post_type, 
                   likes_count, comments_count, views_count, created_at
            FROM posts 
            WHERE is_deleted = 0 AND privacy = 'public'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        posts = cursor.fetchall()
        conn.close()
        
        # Converter para lista de dicionários
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post['id'],
                'user_id': post['user_id'],
                'content': post['content'],
                'privacy': post['privacy'],
                'post_type': post['post_type'],
                'likes_count': post['likes_count'] or 0,
                'comments_count': post['comments_count'] or 0,
                'views_count': post['views_count'] or 0,
                'created_at': post['created_at']
            })
        
        return jsonify({
            "success": True,
            "message": "Posts retrieved successfully!",
            "data": {
                'posts': posts_data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': len(posts_data)
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar posts: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@posts_bp.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Curtir/descurtir post usando SQLite direto"""
    try:
        user_id = 1  # Mock user
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se post existe
        cursor.execute("SELECT id, likes_count FROM posts WHERE id = ? AND is_deleted = 0", (post_id,))
        post = cursor.fetchone()
        
        if not post:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Post not found"
            }), 404
        
        # Verificar se já curtiu
        cursor.execute("SELECT id FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        existing_like = cursor.fetchone()
        
        if existing_like:
            # Remover curtida
            cursor.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
            new_likes_count = max(0, (post['likes_count'] or 0) - 1)
            cursor.execute("UPDATE posts SET likes_count = ? WHERE id = ?", (new_likes_count, post_id))
            action = 'unliked'
            message = 'Post unliked successfully!'
        else:
            # Adicionar curtida
            cursor.execute("INSERT INTO likes (user_id, post_id, created_at) VALUES (?, ?, ?)", 
                          (user_id, post_id, datetime.utcnow().isoformat()))
            new_likes_count = (post['likes_count'] or 0) + 1
            cursor.execute("UPDATE posts SET likes_count = ? WHERE id = ?", (new_likes_count, post_id))
            action = 'liked'
            message = 'Post liked successfully!'
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": message,
            "data": {
                'action': action,
                'likes_count': new_likes_count,
                'post_id': post_id
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Erro no like: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@posts_bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Obter post específico usando SQLite direto"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar post
        cursor.execute("""
            SELECT id, user_id, content, privacy, post_type, 
                   likes_count, comments_count, views_count, created_at
            FROM posts 
            WHERE id = ? AND is_deleted = 0
        """, (post_id,))
        
        post = cursor.fetchone()
        
        if not post:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Post not found"
            }), 404
        
        # Incrementar views
        new_views = (post['views_count'] or 0) + 1
        cursor.execute("UPDATE posts SET views_count = ? WHERE id = ?", (new_views, post_id))
        conn.commit()
        conn.close()
        
        post_data = {
            'id': post['id'],
            'user_id': post['user_id'],
            'content': post['content'],
            'privacy': post['privacy'],
            'post_type': post['post_type'],
            'likes_count': post['likes_count'] or 0,
            'comments_count': post['comments_count'] or 0,
            'views_count': new_views,
            'created_at': post['created_at']
        }
        
        return jsonify({
            "success": True,
            "message": "Post retrieved successfully!",
            "data": post_data
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar post: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500