from flask import Blueprint, jsonify
from web.models import Product

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.select().where(Product.is_active == True)
        products_list = [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'photo_path': p.photo_path
        } for p in products]
        return jsonify({'success': True, 'products': products_list}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
