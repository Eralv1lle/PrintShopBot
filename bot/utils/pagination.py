from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Callable

def create_pagination_keyboard(
    items: List,
    page: int,
    per_page: int,
    callback_prefix: str,
    get_button_text: Callable,
    get_button_data: Callable
) -> InlineKeyboardMarkup:
    keyboard = []

    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(items))
    page_items = items[start_idx:end_idx]

    for item in page_items:
        keyboard.append([InlineKeyboardButton(
            text=get_button_text(item),
            callback_data=get_button_data(item)
        )])

    nav_buttons = []
    total_pages = (len(items) + per_page - 1) // per_page
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"{callback_prefix}_page_{page-1}"
        ))
    
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}",
            callback_data="page_info"
        ))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data=f"{callback_prefix}_page_{page+1}"
        ))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
