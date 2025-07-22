# src/i18n/i18n_middleware.py
"""
Middleware Flask para integração automática do sistema i18n/L10n
Modifica automaticamente as respostas das rotas existentes
"""

from flask import request, g, jsonify, current_app
from functools import wraps
import json
from typing import Dict, Any, Optional
from .translator import Translator
from .localizer import Localizer
from .utils import get_browser_locale, get_currency_for_locale

class I18nMiddleware:
    """Middleware para automatizar i18n/L10n nas respostas da API"""
    
    def __init__(self, app=None):
        self.translator = Translator()
        self.localizer = Localizer()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa o middleware na aplicação Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Registrar funções de template global
        app.jinja_env.globals.update(
            _=self.translate,
            format_currency=self.format_currency,
            format_date=self.format_date,
            format_time=self.format_time,
            format_number=self.format_number,
            format_phone=self.format_phone
        )
        
        print("🌍 I18n Middleware inicializado!")
    
    def before_request(self):
        """Executado antes de cada requisição"""
        # Detectar locale da requisição
        g.locale = self.detect_request_locale()
        
        # Criar funções de conveniência no contexto global
        g._ = lambda key, **kwargs: self.translate(key, **kwargs)
        g.format_currency = self.format_currency
        g.format_date = self.format_date
        g.format_time = self.format_time
        g.format_number = self.format_number
        g.format_phone = self.format_phone
        g.get_locale = lambda: g.locale
        
        print(f"🔍 Locale detectado: {g.locale}")
    
    def after_request(self, response):
        """Executado após cada requisição"""
        # Adicionar header de idioma na resposta
        response.headers['Content-Language'] = g.get('locale', 'en_US')
        
        # Auto-localizar respostas JSON se configurado
        if current_app.config.get('AUTO_LOCALIZE_RESPONSES', True):
            self.localize_response(response)
        
        return response
    
    def detect_request_locale(self) -> str:
        """Detecta locale da requisição atual"""
        # 1. Query parameter ?locale=pt_BR
        locale_param = request.args.get('locale') or request.args.get('lang')
        if locale_param:
            from .utils import normalize_locale, validate_locale
            normalized = normalize_locale(locale_param)
            if validate_locale(normalized):
                return normalized
        
        # 2. Header personalizado X-Locale
        custom_header = request.headers.get('X-Locale')
        if custom_header:
            from .utils import normalize_locale, validate_locale
            normalized = normalize_locale(custom_header)
            if validate_locale(normalized):
                return normalized
        
        # 3. Accept-Language header
        browser_locale = get_browser_locale(request)
        if browser_locale:
            return browser_locale
        
        # 4. Fallback para configuração padrão
        return current_app.config.get('DEFAULT_LOCALE', 'en_US')
    
    def translate(self, key: str, **kwargs) -> str:
        """Traduz uma chave usando o locale atual"""
        locale = g.get('locale', 'en_US')
        return self.translator.get(key, locale, **kwargs)
    
    def format_currency(self, amount, currency=None):
        """Formata moeda usando o locale atual"""
        locale = g.get('locale', 'en_US')
        if not currency:
            currency = get_currency_for_locale(locale)
        return self.localizer.format_currency(amount, currency, locale)
    
    def format_date(self, date_obj, format_type='short'):
        """Formata data usando o locale atual"""
        locale = g.get('locale', 'en_US')
        return self.localizer.format_date(date_obj, format_type, locale)
    
    def format_time(self, time_obj, format_type='short'):
        """Formata horário usando o locale atual"""
        locale = g.get('locale', 'en_US')
        return self.localizer.format_time(time_obj, format_type, locale)
    
    def format_number(self, number):
        """Formata número usando o locale atual"""
        locale = g.get('locale', 'en_US')
        return self.localizer.format_number(number, locale)
    
    def format_phone(self, phone):
        """Formata telefone usando o locale atual"""
        locale = g.get('locale', 'en_US')
        return self.localizer.format_phone(phone, locale)
    
    def localize_response(self, response):
        """Localiza automaticamente respostas JSON"""
        if not response.is_json:
            return
        
        try:
            data = response.get_json()
            if data and isinstance(data, dict):
                localized_data = self.localize_dict(data)
                response.data = json.dumps(localized_data, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Erro ao localizar resposta: {e}")
    
    def localize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Localiza recursivamente um dicionário"""
        if not isinstance(data, dict):
            return data
        
        localized = {}
        locale = g.get('locale', 'en_US')
        
        for key, value in data.items():
            # Localizar strings que começam com 'i18n:'
            if isinstance(value, str) and value.startswith('i18n:'):
                localized[key] = self.translator.get(value[5:], locale)
            
            # Localizar dicionários recursivamente
            elif isinstance(value, dict):
                localized[key] = self.localize_dict(value)
            
            # Localizar listas
            elif isinstance(value, list):
                localized[key] = [
                    self.localize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            
            # Localizar campos específicos conhecidos
            elif key in ['message', 'error_message', 'success_message']:
                localized[key] = self.translator.get(value, locale) if isinstance(value, str) else value
            
            else:
                localized[key] = value
        
        return localized

# Decorator para tradução automática de respostas
def localized_response(func):
    """
    Decorator para traduzir automaticamente mensagens em respostas
    
    Usage:
    @app.route('/api/test')
    @localized_response
    def test():
        return jsonify({
            'success': True,
            'message': 'i18n:messages.success',  # Será traduzido automaticamente
            'error': 'i18n:errors.generic'      # Será traduzido automaticamente
        })
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Se retornou tupla (response, status_code)
        if isinstance(result, tuple):
            response_data, status_code = result
        else:
            response_data = result
            status_code = 200
        
        # Localizar se for dicionário
        if isinstance(response_data, dict):
            i18n_middleware = current_app.extensions.get('i18n_middleware')
            if i18n_middleware:
                response_data = i18n_middleware.localize_dict(response_data)
        
        return jsonify(response_data), status_code
    
    return wrapper

# Funções de conveniência para uso em rotas
def _(key: str, **kwargs) -> str:
    """Função de conveniência para tradução"""
    locale = g.get('locale', 'en_US')
    translator = Translator()
    return translator.get(key, locale, **kwargs)

def localized_error(message_key: str, status_code: int = 400, **kwargs):
    """Retorna erro localizado"""
    return jsonify({
        'success': False,
        'message': _(message_key, **kwargs),
        'locale': g.get('locale', 'en_US')
    }), status_code

def localized_success(message_key: str, data: Dict = None, **kwargs):
    """Retorna sucesso localizado"""
    response = {
        'success': True,
        'message': _(message_key, **kwargs),
        'locale': g.get('locale', 'en_US')
    }
    
    if data:
        response.update(data)
    
    return jsonify(response)

# Função para inicializar middleware em uma app Flask
def init_i18n_middleware(app):
    """Inicializa middleware i18n em uma aplicação Flask"""
    middleware = I18nMiddleware(app)
    
    # Registrar no extensions para acesso posterior
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    app.extensions['i18n_middleware'] = middleware
    
    return middleware