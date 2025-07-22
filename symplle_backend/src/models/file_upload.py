# src/models/file_upload.py
"""
Modelo de dados para File Uploads no Symplle
Registra todos os uploads de arquivos no banco de dados
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from . import db

class FileUpload(db.Model):
    """
    Modelo para registrar uploads de arquivos
    """
    __tablename__ = 'file_uploads'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Informações do arquivo
    filename = db.Column(db.String(255), nullable=False)  # Nome único gerado
    original_filename = db.Column(db.String(255), nullable=False)  # Nome original
    file_path = db.Column(db.String(500), nullable=False)  # Caminho completo
    file_url = db.Column(db.String(500), nullable=False)  # URL de acesso
    
    # Metadados do arquivo
    file_size = db.Column(db.BigInteger, nullable=False)  # Tamanho em bytes
    mime_type = db.Column(db.String(100), nullable=False)  # Tipo MIME
    file_hash = db.Column(db.String(32), nullable=True, index=True)  # Hash MD5
    file_ext = db.Column(db.String(10), nullable=False)  # Extensão
    
    # Categorização
    category = db.Column(db.String(50), nullable=False, index=True)  # avatars, posts, documents, chat
    file_type = db.Column(db.String(20), nullable=False)  # image, document, video, audio
    
    # Contexto de uso
    related_id = db.Column(db.String(100), nullable=True)  # ID do post, chat, etc.
    related_type = db.Column(db.String(50), nullable=True)  # post, chat_message, profile
    
    # Status e processamento
    is_processed = db.Column(db.Boolean, default=False)  # Se foi processado (thumbnails, etc.)
    is_active = db.Column(db.Boolean, default=True)  # Se está ativo
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    
    # Metadados de imagem (se aplicável)
    image_width = db.Column(db.Integer, nullable=True)
    image_height = db.Column(db.Integer, nullable=True)
    has_thumbnails = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='file_uploads')
    
    def __repr__(self):
        return f'<FileUpload {self.filename} by User {self.user_id}>'
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_ext': self.file_ext,
            'category': self.category,
            'file_type': self.file_type,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'is_processed': self.is_processed,
            'is_active': self.is_active,
            'processing_status': self.processing_status,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'has_thumbnails': self.has_thumbnails,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_from_upload(cls, file_info, user_id, category, related_id=None, related_type=None):
        """
        Cria registro a partir de informações de upload
        
        Args:
            file_info: Dict com informações do arquivo
            user_id: ID do usuário
            category: Categoria do arquivo
            related_id: ID relacionado (opcional)
            related_type: Tipo relacionado (opcional)
        
        Returns:
            Instância do FileUpload
        """
        # Determinar tipo de arquivo
        mime_type = file_info.get('mime_type', '')
        if mime_type.startswith('image/'):
            file_type = 'image'
        elif mime_type.startswith('video/'):
            file_type = 'video'
        elif mime_type.startswith('audio/'):
            file_type = 'audio'
        else:
            file_type = 'document'
        
        upload = cls(
            user_id=user_id,
            filename=file_info.get('filename'),
            original_filename=file_info.get('original_filename'),
            file_path=file_info.get('file_path'),
            file_url=file_info.get('file_url'),
            file_size=file_info.get('file_size'),
            mime_type=file_info.get('mime_type'),
            file_hash=file_info.get('file_hash'),
            file_ext=file_info.get('file_ext'),
            category=category,
            file_type=file_type,
            related_id=related_id,
            related_type=related_type
        )
        
        return upload
    
    @classmethod
    def get_user_files(cls, user_id, category=None, file_type=None, limit=50):
        """
        Obtém arquivos de um usuário
        
        Args:
            user_id: ID do usuário
            category: Categoria específica (opcional)
            file_type: Tipo específico (opcional)
            limit: Limite de resultados
        
        Returns:
            Lista de FileUpload
        """
        query = cls.query.filter_by(user_id=user_id, is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        if file_type:
            query = query.filter_by(file_type=file_type)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_hash(cls, file_hash):
        """
        Busca arquivo por hash (para detectar duplicatas)
        
        Args:
            file_hash: Hash MD5 do arquivo
        
        Returns:
            FileUpload ou None
        """
        return cls.query.filter_by(file_hash=file_hash, is_active=True).first()
    
    def mark_processed(self, has_thumbnails=False, image_width=None, image_height=None):
        """
        Marca arquivo como processado
        
        Args:
            has_thumbnails: Se thumbnails foram criados
            image_width: Largura da imagem (se aplicável)
            image_height: Altura da imagem (se aplicável)
        """
        self.is_processed = True
        self.processing_status = 'completed'
        self.has_thumbnails = has_thumbnails
        
        if image_width:
            self.image_width = image_width
        if image_height:
            self.image_height = image_height
        
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message=None):
        """
        Marca arquivo como falha no processamento
        
        Args:
            error_message: Mensagem de erro (opcional)
        """
        self.processing_status = 'failed'
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self):
        """
        Remove arquivo logicamente (soft delete)
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()

class FileVersion(db.Model):
    """
    Modelo para versões de arquivos (thumbnails, resizes, etc.)
    """
    __tablename__ = 'file_versions'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    file_upload_id = db.Column(db.Integer, db.ForeignKey('file_uploads.id'), nullable=False)
    
    # Informações da versão
    version_name = db.Column(db.String(50), nullable=False)  # thumb, small, medium, large
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    
    # Metadados da versão
    file_size = db.Column(db.BigInteger, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    quality = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    file_upload = db.relationship('FileUpload', backref='versions')
    
    def __repr__(self):
        return f'<FileVersion {self.version_name} of {self.file_upload_id}>'
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'file_upload_id': self.file_upload_id,
            'version_name': self.version_name,
            'filename': self.filename,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'quality': self.quality,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_version(cls, file_upload_id, version_name, version_info):
        """
        Cria nova versão de arquivo
        
        Args:
            file_upload_id: ID do arquivo original
            version_name: Nome da versão
            version_info: Dict com informações da versão
        
        Returns:
            Instância do FileVersion
        """
        version = cls(
            file_upload_id=file_upload_id,
            version_name=version_name,
            filename=version_info.get('filename'),
            file_path=version_info.get('path'),
            file_url=version_info.get('url'),
            file_size=version_info.get('file_size'),
            width=version_info.get('size', (None, None))[0],
            height=version_info.get('size', (None, None))[1],
            quality=version_info.get('quality')
        )
        
        return version