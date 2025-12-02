from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_main_keyboard, get_admin_keyboard
from bot.states.admin import UserOrders
from web.models import User

router = Router()

def is_admin(user_id: int) -> bool:
    try:
        user = User.get(User.telegram_id == user_id)
        return user.is_admin
    except User.DoesNotExist:
        return False

@router.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    User.get_or_create(telegram_id=user_id)
    
    await message.answer(
        "👋 Добро пожаловать в Print Shop!\n\n"
        "🛍 Откройте магазин через кнопку ниже\n"
        "📦 Или проверьте свои заказы",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == '🛍 Открыть магазин')
async def open_shop(message: Message):
    await message.answer(
        "🛍️ Откройте магазин через кнопку выше",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == '📦 Мои заказы')
async def my_orders_start(message: Message, state: FSMContext):
    username = message.from_user.username

    if not username:
        await message.answer(
            "❌ У вас не установлен username в Telegram\n\n"
            "Установите username в настройках Telegram и попробуйте снова",
            reply_markup=get_main_keyboard()
        )
        return

    from web.models import Order
    orders = list(Order.select().where(Order.username == username))

    if not orders:
        await message.answer(
            f"❌ Заказы для @{username} не найдены\n\n"
            "Возможно, вы указали другой username при оформлении заказа",
            reply_markup=get_main_keyboard()
        )
        return

    from bot.utils import create_pagination_keyboard
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

@router.message(Command('help'))
async def cmd_help(message: Message):
    user_id = message.from_user.id
    
    help_text = "ℹ️ Справка:\n\n"
    help_text += "/start - начать работу\n"
    help_text += "/help - показать справку\n"
    help_text += "🛍 Открыть магазин - перейти в каталог\n"
    help_text += "📦 Мои заказы - посмотреть заказы\n"
    
    if is_admin(user_id):
        help_text += "\n👑 Админ команды:\n"
        help_text += "/admin - админ-панель\n"
        help_text += "➕ Добавить товар\n"
        help_text += "✏️ Редактировать товары\n"
        help_text += "📊 Статистика\n"
        help_text += "👥 Клиенты\n"
        help_text += "📥 Получить Excel\n"
    
    await message.answer(
        help_text,
        reply_markup=get_admin_keyboard() if is_admin(user_id) else get_main_keyboard()
    )

@router.message()
async def handle_unknown(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state:
        return

    user_id = message.from_user.id

    if is_admin(user_id):
        await message.answer(
            "🤔 Не понял команду. Используйте кнопки меню или /help",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "🤔 Не понял команду.\n\n"
            "🛍 Откройте магазин через кнопку\n"
            "📦 Или проверьте свои заказы\n"
            "ℹ️ Используйте /help для справки",
            reply_markup=get_main_keyboard()
        )
