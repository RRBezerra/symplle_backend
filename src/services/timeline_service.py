# src/services/timeline_service.py
"""
Serviço de Timeline Personalizada do Symplle
Algoritmo inteligente para ordenar posts na timeline
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import joinedload

# ✅ CORRIGIDO: Imports absolutos
from models import db
from models.post import Post, Like, Comment, PostPrivacy
from models.user import User

class TimelineService:
    """
    Serviço para gerar timeline personalizada dos usuários
    """
    
    def __init__(self):
        self.engagement_weight = 0.4  # Peso das interações (likes, comentários)
        self.recency_weight = 0.3     # Peso da recência do post
        self.author_weight = 0.2      # Peso da relevância do autor
        self.content_weight = 0.1     # Peso do tipo de conteúdo
    
    def get_user_timeline(self, user_id, limit=20, offset=0, algorithm='smart'):
        """
        Gera timeline personalizada para o usuário
        
        Args:
            user_id: ID do usuário
            limit: Número de posts (max 100)
            offset: Offset para paginação
            algorithm: 'smart' | 'chronological' | 'popular'
        
        Returns:
            Lista de posts ordenados + metadata
        """
        try:
            if algorithm == 'chronological':
                return self._get_chronological_timeline(user_id, limit, offset)
            elif algorithm == 'popular':
                return self._get_popular_timeline(user_id, limit, offset)
            else:  # smart (default)
                return self._get_smart_timeline(user_id, limit, offset)
                
        except Exception as e:
            print(f"❌ Erro na timeline: {e}")
            # Fallback para timeline cronológica
            return self._get_chronological_timeline(user_id, limit, offset)
    
    def _get_chronological_timeline(self, user_id, limit, offset):
        """Timeline ordenada cronologicamente (mais recente primeiro)"""
        
        # Query base - posts públicos por enquanto
        # TODO: Adicionar posts de usuários seguidos quando implementar follow system
        query = db.session.query(Post).options(
            joinedload(Post.user)
        ).filter(
            Post.is_deleted == False,
            Post.privacy == PostPrivacy.PUBLIC
        )
        
        # Ordenar por data de criação (mais recente primeiro)
        posts = query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()
        
        return {
            'posts': [self._enrich_post_data(post, user_id) for post in posts],
            'algorithm': 'chronological',
            'total_count': len(posts),
            'metadata': {
                'limit': limit,
                'offset': offset,
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    
    def _get_popular_timeline(self, user_id, limit, offset):
        """Timeline ordenada por popularidade (mais curtidas/comentários)"""
        
        # Calcular score de popularidade
        popularity_score = (
            func.coalesce(Post.likes_count, 0) * 2 +  # Likes valem mais
            func.coalesce(Post.comments_count, 0) * 3 +  # Comentários valem mais ainda
            func.coalesce(Post.shares_count, 0) * 1.5  # Shares moderados
        ).label('popularity_score')
        
        query = db.session.query(Post, popularity_score).options(
            joinedload(Post.user)
        ).filter(
            Post.is_deleted == False,
            Post.privacy == PostPrivacy.PUBLIC,
            Post.created_at >= datetime.utcnow() - timedelta(days=7)  # Últimos 7 dias
        )
        
        # Ordenar por popularidade e depois por data
        results = query.order_by(
            desc('popularity_score'),
            desc(Post.created_at)
        ).offset(offset).limit(limit).all()
        
        posts = [result[0] for result in results]  # Extrair apenas o Post
        
        return {
            'posts': [self._enrich_post_data(post, user_id) for post in posts],
            'algorithm': 'popular',
            'total_count': len(posts),
            'metadata': {
                'limit': limit,
                'offset': offset,
                'time_range': '7_days',
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    
    def _get_smart_timeline(self, user_id, limit, offset):
        """Timeline inteligente com algoritmo de relevância"""
        
        # Calcular score inteligente baseado em múltiplos fatores
        now = datetime.utcnow()
        
        # Score de engajamento (likes + comentários)
        engagement_score = (
            func.coalesce(Post.likes_count, 0) + 
            func.coalesce(Post.comments_count, 0) * 2
        )
        
        # Score de recência (posts mais recentes pontuam mais)
        # Usar diferença em horas e converter para score 0-100
        hours_diff = func.extract('epoch', now - Post.created_at) / 3600.0
        recency_score = func.greatest(0, 100 - hours_diff / 24.0 * 10)  # Decai ao longo dos dias
        
        # Score de tipo de conteúdo (mídia pontua mais)
        content_score = func.case(
            (Post.post_type == 'image', 20),
            (Post.post_type == 'video', 25),
            (Post.post_type == 'mixed', 30),
            else_=10  # text
        )
        
        # Score final combinado
        final_score = (
            engagement_score * self.engagement_weight +
            recency_score * self.recency_weight +
            content_score * self.content_weight
        ).label('smart_score')
        
        query = db.session.query(Post, final_score).options(
            joinedload(Post.user)
        ).filter(
            Post.is_deleted == False,
            Post.privacy == PostPrivacy.PUBLIC,
            Post.created_at >= datetime.utcnow() - timedelta(days=30)  # Últimos 30 dias
        )
        
        # Ordenar por score inteligente
        results = query.order_by(
            desc('smart_score'),
            desc(Post.created_at)  # Tiebreaker por data
        ).offset(offset).limit(limit).all()
        
        posts_with_scores = [(result[0], float(result[1])) for result in results]
        
        return {
            'posts': [self._enrich_post_data(post, user_id, score) 
                     for post, score in posts_with_scores],
            'algorithm': 'smart',
            'total_count': len(posts_with_scores),
            'metadata': {
                'limit': limit,
                'offset': offset,
                'algorithm_weights': {
                    'engagement': self.engagement_weight,
                    'recency': self.recency_weight,
                    'author': self.author_weight,
                    'content': self.content_weight
                },
                'time_range': '30_days',
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    
    def _enrich_post_data(self, post, current_user_id, smart_score=None):
        """
        Enriquecer dados do post com informações contextuais
        """
        post_data = post.to_dict()
        
        # Adicionar informações contextuais para o usuário atual
        try:
            # Verificar se usuário curtiu este post
            user_liked = db.session.query(Like).filter(
                Like.user_id == current_user_id,
                Like.post_id == post.id
            ).first() is not None
            
            post_data['user_interactions'] = {
                'liked': user_liked,
                'can_edit': post.user_id == current_user_id,
                'can_delete': post.user_id == current_user_id
            }
            
            # Adicionar score se disponível
            if smart_score is not None:
                post_data['relevance_score'] = round(smart_score, 2)
            
            # Adicionar tempo relativo
            post_data['time_ago'] = self._get_relative_time(post.created_at)
            
            # Adicionar preview de comentários recentes (máximo 3)
            recent_comments = db.session.query(Comment).options(
                joinedload(Comment.user)
            ).filter(
                Comment.post_id == post.id,
                Comment.is_deleted == False,
                Comment.parent_comment_id.is_(None)  # Apenas comentários principais
            ).order_by(desc(Comment.created_at)).limit(3).all()
            
            post_data['recent_comments'] = [
                comment.to_dict(include_user=True, include_replies=False)
                for comment in recent_comments
            ]
            
        except Exception as e:
            print(f"⚠️ Erro ao enriquecer post {post.id}: {e}")
        
        return post_data
    
    def _get_relative_time(self, created_at):
        """
        Converte datetime para tempo relativo (ex: "há 2 horas", "há 1 dia")
        """
        if not created_at:
            return "unknown"
        
        now = datetime.utcnow()
        diff = now - created_at
        
        if diff.days > 0:
            if diff.days == 1:
                return "há 1 dia"
            elif diff.days < 7:
                return f"há {diff.days} dias"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"há {weeks} semana{'s' if weeks > 1 else ''}"
            else:
                months = diff.days // 30
                return f"há {months} {'meses' if months > 1 else 'mês'}"
        
        hours = diff.seconds // 3600
        if hours > 0:
            return f"há {hours} hora{'s' if hours > 1 else ''}"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"há {minutes} minuto{'s' if minutes > 1 else ''}"
        
        return "agora mesmo"
    
    def get_trending_posts(self, limit=10):
        """
        Obter posts em alta (trending) baseado em engajamento recente
        """
        try:
            # Posts das últimas 24 horas com mais engajamento
            trending_threshold = datetime.utcnow() - timedelta(hours=24)
            
            trending_score = (
                func.coalesce(Post.likes_count, 0) * 2 +
                func.coalesce(Post.comments_count, 0) * 3 +
                func.coalesce(Post.views_count, 0) * 0.1
            ).label('trending_score')
            
            query = db.session.query(Post, trending_score).options(
                joinedload(Post.user)
            ).filter(
                Post.is_deleted == False,
                Post.privacy == PostPrivacy.PUBLIC,
                Post.created_at >= trending_threshold,
                trending_score > 5  # Mínimo de engajamento
            )
            
            results = query.order_by(desc('trending_score')).limit(limit).all()
            posts = [result[0] for result in results]
            
            return {
                'trending_posts': [post.to_dict() for post in posts],
                'generated_at': datetime.utcnow().isoformat(),
                'time_window': '24_hours',
                'total_count': len(posts)
            }
            
        except Exception as e:
            print(f"❌ Erro ao buscar trending: {e}")
            return {
                'trending_posts': [],
                'error': str(e)
            }

# Instância global do serviço
timeline_service = TimelineService()