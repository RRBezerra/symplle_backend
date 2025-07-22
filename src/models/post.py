# src/models/post.py
"""
Modelos para o sistema de Posts do Symplle
- Post: posts dos usuários (texto + mídia)
- Like: curtidas em posts
- Comment: comentários em posts
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from models import db
import enum

class PostPrivacy(enum.Enum):
    """Tipos de privacidade dos posts"""
    PUBLIC = "public"       # Visível para todos
    FRIENDS = "friends"     # Visível para quem segue
    PRIVATE = "private"     # Visível apenas para o autor

class PostType(enum.Enum):
    """Tipos de posts"""
    TEXT = "text"           # Apenas texto
    IMAGE = "image"         # Texto + imagens
    VIDEO = "video"         # Texto + vídeos
    MIXED = "mixed"         # Texto + imagens + vídeos

class Post(db.Model):
    """
    Modelo para posts dos usuários
    """
    __tablename__ = 'posts'
    
    # Campos básicos
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text)  # Conteúdo textual (pode ser vazio se só mídia)
    
    # Configurações
    privacy = Column(Enum(PostPrivacy), default=PostPrivacy.PUBLIC, nullable=False)
    post_type = Column(Enum(PostType), default=PostType.TEXT, nullable=False)
    
    # Mídia (JSON com URLs dos arquivos)
    media_urls = Column(Text)  # JSON string: ["url1.jpg", "url2.mp4"]
    
    # Contadores (cache para performance)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    
    # Metadados
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # Soft delete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="posts")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Post {self.id}: {self.content[:50]}>'
    
    def to_dict(self, include_user=True, include_stats=True):
        """Converte post para dicionário JSON"""
        import json
        
        data = {
            'id': self.id,
            'content': self.content,
            'privacy': self.privacy.value if self.privacy else 'public',
            'post_type': self.post_type.value if self.post_type else 'text',
            'media_urls': json.loads(self.media_urls) if self.media_urls else [],
            'is_edited': self.is_edited,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Incluir estatísticas
        if include_stats:
            data.update({
                'likes_count': self.likes_count,
                'comments_count': self.comments_count,
                'shares_count': self.shares_count,
                'views_count': self.views_count
            })
        
        # Incluir dados do usuário
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'name': f"{self.user.first_name} {self.user.last_name}".strip(),
                'avatar_url': getattr(self.user, 'avatar_url', None)
            }
        
        return data

class Like(db.Model):
    """
    Modelo para curtidas em posts
    """
    __tablename__ = 'likes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User")
    post = relationship("Post", back_populates="likes")
    
    # Constraint único: usuário só pode curtir uma vez
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )
    
    def __repr__(self):
        return f'<Like: User {self.user_id} → Post {self.post_id}>'
    
    def to_dict(self):
        """Converte like para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat()
        }

class Comment(db.Model):
    """
    Modelo para comentários em posts
    """
    __tablename__ = 'comments'
    
    # Campos básicos
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    content = Column(Text, nullable=False)
    
    # Comentários aninhados (resposta a outro comentário)
    parent_comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    
    # Contadores
    likes_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    
    # Metadados
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # Soft delete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User")
    post = relationship("Post", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id])
    replies = relationship("Comment", back_populates="parent_comment")
    
    def __repr__(self):
        return f'<Comment {self.id}: {self.content[:50]}>'
    
    def to_dict(self, include_user=True, include_replies=False):
        """Converte comentário para dicionário"""
        data = {
            'id': self.id,
            'content': self.content,
            'parent_comment_id': self.parent_comment_id,
            'likes_count': self.likes_count,
            'replies_count': self.replies_count,
            'is_edited': self.is_edited,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Incluir dados do usuário
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'name': f"{self.user.first_name} {self.user.last_name}".strip(),
                'avatar_url': getattr(self.user, 'avatar_url', None)
            }
        
        # Incluir respostas (comentários filhos)
        if include_replies and self.replies:
            data['replies'] = [reply.to_dict(include_user=True, include_replies=False) 
                             for reply in self.replies if not reply.is_deleted]
        
        return data

# Atualizar o modelo User para incluir relacionamento com posts
def update_user_model():
    """
    Função para adicionar relacionamento posts ao modelo User existente
    Adicione esta linha no modelo User:
    
    posts = relationship("Post", back_populates="user")
    """
    pass