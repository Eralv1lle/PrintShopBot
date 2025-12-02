from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.admin import UserOrders
from bot.keyboards import get_main_keyboard
from bot.utils import create_pagination_keyboard
from web.models import Order
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(UserOrders.waiting_username)
async def search_user_orders(message: Message, state: FSMContext):
    username = message.text.strip().lstrip('@')
    
    if not username:
        await message.answer("❌ Введите username", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    orders = list(Order.select().where(Order.username == username))
    
    if not orders:
        await message.answer(
            f"❌ Заказы для @{username} не найдены\n\n"
            "Проверьте правильность username",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return
    
    await state.update_data(username=username)
    
    keyboard = create_pagination_keyboard(
        items=orders,
        page=0,
        per_page=10,
        callback_prefix='user_orders',
        get_button_text=lambda o: f"#{o.id} — {float(o.total_amount):.2f} ₽ ({o.created_at.strftime('%d.%m.%Y')})",
        get_button_data=lambda o: f"user_order_{o.id}"
    )
    
    text = f"📦 Ваши заказы (@{username}):\n"
    text += f"Всего: {len(orders)}"
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()

@router.callback_query(F.data.startswith('user_orders_page_'))
async def user_orders_pagination(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = data.get('username')
    
    if not username:
        await callback.answer("❌ Ошибка")
        return
    
    page = int(callback.data.split('_')[-1])
    orders = list(Order.select().where(Order.username == username))
    
    keyboard = create_pagination_keyboard(
        items=orders,
        page=page,
        per_page=10,
        callback_prefix='user_orders',
        get_button_text=lambda o: f"#{o.id} — {float(o.total_amount):.2f} ₽ ({o.created_at.strftime('%d.%m.%Y')})",
        get_button_data=lambda o: f"user_order_{o.id}"
    )
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(F.data.startswith('user_order_'))
async def show_user_order(callback: CallbackQuery):
    order_id = int(callback.data.split('_')[2])
    order = Order.get_by_id(order_id)
    
    text = f"📋 Заказ #{order.id}\n\n"
    text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"👤 {order.first_name} {order.last_name}\n"
    text += f"📞 {order.phone}\n"
    text += f"💰 Итого: {float(order.total_amount):.2f} ₽\n\n"
    text += "📦 Товары:\n"
    
    for item in order.items:
        text += f"  • {item.product_name}\n"
        text += f"    {item.quantity} шт × {float(item.price):.2f} ₽ = {float(item.price * item.quantity):.2f} ₽\n"
    
    if order.comment:
        text += f"\n💬 Комментарий: {order.comment}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 К списку заказов', callback_data='back_to_user_orders')]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == 'back_to_user_orders')
async def back_to_user_orders(callback: CallbackQuery):
    username = callback.from_user.username

    if not username:
        await callback.message.edit_text("❌ Username не найден")
        return

    orders = list(Order.select().where(Order.username == username))

    if not orders:
        await callback.message.edit_text(f"❌ Заказы для @{username} не найдены")
        return

    keyboard = create_pagination_keyboard(
        items=orders,
        page=0,
        per_page=10,
        callback_prefix='user_orders',
        get_button_text=lambda o: f"#{o.id} — {float(o.total_amount):.2f} ₽ ({o.created_at.strftime('%d.%m.%Y')})",
        get_button_data=lambda o: f"user_order_{o.id}"
    )

    text = f"📦 Ваши заказы (@{username}):\n"
    text += f"Всего: {len(orders)}"

    await callback.message.edit_text(text, reply_markup=keyboard)
