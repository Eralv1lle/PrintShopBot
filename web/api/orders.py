from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
from web.models import Order, OrderItem, Product, User
from web.utils import add_order_to_excel, get_excel_file
import asyncio
from aiogram import Bot
from config import config

orders_bp = Blueprint('orders', __name__)

async def notify_admins(order_text):
    try:
        bot = Bot(token=config.BOT_TOKEN)
        admins = User.select().where(User.is_admin == True)
        for admin in admins:
            try:
                await bot.send_message(admin.telegram_id, order_text)
            except:
                pass
        await bot.session.close()
    except:
        pass

@orders_bp.route('/checkout', methods=['POST'])
def checkout():
    try:
        data = request.json
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        phone = data.get('phone', '').strip()
        username = data.get('username', '').strip().lstrip('@')
        cart_items = data.get('cart', [])
        comment = data.get('comment', '').strip()
        
        if not first_name or not last_name or not phone or not cart_items:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        total_amount = 0
        order_items_data = []
        
        for item in cart_items:
            product = Product.get_by_id(item['product_id'])
            quantity = item['quantity']
            item_total = float(product.price) * quantity
            total_amount += item_total
            
            order_items_data.append({
                'product': product,
                'product_name': product.name,
                'quantity': quantity,
                'price': product.price
            })
        
        order = Order.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            username=username if username else None,
            total_amount=total_amount,
            comment=comment
        )
        
        for item_data in order_items_data:
            OrderItem.create(
                order=order,
                product=item_data['product'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        excel_data = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'username': username,
            'items': [{
                'product_name': item['product_name'],
                'quantity': item['quantity']
            } for item in order_items_data]
        }
        
        add_order_to_excel(excel_data)
        
        notification = f"🛒 Новый заказ #{order.id}\n\n"
        notification += f"👤 {first_name} {last_name}\n"
        notification += f"📞 {phone}\n"
        if username:
            notification += f"👤 @{username}\n"
        notification += f"💰 {total_amount:.2f} ₽\n\n"
        notification += "📦 Товары:\n"
        for item in order_items_data:
            notification += f"  • {item['product_name']} — {item['quantity']} шт\n"
        if comment:
            notification += f"\n💬 {comment}"
        
        try:
            asyncio.run(notify_admins(notification))
        except:
            pass
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Order created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orders_bp.route('/excel/latest', methods=['GET'])
def download_excel():
    try:
        excel_path = get_excel_file()
        return send_file(
            excel_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='orders.xlsx'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
