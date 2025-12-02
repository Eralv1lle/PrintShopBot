from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from config import config

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text='🛍 Открыть магазин', web_app=WebAppInfo(url=config.WEBAPP_URL))],
        [KeyboardButton(text='📦 Мои заказы')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        [KeyboardButton(text='➕ Добавить товар')],
        [KeyboardButton(text='✏️ Редактировать товары')],
        [KeyboardButton(text='📊 Статистика'), KeyboardButton(text='👥 Клиенты')],
        [KeyboardButton(text='📥 Получить Excel')],
        [KeyboardButton(text='🚪 Выйти из меню')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='❌ Отмена')]],
        resize_keyboard=True
    )

def get_add_product_choice():
    keyboard = [
        [InlineKeyboardButton(text='✍️ Добавить вручную', callback_data='add_manual')],
        [InlineKeyboardButton(text='📁 Импортировать из Excel', callback_data='add_import')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_photo_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⏭️ Пропустить фото', callback_data='skip_photo')]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_products')]
    ])

def get_product_actions_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton(text='✏️ Изменить название', callback_data=f'edit_name_{product_id}')],
        [InlineKeyboardButton(text='📝 Изменить описание', callback_data=f'edit_desc_{product_id}')],
        [InlineKeyboardButton(text='💰 Изменить цену', callback_data=f'edit_price_{product_id}')],
        [InlineKeyboardButton(text='🖼 Изменить фото', callback_data=f'edit_photo_{product_id}')],
        [InlineKeyboardButton(text='🗑 Удалить товар', callback_data=f'delete_{product_id}')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_products')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
