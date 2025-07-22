from flask import Blueprint, jsonify
from src.models.country import Country

countries_bp = Blueprint('countries', __name__)

@countries_bp.route('/countries', methods=['GET'])
def get_countries():
    """
    Retorna a lista de todos os países com seus códigos ISO e DDI.
    Utilizado pelo frontend para o seletor de países na tela de registo.
    """
    countries = Country.query.order_by(Country.name).all()
    return jsonify({
        'success': True,
        'data': [country.to_dict() for country in countries]
    })

@countries_bp.route('/countries/<iso_code>', methods=['GET'])
def get_country_by_iso(iso_code):
    """
    Retorna os detalhes de um país específico pelo seu código ISO.
    """
    country = Country.query.filter_by(iso_code=iso_code.upper()).first()
    
    if not country:
        return jsonify({
            'success': False,
            'message': f'País com código ISO {iso_code} não encontrado'
        }), 404
    
    return jsonify({
        'success': True,
        'data': country.to_dict()
    })
