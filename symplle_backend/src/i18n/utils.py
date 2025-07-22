# src/i18n/utils.py
from typing import Dict, List, Optional, Any
from flask import g, request
from datetime import datetime
import re

from .translator import translator, _
from .localizer import localizer, format_currency, format_date, format_relative_time

class I18nUtils:
    """
    Utilidades combinadas para i18n + L10n
    Facilita o uso em templates e APIs
    """
    
    @staticmethod
    def get_supported_locales() -> List[Dict[str, str]]:
        """
        Retorna lista de locales suportados com informações
        
        Returns:
            Lista com código, nome nativo e nome em inglês
        """
        return [
            {
                'code': 'pt_BR',
                'name': 'Português (Brasil)',
                'native_name': 'Português (Brasil)',
                'flag': '🇧🇷',
                'currency': 'BRL'
            },
            {
                'code': 'en_US', 
                'name': 'English (United States)',
                'native_name': 'English (US)',
                'flag': '🇺🇸',
                'currency': 'USD'
            },
            {
                'code': 'es_ES',
                'name': 'Español (España)', 
                'native_name': 'Español (España)',
                'flag': '🇪🇸',
                'currency': 'EUR'
            }
        ]
    
    @staticmethod
    def detect_locale_from_request() -> str:
        """
        Detecta locale a partir do request HTTP
        Priority: URL param > Accept-Language > Default
        """
        # 1. Parâmetro na URL (?lang=pt_BR)
        if request and request.args.get('lang'):
            lang = request.args.get('lang')
            if lang in translator.supported_locales:
                return lang
        
        # 2. Accept-Language header
        return translator.detect_language()
    
    @staticmethod
    def set_locale_context(locale: str = None):
        """
        Define locale no contexto da aplicação Flask
        """
        if locale is None:
            locale = I18nUtils.detect_locale_from_request()
        
        translator.set_locale(locale)
        g.locale = locale
        g.language = locale.split('_')[0]  # 'pt' from 'pt_BR'
    
    @staticmethod
    def translate_with_fallback(key: str, fallback: str = None, **kwargs) -> str:
        """
        Traduz com fallback personalizado
        """
        translation = _(key, **kwargs)
        
        # Se não encontrou tradução e fallback foi fornecido
        if translation == key and fallback:
            return fallback.format(**kwargs) if kwargs else fallback
        
        return translation
    
    @staticmethod
    def format_api_response(data: Any, message_key: str = None, success: bool = True, **message_vars) -> Dict:
        """
        Formata resposta de API com mensagem localizada
        
        Args:
            data: Dados da resposta
            message_key: Chave da mensagem a ser traduzida
            success: Se a operação foi bem-sucedida
            **message_vars: Variáveis para interpolação na mensagem
        
        Returns:
            Dicionário formatado para resposta API
        """
        response = {
            'success': success,
            'data': data,
            'locale': translator.get_locale(),
            'timestamp': datetime.now().isoformat()
        }
        
        if message_key:
            response['message'] = _(message_key, **message_vars)
        
        return response
    
    @staticmethod
    def format_validation_errors(errors: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Formata erros de validação com mensagens localizadas
        
        Args:
            errors: Dicionário com campo -> lista de erros
        
        Returns:
            Erros com mensagens traduzidas
        """
        localized_errors = {}
        
        for field, field_errors in errors.items():
            localized_errors[field] = []
            
            for error in field_errors:
                # Tenta traduzir o erro, senão mantém original
                if error.startswith('validation.'):
                    localized_error = _(error)
                else:
                    # Mapeia erros comuns
                    error_mapping = {
                        'required': 'validation.required',
                        'invalid_email': 'validation.invalid_email',
                        'too_short': 'validation.too_short',
                        'too_long': 'validation.too_long'
                    }
                    
                    error_key = error_mapping.get(error, f'validation.{error}')
                    localized_error = _(error_key)
                    
                    # Se não encontrou tradução, usa o erro original
                    if localized_error == error_key:
                        localized_error = error
                
                localized_errors[field].append(localized_error)
        
        return localized_errors
    
    @staticmethod
    def format_user_data(user_data: Dict, include_locale_info: bool = True) -> Dict:
        """
        Formata dados do usuário com informações localizadas
        """
        formatted = user_data.copy()
        
        if include_locale_info:
            locale = translator.get_locale()
            formatted['locale_info'] = {
                'locale': locale,
                'language': locale.split('_')[0],
                'currency': I18nUtils.get_currency_for_locale(locale),
                'date_format': I18nUtils.get_date_format_example(locale)
            }
        
        # Formatar campos específicos se existirem
        if 'created_at' in formatted and isinstance(formatted['created_at'], datetime):
            formatted['created_at_formatted'] = format_date(formatted['created_at'])
            formatted['created_at_relative'] = format_relative_time(formatted['created_at'])
        
        if 'phone' in formatted and formatted['phone']:
            formatted['phone_formatted'] = localizer.format_phone(formatted['phone'])
        
        return formatted
    
    @staticmethod
    def get_currency_for_locale(locale: str = None) -> str:
        """Retorna moeda padrão para o locale"""
        if locale is None:
            locale = translator.get_locale()
        
        currency_mapping = {
            'pt_BR': 'BRL',
            'en_US': 'USD', 
            'es_ES': 'EUR'
        }
        
        return currency_mapping.get(locale, 'USD')
    
    @staticmethod
    def get_date_format_example(locale: str = None) -> str:
        """Retorna exemplo de formato de data para o locale"""
        if locale is None:
            locale = translator.get_locale()
        
        example_date = datetime(2024, 3, 15, 14, 30)
        return format_date(example_date, 'short', locale)
    
    @staticmethod
    def validate_phone_number(phone: str, locale: str = None) -> bool:
        """
        Valida número de telefone conforme padrão regional
        """
        if locale is None:
            locale = translator.get_locale()
        
        # Remove caracteres não numéricos
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Validação por região
        if locale == 'pt_BR':
            # Brasil: 10 ou 11 dígitos (com DDD)
            return len(clean_phone) in [10, 11] and clean_phone[:2] in ['11', '12', '13', '14', '15', '16', '17', '18', '19', '21', '22', '24', '27', '28', '31', '32', '33', '34', '35', '37', '38', '41', '42', '43', '44', '45', '46', '47', '48', '49', '51', '53', '54', '55', '61', '62', '63', '64', '65', '66', '67', '68', '69', '71', '73', '74', '75', '77', '79', '81', '82', '83', '84', '85', '86', '87', '88', '89', '91', '92', '93', '94', '95', '96', '97', '98', '99']
        
        elif locale == 'en_US':
            # EUA: 10 dígitos
            return len(clean_phone) == 10
        
        elif locale == 'es_ES':
            # Espanha: 9 dígitos
            return len(clean_phone) == 9
        
        return False
    
    @staticmethod
    def get_country_list(locale: str = None) -> List[Dict]:
        """
        Retorna lista de países com nomes traduzidos
        """
        if locale is None:
            locale = translator.get_locale()
        
        # Base dos países mais comuns
        countries_base = [
            {'code': 'BR', 'calling_code': '+55'},
            {'code': 'US', 'calling_code': '+1'},
            {'code': 'ES', 'calling_code': '+34'},
            {'code': 'AR', 'calling_code': '+54'},
            {'code': 'MX', 'calling_code': '+52'},
            {'code': 'CA', 'calling_code': '+1'},
            {'code': 'FR', 'calling_code': '+33'},
            {'code': 'DE', 'calling_code': '+49'},
            {'code': 'IT', 'calling_code': '+39'},
            {'code': 'PT', 'calling_code': '+351'}
        ]
        
        # Nomes por idioma
        country_names = {
            'pt_BR': {
                'BR': 'Brasil', 'US': 'Estados Unidos', 'ES': 'Espanha',
                'AR': 'Argentina', 'MX': 'México', 'CA': 'Canadá',
                'FR': 'França', 'DE': 'Alemanha', 'IT': 'Itália', 'PT': 'Portugal'
            },
            'en_US': {
                'BR': 'Brazil', 'US': 'United States', 'ES': 'Spain',
                'AR': 'Argentina', 'MX': 'Mexico', 'CA': 'Canada',
                'FR': 'France', 'DE': 'Germany', 'IT': 'Italy', 'PT': 'Portugal'
            },
            'es_ES': {
                'BR': 'Brasil', 'US': 'Estados Unidos', 'ES': 'España',
                'AR': 'Argentina', 'MX': 'México', 'CA': 'Canadá',
                'FR': 'Francia', 'DE': 'Alemania', 'IT': 'Italia', 'PT': 'Portugal'
            }
        }
        
        names = country_names.get(locale, country_names['en_US'])
        
        return [
            {
                'code': country['code'],
                'name': names.get(country['code'], country['code']),
                'calling_code': country['calling_code']
            }
            for country in countries_base
        ]

# Instância global dos utilitários
i18n_utils = I18nUtils()

# Funções de conveniência para templates Flask
def setup_template_globals(app):
    """
    Registra funções globais para templates Jinja2
    Chame esta função após criar a app Flask
    """
    
    @app.template_global()
    def t(key, **kwargs):
        """Tradução em templates: {{ t('auth.login.title') }}"""
        return _(key, **kwargs)
    
    @app.template_global()
    def format_currency_template(amount, currency=None):
        """Formato de moeda em templates: {{ format_currency_template(1234.56) }}"""
        return format_currency(amount, currency)
    
    @app.template_global()
    def format_date_template(date, format_type='medium'):
        """Formato de data em templates: {{ format_date_template(user.created_at) }}"""
        return format_date(date, format_type)
    
    @app.template_global()
    def format_relative_time_template(date):
        """Tempo relativo em templates: {{ format_relative_time_template(post.created_at) }}"""
        return format_relative_time(date)
    
    @app.template_global()
    def get_current_locale():
        """Locale atual em templates: {{ get_current_locale() }}"""
        return translator.get_locale()
    
    @app.template_global()
    def get_supported_locales_template():
        """Locales suportados em templates: {{ get_supported_locales_template() }}"""
        return i18n_utils.get_supported_locales()

# Context processor para Flask
def i18n_context_processor():
    """
    Context processor que adiciona variáveis i18n em todos os templates
    Registre com: app.context_processor(i18n_context_processor)
    """
    return {
        'current_locale': translator.get_locale(),
        'current_language': translator.get_locale().split('_')[0],
        'supported_locales': i18n_utils.get_supported_locales(),
        'currency': i18n_utils.get_currency_for_locale(),
        'date_format_example': i18n_utils.get_date_format_example()
    }

def get_browser_locale(request=None):
    """Detecta locale do browser via Accept-Language header"""
    if not request:
        from flask import request as flask_request
        request = flask_request
    
    if request and request.headers.get('Accept-Language'):
        # Pega o primeiro idioma do Accept-Language
        lang = request.headers.get('Accept-Language').split(',')[0].strip()
        
        # Mapear para nossos locales suportados
        lang_mapping = {
            'pt': 'pt_BR', 'pt-BR': 'pt_BR', 'pt-br': 'pt_BR',
            'en': 'en_US', 'en-US': 'en_US', 'en-us': 'en_US',
            'es': 'es_ES', 'es-ES': 'es_ES', 'es-es': 'es_ES'
        }
        
        return lang_mapping.get(lang, 'en_US')
    
    return 'en_US'

def get_currency_for_locale(locale=None):
    """Retorna moeda padrão para o locale (duplicata para compatibilidade)"""
    return i18n_utils.get_currency_for_locale(locale)