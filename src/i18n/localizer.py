# src/i18n/localizer.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
from flask import g

class Localizer:
    """
    Sistema de localização (L10n) para formatação regional
    Formata: datas, números, moedas, telefones por região
    """
    
    def __init__(self, locales_dir: str = None):
        self.locales_dir = locales_dir or os.path.join(os.path.dirname(__file__), 'locales')
        self.default_locale = 'en_US'
        self.supported_locales = ['pt_BR', 'en_US', 'es_ES']
        self._formats = {}
        self._load_formats()
    
    def _load_formats(self):
        """Carrega configurações de formato dos arquivos JSON"""
        for locale in self.supported_locales:
            try:
                formats_path = os.path.join(self.locales_dir, locale, 'formats.json')
                if os.path.exists(formats_path):
                    with open(formats_path, 'r', encoding='utf-8') as f:
                        self._formats[locale] = json.load(f)
                else:
                    print(f"Warning: Arquivo de formato não encontrado: {formats_path}")
                    self._formats[locale] = self._get_default_formats()
            except Exception as e:
                print(f"Erro ao carregar formatos para {locale}: {e}")
                self._formats[locale] = self._get_default_formats()
    
    def _get_default_formats(self) -> Dict:
        """Retorna formatos padrão (inglês) como fallback"""
        return {
            "currency": {
                "symbol": "$",
                "decimal_separator": ".",
                "thousands_separator": ",",
                "format": "{symbol}{amount}",
                "decimals": 2
            },
            "date": {
                "short": "MM/dd/yyyy",
                "medium": "MMM dd, yyyy",
                "long": "MMMM dd, yyyy",
                "time_12": "h:mm a",
                "time_24": "HH:mm",
                "datetime": "MMM dd, yyyy 'at' h:mm a"
            },
            "numbers": {
                "decimal_separator": ".",
                "thousands_separator": ","
            },
            "phone": {
                "format": "({area}) {prefix}-{number}",
                "country_code": "+1"
            }
        }
    
    def get_locale(self) -> str:
        """Obtém o locale atual"""
        if hasattr(g, 'locale'):
            return g.locale
        return self.default_locale
    
    def format_currency(self, amount: Union[int, float], currency_code: str = None, locale: str = None) -> str:
        """
        Formata valor monetário
        
        Args:
            amount: Valor a ser formatado
            currency_code: Código da moeda (USD, BRL, EUR)
            locale: Locale para formatação
        
        Returns:
            Valor formatado (ex: "R$ 1.234,56", "$1,234.56")
        """
        if locale is None:
            locale = self.get_locale()
        
        formats = self._formats.get(locale, self._get_default_formats())
        currency_config = formats.get('currency', {})
        
        # Configurações por moeda e região
        if currency_code:
            currency_symbols = {
                'pt_BR': {'BRL': 'R$', 'USD': 'US$', 'EUR': '€'},
                'en_US': {'USD': '$', 'BRL': 'R$', 'EUR': '€'},
                'es_ES': {'EUR': '€', 'USD': '$', 'BRL': 'R$'}
            }
            
            if locale in currency_symbols and currency_code in currency_symbols[locale]:
                currency_config['symbol'] = currency_symbols[locale][currency_code]
        
        # Formatação do número
        decimals = currency_config.get('decimals', 2)
        decimal_sep = currency_config.get('decimal_separator', '.')
        thousands_sep = currency_config.get('thousands_separator', ',')
        
        # Formatar o valor
        formatted_amount = f"{amount:.{decimals}f}"
        integer_part, decimal_part = formatted_amount.split('.')
        
        # Adicionar separador de milhares
        if len(integer_part) > 3:
            parts = []
            for i in range(len(integer_part), 0, -3):
                start = max(0, i - 3)
                parts.append(integer_part[start:i])
            integer_part = thousands_sep.join(reversed(parts))
        
        # Montar valor final
        if decimals > 0:
            formatted_amount = f"{integer_part}{decimal_sep}{decimal_part}"
        else:
            formatted_amount = integer_part
        
        # Aplicar formato da moeda
        symbol = currency_config.get('symbol', '$')
        currency_format = currency_config.get('format', '{symbol}{amount}')
        
        return currency_format.format(symbol=symbol, amount=formatted_amount)
    
    def format_number(self, number: Union[int, float], decimals: int = None, locale: str = None) -> str:
        """
        Formata números com separadores regionais
        
        Args:
            number: Número a ser formatado
            decimals: Número de casas decimais (None = automático)
            locale: Locale para formatação
        
        Returns:
            Número formatado (ex: "1.234,56", "1,234.56")
        """
        if locale is None:
            locale = self.get_locale()
        
        formats = self._formats.get(locale, self._get_default_formats())
        number_config = formats.get('numbers', {})
        
        decimal_sep = number_config.get('decimal_separator', '.')
        thousands_sep = number_config.get('thousands_separator', ',')
        
        # Determinar casas decimais
        if decimals is None:
            decimals = 2 if isinstance(number, float) and number % 1 != 0 else 0
        
        # Formatar
        formatted = f"{number:.{decimals}f}" if decimals > 0 else str(int(number))
        
        if decimals > 0:
            integer_part, decimal_part = formatted.split('.')
        else:
            integer_part, decimal_part = formatted, ""
        
        # Separador de milhares
        if len(integer_part) > 3:
            parts = []
            for i in range(len(integer_part), 0, -3):
                start = max(0, i - 3)
                parts.append(integer_part[start:i])
            integer_part = thousands_sep.join(reversed(parts))
        
        return f"{integer_part}{decimal_sep}{decimal_part}" if decimal_part else integer_part
    
    def format_date(self, date: datetime, format_type: str = 'medium', locale: str = None) -> str:
        """
        Formata data conforme padrão regional
        
        Args:
            date: Data a ser formatada
            format_type: Tipo do formato ('short', 'medium', 'long', 'time_12', 'time_24', 'datetime')
            locale: Locale para formatação
        
        Returns:
            Data formatada
        """
        if locale is None:
            locale = self.get_locale()
        
        # Mapeamentos por idioma
        months = {
            'pt_BR': [
                'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
            ],
            'en_US': [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ],
            'es_ES': [
                'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]
        }
        
        months_short = {
            'pt_BR': ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'],
            'en_US': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'es_ES': ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        }
        
        # Formatos por tipo e locale
        if format_type == 'short':
            if locale == 'pt_BR':
                return date.strftime('%d/%m/%Y')
            elif locale == 'es_ES':
                return date.strftime('%d/%m/%Y')
            else:  # en_US
                return date.strftime('%m/%d/%Y')
        
        elif format_type == 'medium':
            month = months_short.get(locale, months_short['en_US'])[date.month - 1]
            if locale == 'pt_BR':
                return f"{date.day} de {month} de {date.year}"
            elif locale == 'es_ES':
                return f"{date.day} de {month} de {date.year}"
            else:  # en_US
                return f"{month} {date.day}, {date.year}"
        
        elif format_type == 'long':
            month = months.get(locale, months['en_US'])[date.month - 1]
            if locale == 'pt_BR':
                return f"{date.day} de {month} de {date.year}"
            elif locale == 'es_ES':
                return f"{date.day} de {month} de {date.year}"
            else:  # en_US
                return f"{month} {date.day}, {date.year}"
        
        elif format_type == 'time_12':
            return date.strftime('%I:%M %p')
        
        elif format_type == 'time_24':
            return date.strftime('%H:%M')
        
        elif format_type == 'datetime':
            date_part = self.format_date(date, 'medium', locale)
            time_part = date.strftime('%H:%M')
            
            if locale == 'pt_BR':
                return f"{date_part} às {time_part}"
            elif locale == 'es_ES':
                return f"{date_part} a las {time_part}"
            else:  # en_US
                return f"{date_part} at {time_part}"
        
        return date.isoformat()
    
    def format_relative_time(self, date: datetime, locale: str = None) -> str:
        """
        Formata tempo relativo (ex: "há 2 horas", "2 hours ago")
        """
        if locale is None:
            locale = self.get_locale()
        
        now = datetime.now()
        diff = now - date
        
        # Textos por idioma
        relative_texts = {
            'pt_BR': {
                'now': 'agora',
                'minute': 'há {n} minuto|há {n} minutos',
                'hour': 'há {n} hora|há {n} horas',
                'day': 'há {n} dia|há {n} dias',
                'week': 'há {n} semana|há {n} semanas',
                'month': 'há {n} mês|há {n} meses',
                'year': 'há {n} ano|há {n} anos'
            },
            'en_US': {
                'now': 'now',
                'minute': '{n} minute ago|{n} minutes ago',
                'hour': '{n} hour ago|{n} hours ago',
                'day': '{n} day ago|{n} days ago',
                'week': '{n} week ago|{n} weeks ago',
                'month': '{n} month ago|{n} months ago',
                'year': '{n} year ago|{n} years ago'
            },
            'es_ES': {
                'now': 'ahora',
                'minute': 'hace {n} minuto|hace {n} minutos',
                'hour': 'hace {n} hora|hace {n} horas',
                'day': 'hace {n} día|hace {n} días',
                'week': 'hace {n} semana|hace {n} semanas',
                'month': 'hace {n} mes|hace {n} meses',
                'year': 'hace {n} año|hace {n} años'
            }
        }
        
        texts = relative_texts.get(locale, relative_texts['en_US'])
        
        if diff.total_seconds() < 60:
            return texts['now']
        elif diff.total_seconds() < 3600:  # < 1 hora
            minutes = int(diff.total_seconds() / 60)
            template = texts['minute'].split('|')[0 if minutes == 1 else 1]
            return template.format(n=minutes)
        elif diff.days < 1:  # < 1 dia
            hours = int(diff.total_seconds() / 3600)
            template = texts['hour'].split('|')[0 if hours == 1 else 1]
            return template.format(n=hours)
        elif diff.days < 7:  # < 1 semana
            template = texts['day'].split('|')[0 if diff.days == 1 else 1]
            return template.format(n=diff.days)
        elif diff.days < 30:  # < 1 mês
            weeks = diff.days // 7
            template = texts['week'].split('|')[0 if weeks == 1 else 1]
            return template.format(n=weeks)
        elif diff.days < 365:  # < 1 ano
            months = diff.days // 30
            template = texts['month'].split('|')[0 if months == 1 else 1]
            return template.format(n=months)
        else:  # >= 1 ano
            years = diff.days // 365
            template = texts['year'].split('|')[0 if years == 1 else 1]
            return template.format(n=years)
    
    def format_phone(self, phone: str, locale: str = None) -> str:
        """
        Formata número de telefone conforme padrão regional
        
        Args:
            phone: Número de telefone limpo (apenas dígitos)
            locale: Locale para formatação
        
        Returns:
            Telefone formatado
        """
        if locale is None:
            locale = self.get_locale()
        
        # Remove caracteres não numéricos
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Formatação por região
        if locale == 'pt_BR':
            if len(clean_phone) == 11:  # Celular com 9º dígito
                return f"({clean_phone[:2]}) {clean_phone[2]} {clean_phone[3:7]}-{clean_phone[7:]}"
            elif len(clean_phone) == 10:  # Fixo
                return f"({clean_phone[:2]}) {clean_phone[2:6]}-{clean_phone[6:]}"
            else:
                return clean_phone
        
        elif locale == 'en_US':
            if len(clean_phone) == 10:
                return f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
            elif len(clean_phone) == 11 and clean_phone[0] == '1':
                return f"+1 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:]}"
            else:
                return clean_phone
        
        elif locale == 'es_ES':
            if len(clean_phone) == 9:
                return f"{clean_phone[:3]} {clean_phone[3:6]} {clean_phone[6:]}"
            else:
                return clean_phone
        
        return clean_phone

# Instância global do localizador
localizer = Localizer()

def format_currency(amount: Union[int, float], currency: str = None, locale: str = None) -> str:
    """Função de conveniência para formatação de moeda"""
    return localizer.format_currency(amount, currency, locale)

def format_date(date: datetime, format_type: str = 'medium', locale: str = None) -> str:
    """Função de conveniência para formatação de data"""
    return localizer.format_date(date, format_type, locale)

def format_relative_time(date: datetime, locale: str = None) -> str:
    """Função de conveniência para tempo relativo"""
    return localizer.format_relative_time(date, locale)