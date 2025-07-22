# src/services/file_service.py
"""
Core File Upload Service para Symplle
Suporte completo para imagens, documentos e vídeos com i18n
"""

import os
import uuid
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import current_app

# Importar sistema i18n
try:
    from i18n import _, i18n_utils
    I18N_AVAILABLE = True
except ImportError:
    def _(key, **kwargs): return key
    class MockI18nUtils:
        @staticmethod
        def format_api_response(data, message_key=None, success=True, **kwargs):
            return {'success': success, 'data': data, 'message': message_key or ''}
    i18n_utils = MockI18nUtils()
    I18N_AVAILABLE = False

class FileUploadService:
    """
    Serviço principal para upload e gerenciamento de arquivos
    Features: validação, processamento, storage, segurança
    """
    
    def __init__(self):
        # Configurações de upload
        self.base_upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        self.max_file_size = 10 * 1024 * 1024  # 10MB default
        self.chunk_size = 8192  # 8KB chunks
        
        # Tipos de arquivo permitidos
        self.allowed_extensions = {
            'image': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'},
            'document': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
            'video': {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'},
            'audio': {'mp3', 'wav', 'aac', 'ogg', 'flac'}
        }
        
        # MIME types seguros
        self.safe_mime_types = {
            # Imagens
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            # Documentos
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'text/rtf',
            # Vídeos
            'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm',
            # Áudios
            'audio/mpeg', 'audio/wav', 'audio/aac', 'audio/ogg', 'audio/flac'
        }
        
        # Tamanhos máximos por tipo (em bytes)
        self.max_sizes = {
            'image': 5 * 1024 * 1024,      # 5MB para imagens
            'document': 10 * 1024 * 1024,  # 10MB para documentos
            'video': 50 * 1024 * 1024,     # 50MB para vídeos
            'audio': 10 * 1024 * 1024      # 10MB para áudios
        }
        
        # Criar diretórios se não existirem
        self._ensure_upload_directories()
    
    def _ensure_upload_directories(self):
        """Cria diretórios de upload se não existirem"""
        directories = [
            'avatars',      # Fotos de perfil
            'posts',        # Mídia de posts
            'documents',    # Documentos (CVs, portfolios)
            'chat',         # Arquivos compartilhados em chat
            'temp',         # Arquivos temporários
            'thumbnails'    # Miniaturas geradas
        ]
        
        for directory in directories:
            dir_path = os.path.join(self.base_upload_dir, directory)
            os.makedirs(dir_path, exist_ok=True)
            
            # Criar arquivo .gitkeep para manter diretório no git
            gitkeep_path = os.path.join(dir_path, '.gitkeep')
            if not os.path.exists(gitkeep_path):
                open(gitkeep_path, 'a').close()
    
    def validate_file(self, file: FileStorage, file_type: str = 'image') -> Dict:
        """
        Valida arquivo antes do upload
        
        Args:
            file: Arquivo enviado
            file_type: Tipo esperado ('image', 'document', 'video', 'audio')
        
        Returns:
            Dict com resultado da validação
        """
        if not file or not file.filename:
            return {
                'valid': False,
                'error': _('upload.validation.no_file'),
                'code': 'NO_FILE'
            }
        
        # Verificar nome do arquivo
        filename = secure_filename(file.filename)
        if not filename:
            return {
                'valid': False,
                'error': _('upload.validation.invalid_filename'),
                'code': 'INVALID_FILENAME'
            }
        
        # Verificar extensão
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if file_ext not in self.allowed_extensions.get(file_type, set()):
            allowed = ', '.join(self.allowed_extensions.get(file_type, []))
            return {
                'valid': False,
                'error': _('upload.validation.invalid_extension', 
                          extension=file_ext, allowed=allowed),
                'code': 'INVALID_EXTENSION'
            }
        
        # Verificar MIME type
        file.seek(0)  # Reset file pointer
        mime_type = file.mimetype or mimetypes.guess_type(filename)[0]
        if mime_type not in self.safe_mime_types:
            return {
                'valid': False,
                'error': _('upload.validation.invalid_mime_type', mime_type=mime_type),
                'code': 'INVALID_MIME_TYPE'
            }
        
        # Verificar tamanho
        file.seek(0, 2)  # Ir para o final do arquivo
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        max_size = self.max_sizes.get(file_type, self.max_file_size)
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            return {
                'valid': False,
                'error': _('upload.validation.file_too_large', 
                          size=f'{file_size/(1024*1024):.1f}MB', 
                          max_size=f'{max_size_mb:.0f}MB'),
                'code': 'FILE_TOO_LARGE'
            }
        
        # Verificar se arquivo não está vazio
        if file_size == 0:
            return {
                'valid': False,
                'error': _('upload.validation.empty_file'),
                'code': 'EMPTY_FILE'
            }
        
        return {
            'valid': True,
            'filename': filename,
            'file_ext': file_ext,
            'mime_type': mime_type,
            'file_size': file_size
        }
    
    def generate_unique_filename(self, original_filename: str, user_id: int = None) -> str:
        """
        Gera nome único para o arquivo
        
        Args:
            original_filename: Nome original do arquivo
            user_id: ID do usuário (opcional)
        
        Returns:
            Nome único do arquivo
        """
        # Obter extensão
        file_ext = ''
        if '.' in original_filename:
            file_ext = '.' + original_filename.rsplit('.', 1)[1].lower()
        
        # Gerar ID único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Incluir user_id se fornecido
        if user_id:
            filename = f"user_{user_id}_{timestamp}_{unique_id}{file_ext}"
        else:
            filename = f"{timestamp}_{unique_id}{file_ext}"
        
        return filename
    
    def calculate_file_hash(self, file: FileStorage) -> str:
        """
        Calcula hash MD5 do arquivo para detectar duplicatas
        
        Args:
            file: Arquivo para calcular hash
        
        Returns:
            Hash MD5 do arquivo
        """
        file.seek(0)
        hash_md5 = hashlib.md5()
        
        for chunk in iter(lambda: file.read(self.chunk_size), b""):
            hash_md5.update(chunk)
        
        file.seek(0)  # Reset file pointer
        return hash_md5.hexdigest()
    
    def save_file(self, file: FileStorage, category: str, user_id: int = None, 
                  custom_filename: str = None) -> Dict:
        """
        Salva arquivo no sistema de storage
        
        Args:
            file: Arquivo a ser salvo
            category: Categoria do arquivo ('avatars', 'posts', 'documents', 'chat')
            user_id: ID do usuário
            custom_filename: Nome personalizado (opcional)
        
        Returns:
            Dict com informações do arquivo salvo
        """
        try:
            # Determinar tipo de arquivo baseado na categoria
            file_type_mapping = {
                'avatars': 'image',
                'posts': 'image',
                'documents': 'document',
                'chat': 'image',  # Default, pode ser qualquer tipo
                'temp': 'image'
            }
            
            file_type = file_type_mapping.get(category, 'image')
            
            # Validar arquivo
            validation = self.validate_file(file, file_type)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error'],
                    'code': validation['code']
                }
            
            # Gerar nome único
            if custom_filename:
                filename = secure_filename(custom_filename)
                # Garantir extensão correta
                if '.' not in filename:
                    filename += '.' + validation['file_ext']
            else:
                filename = self.generate_unique_filename(validation['filename'], user_id)
            
            # Determinar caminho de destino
            upload_dir = os.path.join(self.base_upload_dir, category)
            file_path = os.path.join(upload_dir, filename)
            
            # Verificar se arquivo já existe
            counter = 1
            original_filename = filename
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                file_path = os.path.join(upload_dir, filename)
                counter += 1
            
            # Calcular hash do arquivo
            file_hash = self.calculate_file_hash(file)
            
            # Salvar arquivo
            file.save(file_path)
            
            # Obter informações do arquivo salvo
            file_stats = os.stat(file_path)
            
            # Gerar URL de acesso
            file_url = f"/uploads/{category}/{filename}"
            
            return {
                'success': True,
                'file_info': {
                    'filename': filename,
                    'original_filename': file.filename,
                    'file_path': file_path,
                    'file_url': file_url,
                    'category': category,
                    'file_size': validation['file_size'],
                    'mime_type': validation['mime_type'],
                    'file_hash': file_hash,
                    'user_id': user_id,
                    'uploaded_at': datetime.now().isoformat(),
                    'file_ext': validation['file_ext']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': _('upload.error.save_failed', error=str(e)),
                'code': 'SAVE_FAILED'
            }
    
    def delete_file(self, file_path: str) -> Dict:
        """
        Remove arquivo do sistema
        
        Args:
            file_path: Caminho do arquivo a ser removido
        
        Returns:
            Dict com resultado da operação
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return {
                    'success': True,
                    'message': _('upload.delete.success')
                }
            else:
                return {
                    'success': False,
                    'error': _('upload.delete.file_not_found'),
                    'code': 'FILE_NOT_FOUND'
                }
        except Exception as e:
            return {
                'success': False,
                'error': _('upload.delete.failed', error=str(e)),
                'code': 'DELETE_FAILED'
            }
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Obtém informações detalhadas de um arquivo
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            Dict com informações do arquivo
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'exists': False,
                    'error': _('upload.info.file_not_found')
                }
            
            stats = os.stat(file_path)
            filename = os.path.basename(file_path)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            return {
                'exists': True,
                'filename': filename,
                'file_size': stats.st_size,
                'file_ext': file_ext,
                'created_at': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'file_path': file_path
            }
            
        except Exception as e:
            return {
                'exists': False,
                'error': _('upload.info.failed', error=str(e))
            }
    
    def list_user_files(self, user_id: int, category: str = None) -> List[Dict]:
        """
        Lista arquivos de um usuário
        
        Args:
            user_id: ID do usuário
            category: Categoria específica (opcional)
        
        Returns:
            Lista de arquivos do usuário
        """
        files = []
        
        # Categorias a verificar
        categories = [category] if category else ['avatars', 'posts', 'documents', 'chat']
        
        for cat in categories:
            cat_dir = os.path.join(self.base_upload_dir, cat)
            if not os.path.exists(cat_dir):
                continue
            
            # Buscar arquivos do usuário
            for filename in os.listdir(cat_dir):
                if filename.startswith(f"user_{user_id}_"):
                    file_path = os.path.join(cat_dir, filename)
                    file_info = self.get_file_info(file_path)
                    
                    if file_info['exists']:
                        file_info['category'] = cat
                        file_info['file_url'] = f"/uploads/{cat}/{filename}"
                        files.append(file_info)
        
        # Ordenar por data de criação (mais recente primeiro)
        files.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return files

# Instância global do serviço
file_service = FileUploadService()