import os
import sys
import json

# Adicionar o diretório pai ao path para poder importar os módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask
from src.models import db  # Modificado aqui
from src.models.country import Country

# Dados de exemplo para países (versão simplificada)
countries_data = [
    {"name": "Afghanistan", "iso_code": "AF", "iso_code_3": "AFG", "iso_num": "004", "calling_code": "+93"},
    {"name": "Albania", "iso_code": "AL", "iso_code_3": "ALB", "iso_num": "008", "calling_code": "+355"},
    {"name": "Algeria", "iso_code": "DZ", "iso_code_3": "DZA", "iso_num": "012", "calling_code": "+213"},
    {"name": "Andorra", "iso_code": "AD", "iso_code_3": "AND", "iso_num": "020", "calling_code": "+376"},
    {"name": "Angola", "iso_code": "AO", "iso_code_3": "AGO", "iso_num": "024", "calling_code": "+244"},
    {"name": "Argentina", "iso_code": "AR", "iso_code_3": "ARG", "iso_num": "032", "calling_code": "+54"},
    {"name": "Australia", "iso_code": "AU", "iso_code_3": "AUS", "iso_num": "036", "calling_code": "+61"},
    {"name": "Austria", "iso_code": "AT", "iso_code_3": "AUT", "iso_num": "040", "calling_code": "+43"},
    {"name": "Belgium", "iso_code": "BE", "iso_code_3": "BEL", "iso_num": "056", "calling_code": "+32"},
    {"name": "Brazil", "iso_code": "BR", "iso_code_3": "BRA", "iso_num": "076", "calling_code": "+55"},
    {"name": "Canada", "iso_code": "CA", "iso_code_3": "CAN", "iso_num": "124", "calling_code": "+1"},
    {"name": "China", "iso_code": "CN", "iso_code_3": "CHN", "iso_num": "156", "calling_code": "+86"},
    {"name": "France", "iso_code": "FR", "iso_code_3": "FRA", "iso_num": "250", "calling_code": "+33"},
    {"name": "Germany", "iso_code": "DE", "iso_code_3": "DEU", "iso_num": "276", "calling_code": "+49"},
    {"name": "India", "iso_code": "IN", "iso_code_3": "IND", "iso_num": "356", "calling_code": "+91"},
    {"name": "Italy", "iso_code": "IT", "iso_code_3": "ITA", "iso_num": "380", "calling_code": "+39"},
    {"name": "Japan", "iso_code": "JP", "iso_code_3": "JPN", "iso_num": "392", "calling_code": "+81"},
    {"name": "Mexico", "iso_code": "MX", "iso_code_3": "MEX", "iso_num": "484", "calling_code": "+52"},
    {"name": "Portugal", "iso_code": "PT", "iso_code_3": "PRT", "iso_num": "620", "calling_code": "+351"},
    {"name": "Russia", "iso_code": "RU", "iso_code_3": "RUS", "iso_num": "643", "calling_code": "+7"},
    {"name": "Spain", "iso_code": "ES", "iso_code_3": "ESP", "iso_num": "724", "calling_code": "+34"},
    {"name": "United Kingdom", "iso_code": "GB", "iso_code_3": "GBR", "iso_num": "826", "calling_code": "+44"},
    {"name": "United States", "iso_code": "US", "iso_code_3": "USA", "iso_num": "840", "calling_code": "+1"}
]

def insert_countries():
    """Insere os dados dos países na base de dados."""
    # Criar uma aplicação Flask temporária para o contexto
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../../symplle.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        
        # Verificar se já existem países na base de dados
        existing_count = Country.query.count()
        if existing_count > 0:
            print(f"Já existem {existing_count} países na base de dados.")
            return
        
        # Inserir os países
        for country_data in countries_data:
            country = Country(
                name=country_data["name"],
                iso_code=country_data["iso_code"],
                iso_code_3=country_data.get("iso_code_3"),
                iso_num=country_data.get("iso_num"),
                calling_code=country_data.get("calling_code")
            )
            db.session.add(country)
        
        # Commit das alterações
        db.session.commit()
        print(f"Inseridos {len(countries_data)} países na base de dados.")

if __name__ == "__main__":
    insert_countries()
