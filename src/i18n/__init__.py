# src/i18n/__init__.py
"""
Sistema de Internacionalização (i18n) e Localização (L10n) para Symplle
Suporte completo para PT-BR, EN-US, ES-ES + extensível

Uso básico:
    from i18n import _, t, format_currency, format_date
    
    # Tradução
    message = _('auth.login.success', username='João')
    
    # Formatação
    price = format_currency(1234.56, 'BRL')  # R$ 1.234,56
    date = format_date(datetime.now())       # formato regional
"""

# Importações principais
from .translator import translator, _, t
from .localizer import localizer, format_currency, format_date, format_relative_time
from .utils import i18n_utils, setup_template_globals, i18n_context_processor
from .i18n_middleware import I18nMiddleware

# Versão do sistema
__version__ = '1.0.0'

# Locales suportados
SUPPORTED_LOCALES = ['pt_BR', 'en_US', 'es_ES']
DEFAULT_LOCALE = 'en_US'

def init_app(app):
    """
    Inicializa o sistema i18n na aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
        
    Uso:
        from i18n import init_app
        init_app(app)
    """
    
    # Configura middleware
    middleware = I18nMiddleware(app)
    
    # Registra funções globais para templates
    setup_template_globals(app)
    
    # Registra context processor
    app.context_processor(i18n_context_processor)
    
    # Configura locale padrão se não definido
    if not hasattr(app.config, 'DEFAULT_LOCALE'):
        app.config['DEFAULT_LOCALE'] = DEFAULT_LOCALE
    
    if not hasattr(app.config, 'SUPPORTED_LOCALES'):
        app.config['SUPPORTED_LOCALES'] = SUPPORTED_LOCALES
    
    print(f"✅ Sistema i18n inicializado com suporte a: {', '.join(SUPPORTED_LOCALES)}")
    
    return middleware

def get_locale():
    """Obtém o locale atual"""
    return translator.get_locale()

def set_locale(locale):
    """Define o locale atual"""
    translator.set_locale(locale)

def translate(key, **kwargs):
    """Alias para função de tradução"""
    return _(key, **kwargs)

def get_supported_locales():
    """Retorna lista de locales suportados"""
    return i18n_utils.get_supported_locales()

# Exportações principais
__all__ = [
    # Core functions
    '_', 't', 'translate',
    
    # Formatting functions  
    'format_currency', 'format_date', 'format_relative_time',
    
    # Locale management
    'get_locale', 'set_locale', 'get_supported_locales',
    
    # Flask integration
    'init_app',
    
    # Utilities
    'i18n_utils',
    
    # Classes
    'translator', 'localizer', 'I18nMiddleware',
    
    # Constants
    'SUPPORTED_LOCALES', 'DEFAULT_LOCALE'
]