# src/services/image_service.py
"""
Image Processing Service para Symplle
Resize, thumbnails, optimization, watermarks com i18n
"""

import os
import io
from PIL import Image, ImageOps, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

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

class ImageProcessingService:
    """
    Serviço de processamento de imagens
    Features: resize, thumbnails, optimization, watermarks, format conversion
    """
    
    def __init__(self):
        # Configurações padrão
        self.default_quality = 85
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (600, 600)
        }
        
        # Tamanhos para diferentes usos
        self.avatar_sizes = {
            'thumb': (50, 50),
            'small': (100, 100),
            'medium': (200, 200),
            'large': (400, 400)
        }
        
        self.post_sizes = {
            'thumb': (200, 200),
            'medium': (600, 600),
            'large': (1200, 1200),
            'full': None  # Tamanho original
        }
        
        # Formatos suportados
        self.supported_formats = {'JPEG', 'PNG', 'WEBP', 'BMP', 'GIF'}
        self.output_format = 'JPEG'  # Formato padrão de saída
        
        # Diretório base para uploads
        self.base_upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    
    def validate_image(self, image_path: str) -> Dict:
        """
        Valida se o arquivo é uma imagem válida
        
        Args:
            image_path: Caminho da imagem
        
        Returns:
            Dict com resultado da validação
        """
        try:
            with Image.open(image_path) as img:
                # Verificar formato
                if img.format not in self.supported_formats:
                    return {
                        'valid': False,
                        'error': _('image.validation.unsupported_format', format=img.format),
                        'code': 'UNSUPPORTED_FORMAT'
                    }
                
                # Obter informações da imagem
                width, height = img.size
                mode = img.mode
                
                # Verificar dimensões mínimas
                if width < 10 or height < 10:
                    return {
                        'valid': False,
                        'error': _('image.validation.too_small'),
                        'code': 'IMAGE_TOO_SMALL'
                    }
                
                # Verificar dimensões máximas (ex: 10000x10000)
                if width > 10000 or height > 10000:
                    return {
                        'valid': False,
                        'error': _('image.validation.too_large'),
                        'code': 'IMAGE_TOO_LARGE'
                    }
                
                return {
                    'valid': True,
                    'image_info': {
                        'width': width,
                        'height': height,
                        'format': img.format,
                        'mode': mode,
                        'has_transparency': img.mode in ('RGBA', 'LA', 'P')
                    }
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': _('image.validation.corrupt', error=str(e)),
                'code': 'CORRUPT_IMAGE'
            }
    
    def resize_image(self, image_path: str, target_size: Tuple[int, int], 
                    maintain_aspect: bool = True, quality: int = None) -> Dict:
        """
        Redimensiona imagem
        
        Args:
            image_path: Caminho da imagem original
            target_size: Tamanho alvo (width, height)
            maintain_aspect: Manter proporção
            quality: Qualidade de compressão (1-100)
        
        Returns:
            Dict com resultado e caminho da imagem redimensionada
        """
        try:
            # Validar imagem
            validation = self.validate_image(image_path)
            if not validation['valid']:
                return validation
            
            quality = quality or self.default_quality
            
            with Image.open(image_path) as img:
                # Converter para RGB se necessário (para JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Criar fundo branco para transparências
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar
                if maintain_aspect:
                    img.thumbnail(target_size, Image.Resampling.LANCZOS)
                    resized_img = img
                else:
                    resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # Gerar nome do arquivo redimensionado
                base_name = os.path.splitext(image_path)[0]
                resized_filename = f"{base_name}_resized_{target_size[0]}x{target_size[1]}.jpg"
                
                # Salvar imagem redimensionada
                resized_img.save(resized_filename, 'JPEG', quality=quality, optimize=True)
                
                # Obter informações da imagem redimensionada
                final_size = resized_img.size
                file_size = os.path.getsize(resized_filename)
                
                return {
                    'success': True,
                    'resized_path': resized_filename,                    
                    'original_size': (validation['image_info']['width'], validation['image_info']['height']),
                    'final_size': final_size,
                    'file_size': file_size,
                    'quality': quality
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': _('image.resize.failed', error=str(e)),
                'code': 'RESIZE_FAILED'
            }
    
    def create_thumbnail(self, image_path: str, size: str = 'medium') -> Dict:
        """
        Cria thumbnail da imagem
        
        Args:
            image_path: Caminho da imagem original
            size: Tamanho do thumbnail ('small', 'medium', 'large')
        
        Returns:
            Dict com resultado e caminho do thumbnail
        """
        if size not in self.thumbnail_sizes:
            return {
                'success': False,
                'error': _('image.thumbnail.invalid_size', size=size),
                'code': 'INVALID_SIZE'
            }
        
        target_size = self.thumbnail_sizes[size]
        
        try:
            with Image.open(image_path) as img:
                # Criar thumbnail mantendo proporção
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Criar imagem quadrada com fundo branco
                thumb = Image.new('RGB', target_size, (255, 255, 255))
                
                # Centralizar imagem no thumbnail
                offset = ((target_size[0] - img.size[0]) // 2,
                         (target_size[1] - img.size[1]) // 2)
                thumb.paste(img, offset)
                
                # Gerar nome do arquivo thumbnail
                base_name = os.path.splitext(image_path)[0]
                thumb_filename = f"{base_name}_thumb_{size}.jpg"
                
                # Salvar thumbnail
                thumb.save(thumb_filename, 'JPEG', quality=self.default_quality, optimize=True)
                
                return {
                    'success': True,
                    'thumbnail_path': thumb_filename,
                    'thumbnail_size': target_size,
                    'file_size': os.path.getsize(thumb_filename)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': _('image.thumbnail.failed', error=str(e)),
                'code': 'THUMBNAIL_FAILED'
            }
    
    def create_avatar_versions(self, image_path: str, user_id: int) -> Dict:
        """
        Cria todas as versões necessárias para avatar
        
        Args:
            image_path: Caminho da imagem original
            user_id: ID do usuário
        
        Returns:
            Dict com todos os caminhos gerados
        """
        try:
            avatar_versions = {}
            
            for size_name, dimensions in self.avatar_sizes.items():
                # Criar versão redimensionada
                result = self.resize_image(image_path, dimensions, maintain_aspect=True)
                
                if result.get('success'):
                    # Mover para diretório de avatars com nome padronizado
                    original_path = result['resized_path']
                    avatar_filename = f"user_{user_id}_avatar_{size_name}.jpg"
                    avatar_path = os.path.join(self.base_upload_dir, 'avatars', avatar_filename)
                    
                    # Mover arquivo
                    os.rename(original_path, avatar_path)
                    
                    avatar_versions[size_name] = {
                        'path': avatar_path,
                        'url': f"/uploads/avatars/{avatar_filename}",
                        'size': dimensions,
                        'file_size': result['file_size']
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error'],
                        'code': result.get('code', 'AVATAR_CREATION_FAILED')
                    }
            
            return {
                'success': True,
                'avatar_versions': avatar_versions,
                'message': _('image.avatar.created_successfully')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': _('image.avatar.failed', error=str(e)),
                'code': 'AVATAR_CREATION_FAILED'
            }
    
    def create_post_versions(self, image_path: str, post_id: str = None) -> Dict:
        """
        Cria versões de imagem para posts
        
        Args:
            image_path: Caminho da imagem original
            post_id: ID do post (opcional)
        
        Returns:
            Dict com todas as versões criadas
        """
        try:
            post_versions = {}
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            for size_name, dimensions in self.post_sizes.items():
                if dimensions is None:  # Versão full (original)
                    # Apenas otimizar sem redimensionar
                    optimized_path = os.path.join(
                        self.base_upload_dir, 'posts', f"{base_name}_full.jpg"
                    )
                    
                    with Image.open(image_path) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(optimized_path, 'JPEG', quality=90, optimize=True)
                    
                    post_versions[size_name] = {
                        'path': optimized_path,
                        'url': f"/uploads/posts/{os.path.basename(optimized_path)}",
                        'size': img.size,
                        'file_size': os.path.getsize(optimized_path)
                    }
                else:
                    # Criar versão redimensionada
                    result = self.resize_image(image_path, dimensions, maintain_aspect=True)
                    
                    if result.get('success'):
                        # Mover para diretório de posts
                        original_path = result['resized_path']
                        post_filename = f"{base_name}_{size_name}.jpg"
                        post_path = os.path.join(self.base_upload_dir, 'posts', post_filename)
                        
                        os.rename(original_path, post_path)
                        
                        post_versions[size_name] = {
                            'path': post_path,
                            'url': f"/uploads/posts/{post_filename}",
                            'size': result['final_size'],
                            'file_size': result['file_size']
                        }
            
            return {
                'success': True,
                'post_versions': post_versions,
                'message': _('image.post.created_successfully')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': _('image.post.failed', error=str(e)),
                'code': 'POST_CREATION_FAILED'
            }
    
    def optimize_image(self, image_path: str, quality: int = None, 
                      max_width: int = None, max_height: int = None) -> Dict:
        """
        Otimiza imagem (compressão + redimensionamento se necessário)
        
        Args:
            image_path: Caminho da imagem
            quality: Qualidade de compressão (1-100)
            max_width: Largura máxima
            max_height: Altura máxima
        
        Returns:
            Dict com resultado da otimização
        """
        try:
            quality = quality or self.default_quality
            
            with Image.open(image_path) as img:
                # Converter para RGB se necessário
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar se necessário
                if max_width or max_height:
                    max_size = (max_width or img.width, max_height or img.height)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Gerar nome do arquivo otimizado
                base_name = os.path.splitext(image_path)[0]
                optimized_path = f"{base_name}_optimized.jpg"
                
                # Salvar otimizado
                img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
                
                # Comparar tamanhos
                original_size = os.path.getsize(image_path)
                optimized_size = os.path.getsize(optimized_path)
                reduction_percent = ((original_size - optimized_size) / original_size) * 100
                
                return {
                    'success': True,
                    'optimized_path': optimized_path,
                    'original_size': original_size,
                    'optimized_size': optimized_size,
                    'reduction_percent': round(reduction_percent, 2),
                    'final_dimensions': img.size
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': _('image.optimize.failed', error=str(e)),
                'code': 'OPTIMIZATION_FAILED'
            }
    
    def add_watermark(self, image_path: str, watermark_text: str = "Symplle") -> Dict:
        """
        Adiciona marca d'água na imagem
        
        Args:
            image_path: Caminho da imagem
            watermark_text: Texto da marca d'água
        
        Returns:
            Dict com resultado
        """
        try:
            with Image.open(image_path) as img:
                # Criar cópia para modificação
                watermarked = img.copy()
                
                # Criar objeto de desenho
                draw = ImageDraw.Draw(watermarked)
                
                # Configurar fonte (usar fonte padrão se não conseguir carregar)
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                
                # Calcular posição (canto inferior direito)
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                margin = 10
                x = img.width - text_width - margin
                y = img.height - text_height - margin
                
                # Adicionar texto com transparência
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
                
                # Gerar nome do arquivo com marca d'água
                base_name = os.path.splitext(image_path)[0]
                watermarked_path = f"{base_name}_watermarked.jpg"
                
                # Salvar
                watermarked.save(watermarked_path, 'JPEG', quality=self.default_quality)
                
                return {
                    'success': True,
                    'watermarked_path': watermarked_path,
                    'watermark_text': watermark_text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': _('image.watermark.failed', error=str(e)),
                'code': 'WATERMARK_FAILED'
            }

# Instância global do serviço
image_service = ImageProcessingService()