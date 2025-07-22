# src/i18n/translator.py
import json
import os
from typing import Dict, Optional, Union
from flask import request, g

class Translator:
    """
    Sistema de internacionalização (i18n) para múltiplos idiomas
    Suporte: PT-BR, EN-US, ES-ES + extensível para novos idiomas
    """
    
    def __init__(self, locales_dir: str = None):
        self.locales_dir = locales_dir or os.path.join(os.path.dirname(__file__), 'locales')
        self.default_locale = 'en_US'
        self.supported_locales = ['pt_BR', 'en_US', 'es_ES']
        self._translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Carrega todas as traduções dos arquivos JSON"""
        for locale in self.supported_locales:
            try:
                messages_path = os.path.join(self.locales_dir, locale, 'messages.json')
                if os.path.exists(messages_path):
                    with open(messages_path, 'r', encoding='utf-8') as f:
                        self._translations[locale] = json.load(f)
                else:
                    print(f"Warning: Arquivo de tradução não encontrado: {messages_path}")
                    self._translations[locale] = {}
            except Exception as e:
                print(f"Erro ao carregar traduções para {locale}: {e}")
                self._translations[locale] = {}
    
    def detect_language(self) -> str:
        """
        Detecta o idioma preferido do usuário
        Priority: User preference > Accept-Language header > Default
        """
        # 1. Preferência do usuário (se logado)
        if hasattr(g, 'user') and g.user and hasattr(g.user, 'preferred_language'):
            if g.user.preferred_language in self.supported_locales:
                return g.user.preferred_language
        
        # 2. Header Accept-Language
        if request:
            accepted_languages = request.headers.get('Accept-Language', '')
            for lang_range in accepted_languages.split(','):
                lang = lang_range.split(';')[0].strip()
                
                # Mapeamento de códigos ISO para nossos locales
                lang_mapping = {
                    'pt': 'pt_BR',
                    'pt-BR': 'pt_BR',
                    'pt-br': 'pt_BR',
                    'en': 'en_US',
                    'en-US': 'en_US',
                    'en-us': 'en_US',
                    'es': 'es_ES',
                    'es-ES': 'es_ES',
                    'es-es': 'es_ES'
                }
                
                if lang in lang_mapping and lang_mapping[lang] in self.supported_locales:
                    return lang_mapping[lang]
        
        # 3. Default fallback
        return self.default_locale
    
    def get_locale(self) -> str:
        """Obtém o locale atual"""
        if hasattr(g, 'locale'):
            return g.locale
        return self.detect_language()
    
    def set_locale(self, locale: str):
        """Define o locale atual"""
        if locale in self.supported_locales:
            g.locale = locale
        else:
            g.locale = self.default_locale
    
    def translate(self, key: str, locale: str = None, **kwargs) -> str:
        """
        Traduz uma chave para o idioma especificado
        
        Args:
            key: Chave da mensagem (ex: 'auth.login.success')
            locale: Código do idioma (ex: 'pt_BR'). Se None, usa o atual
            **kwargs: Variáveis para interpolação
        
        Returns:
            Texto traduzido com variáveis interpoladas
        """
        if locale is None:
            locale = self.get_locale()
        
        # Fallback para inglês se locale não suportado
        if locale not in self.supported_locales:
            locale = self.default_locale
        
        # Busca a tradução
        translation = self._get_nested_translation(self._translations.get(locale, {}), key)
        
        # Fallback para inglês se não encontrar
        if not translation and locale != self.default_locale:
            translation = self._get_nested_translation(
                self._translations.get(self.default_locale, {}), key
            )
        
        # Fallback final - retorna a própria chave
        if not translation:
            translation = key
        
        # Interpolação de variáveis
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Variável {e} não encontrada na tradução '{key}'")
        
        return translation
    
    def _get_nested_translation(self, translations: Dict, key: str) -> Optional[str]:
        """
        Busca tradução usando notação de ponto (ex: 'auth.login.success')
        """
        keys = key.split('.')
        current = translations
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def get_available_locales(self) -> list:
        """Retorna lista de locales disponíveis"""
        return self.supported_locales.copy()
    
    def add_locale_support(self, locale: str):
        """
        Adiciona suporte para novo locale
        Útil para expansão futura
        """
        if locale not in self.supported_locales:
            self.supported_locales.append(locale)
            self._load_translations()  # Recarrega traduções
    
    def reload_translations(self):
        """Recarrega todas as traduções (útil em desenvolvimento)"""
        self._translations.clear()
        self._load_translations()

# Instância global do tradutor
translator = Translator()

def _(key: str, **kwargs) -> str:
    """
    Função de conveniência para tradução rápida
    Uso: _('auth.login.success', username='João')
    """
    return translator.translate(key, **kwargs)

def t(key: str, locale: str = None, **kwargs) -> str:
    """
    Função de tradução com locale explícito
    Uso: t('auth.login.success', 'pt_BR', username='João')
    """
    return translator.translate(key, locale, **kwargs)