from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from bot.states.admin import AdminAuth, AddProduct, EditProduct, ImportProducts
from bot.keyboards import (get_admin_keyboard, get_cancel_keyboard, get_main_keyboard,
                           get_add_product_choice, get_skip_photo_keyboard,
                           get_back_keyboard, get_product_actions_keyboard)
from bot.utils import create_pagination_keyboard
from web.models import User, Product, Order, OrderItem
from config import config
from pathlib import Path
import openpyxl

router = Router()

def is_admin(user_id: int) -> bool:
    try:
        user = User.get(User.telegram_id == user_id)
        return user.is_admin
    except User.DoesNotExist:
        return False

@router.message(Command('admin'))
async def cmd_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        await message.answer(
            "🔐 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "🔐 Введите пароль:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminAuth.waiting_password)

@router.message(AdminAuth.waiting_password, F.text == '❌ Отмена')
async def cancel_auth(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_keyboard())

@router.message(AdminAuth.waiting_password)
async def check_password(message: Message, state: FSMContext):
    if message.text == config.ADMIN_PASSWORD:
        user_id = message.from_user.id
        user, created = User.get_or_create(
            telegram_id=user_id,
            defaults={'is_admin': True}
        )
        if not created:
            user.is_admin = True
            user.save()
        
        await state.clear()
        await message.answer(
            "✅ Добро пожаловать в админ-панель!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ Неверный пароль",
            reply_markup=get_cancel_keyboard()
        )

@router.message(F.text == '🚪 Выйти из меню')
async def logout_menu(message: Message):
    await message.answer("👋 Возврат в главное меню", reply_markup=get_main_keyboard())

@router.message(F.text == '➕ Добавить товар')
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Выберите способ добавления:",
        reply_markup=get_add_product_choice()
    )

@router.callback_query(F.data == 'add_manual')
async def add_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        f"Введите название товара (макс. {config.MAX_NAME_LENGTH} символов):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProduct.name)

@router.callback_query(F.data == 'add_import')
async def add_import(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    template_text = (
        "📁 Отправьте Excel файл для импорта\n\n"
        "📋 Формат файла:\n"
        "• Колонка A: Название\n"
        "• Колонка B: Описание\n"
        "• Колонка C: Цена\n\n"
        f"⚠️ Ограничения:\n"
        f"• Название: до {config.MAX_NAME_LENGTH} символов\n"
        f"• Описание: до {config.MAX_DESCRIPTION_LENGTH} символов\n"
        f"• Цена: от {config.MIN_PRICE} до {config.MAX_PRICE} ₽\n\n"
        "ℹ️ Фото можно добавить через редактирование"
    )
    await callback.message.answer(template_text, reply_markup=get_cancel_keyboard())
    await state.set_state(ImportProducts.waiting_file)

@router.message(ImportProducts.waiting_file, F.text == '❌ Отмена')
async def cancel_import(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(ImportProducts.waiting_file, F.document)
async def import_excel(message: Message, state: FSMContext):
    try:
        file = await message.bot.get_file(message.document.file_id)
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        filepath = temp_dir / f"{message.document.file_id}.xlsx"
        await message.bot.download_file(file.file_path, filepath)
        
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        
        added = 0
        skipped = []
        
        for idx, row in enumerate(ws.iter_rows(min_row=1, values_only=True), start=1):
            if not row[0]:
                continue

            if len(row) < 3:
                skipped.append(f"Строка {idx}: недостаточно колонок")
                continue

            name = str(row[0]).strip()
            description = str(row[1]).strip() if row[1] else ''
            try:
                price = float(row[2])
            except:
                skipped.append(f"Строка {idx}: неверная цена")
                continue
            
            if len(name) > config.MAX_NAME_LENGTH:
                skipped.append(f"Строка {idx}: название слишком длинное")
                continue
            if len(description) > config.MAX_DESCRIPTION_LENGTH:
                skipped.append(f"Строка {idx}: описание слишком длинное")
                continue
            if price < config.MIN_PRICE or price > config.MAX_PRICE:
                skipped.append(f"Строка {idx}: цена вне диапазона")
                continue
            
            Product.create(name=name, description=description, price=price)
            added += 1
        
        filepath.unlink()
        
        result = f"✅ Импортировано: {added} товар(ов)\n"
        if skipped:
            result += f"\n⚠️ Пропущено {len(skipped)} строк:\n"
            result += '\n'.join(skipped[:5])
            if len(skipped) > 5:
                result += f"\n... и ещё {len(skipped)-5}"
        
        await message.answer(result, reply_markup=get_admin_keyboard())
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка импорта: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()

@router.message(AddProduct.name, F.text == '❌ Отмена')
async def cancel_add(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(AddProduct.name)
async def add_name(message: Message, state: FSMContext):
    if len(message.text) > config.MAX_NAME_LENGTH:
        await message.answer(
            f"❌ Название слишком длинное (макс. {config.MAX_NAME_LENGTH} символов)",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        f"Введите описание (макс. {config.MAX_DESCRIPTION_LENGTH} символов):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProduct.description)

@router.message(AddProduct.description, F.text == '❌ Отмена')
async def cancel_desc(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(AddProduct.description)
async def add_desc(message: Message, state: FSMContext):
    if len(message.text) > config.MAX_DESCRIPTION_LENGTH:
        await message.answer(
            f"❌ Описание слишком длинное (макс. {config.MAX_DESCRIPTION_LENGTH} символов)",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(description=message.text)
    await message.answer(
        f"Введите цену ({config.MIN_PRICE}-{config.MAX_PRICE} ₽):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProduct.price)

@router.message(AddProduct.price, F.text == '❌ Отмена')
async def cancel_price(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(AddProduct.price)
async def add_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
        if price < config.MIN_PRICE or price > config.MAX_PRICE:
            await message.answer(
                f"❌ Цена должна быть от {config.MIN_PRICE} до {config.MAX_PRICE} ₽",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await state.update_data(price=price)
        await message.answer(
            "Отправьте фото или пропустите:",
            reply_markup=get_skip_photo_keyboard()
        )
        await state.set_state(AddProduct.photo)
    except:
        await message.answer("❌ Введите число", reply_markup=get_cancel_keyboard())

@router.callback_query(AddProduct.photo, F.data == 'skip_photo')
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    Product.create(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        photo_path=None
    )
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Товар '{data['name']}' добавлен!",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()

@router.message(AddProduct.photo, F.photo)
async def add_with_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    filename = f"{data['name'].replace(' ', '_')}_{photo.file_id}.jpg"
    filepath = config.PHOTOS_PATH / filename
    
    await message.bot.download_file(file_info.file_path, filepath)
    photo_url = f"/static/assets/photos/{filename}"
    
    Product.create(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        photo_path=photo_url
    )
    await message.answer(
        f"✅ Товар '{data['name']}' добавлен с фото!",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()

@router.message(F.text == '✏️ Редактировать товары')
async def edit_products_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    products = list(Product.select().where(Product.is_active == True))
    if not products:
        await message.answer("❌ Нет товаров", reply_markup=get_admin_keyboard())
        return
    
    keyboard = create_pagination_keyboard(
        items=products,
        page=0,
        per_page=10,
        callback_prefix='products',
        get_button_text=lambda p: f"{p.name} — {float(p.price):.2f} ₽",
        get_button_data=lambda p: f"product_{p.id}"
    )
    
    await message.answer("📦 Выберите товар:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('products_page_'))
async def products_pagination(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1])
    products = list(Product.select().where(Product.is_active == True))
    
    keyboard = create_pagination_keyboard(
        items=products,
        page=page,
        per_page=10,
        callback_prefix='products',
        get_button_text=lambda p: f"{p.name} — {float(p.price):.2f} ₽",
        get_button_data=lambda p: f"product_{p.id}"
    )
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(F.data.startswith('product_'))
async def show_product(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[1])
    product = Product.get_by_id(product_id)
    
    text = f"📦 {product.name}\n\n"
    text += f"📝 {product.description}\n\n"
    text += f"💰 Цена: {float(product.price):.2f} ₽"
    
    await callback.message.delete()
    
    if product.photo_path:
        await callback.message.answer_photo(
            photo=product.photo_path.replace('/static', 'https://localhost:5000/static'),
            caption=text,
            reply_markup=get_product_actions_keyboard(product_id)
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=get_product_actions_keyboard(product_id)
        )

@router.callback_query(F.data == 'back_to_products')
async def back_to_products(callback: CallbackQuery):
    products = list(Product.select().where(Product.is_active == True))
    keyboard = create_pagination_keyboard(
        items=products,
        page=0,
        per_page=10,
        callback_prefix='products',
        get_button_text=lambda p: f"{p.name} — {float(p.price):.2f} ₽",
        get_button_data=lambda p: f"product_{p.id}"
    )
    
    await callback.message.delete()
    await callback.message.answer("📦 Выберите товар:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('edit_name_'))
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await callback.message.answer(
        f"Введите новое название (макс. {config.MAX_NAME_LENGTH} символов):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProduct.edit_name)

@router.message(EditProduct.edit_name, F.text == '❌ Отмена')
async def cancel_edit_name(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(EditProduct.edit_name)
async def save_name(message: Message, state: FSMContext):
    if len(message.text) > config.MAX_NAME_LENGTH:
        await message.answer(
            f"❌ Название слишком длинное (макс. {config.MAX_NAME_LENGTH})",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    product = Product.get_by_id(data['product_id'])
    product.name = message.text
    product.save()
    
    await message.answer("✅ Название изменено!", reply_markup=get_admin_keyboard())
    await state.clear()

@router.callback_query(F.data.startswith('edit_desc_'))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await callback.message.answer(
        f"Введите новое описание (макс. {config.MAX_DESCRIPTION_LENGTH} символов):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProduct.edit_description)

@router.message(EditProduct.edit_description, F.text == '❌ Отмена')
async def cancel_edit_desc(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(EditProduct.edit_description)
async def save_desc(message: Message, state: FSMContext):
    if len(message.text) > config.MAX_DESCRIPTION_LENGTH:
        await message.answer(
            f"❌ Описание слишком длинное (макс. {config.MAX_DESCRIPTION_LENGTH})",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    product = Product.get_by_id(data['product_id'])
    product.description = message.text
    product.save()
    
    await message.answer("✅ Описание изменено!", reply_markup=get_admin_keyboard())
    await state.clear()

@router.callback_query(F.data.startswith('edit_price_'))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await callback.message.answer(
        f"Введите новую цену ({config.MIN_PRICE}-{config.MAX_PRICE} ₽):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProduct.edit_price)

@router.message(EditProduct.edit_price, F.text == '❌ Отмена')
async def cancel_edit_price(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(EditProduct.edit_price)
async def save_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
        if price < config.MIN_PRICE or price > config.MAX_PRICE:
            await message.answer(
                f"❌ Цена должна быть от {config.MIN_PRICE} до {config.MAX_PRICE} ₽",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        product = Product.get_by_id(data['product_id'])
        product.price = price
        product.save()
        
        await message.answer("✅ Цена изменена!", reply_markup=get_admin_keyboard())
        await state.clear()
    except:
        await message.answer("❌ Введите число", reply_markup=get_cancel_keyboard())

@router.callback_query(F.data.startswith('edit_photo_'))
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    await callback.message.answer(
        "Отправьте новое фото:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProduct.edit_photo)

@router.message(EditProduct.edit_photo, F.text == '❌ Отмена')
async def cancel_edit_photo(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_admin_keyboard())

@router.message(EditProduct.edit_photo, F.photo)
async def save_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    product = Product.get_by_id(data['product_id'])
    
    if product.photo_path:
        old_path = config.PHOTOS_PATH / Path(product.photo_path).name
        if old_path.exists():
            old_path.unlink()
    
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    filename = f"{product.name.replace(' ', '_')}_{photo.file_id}.jpg"
    filepath = config.PHOTOS_PATH / filename
    
    await message.bot.download_file(file_info.file_path, filepath)
    product.photo_path = f"/static/assets/photos/{filename}"
    product.save()
    
    await message.answer("✅ Фото изменено!", reply_markup=get_admin_keyboard())
    await state.clear()

@router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[1])
    product = Product.get_by_id(product_id)
    
    if product.photo_path:
        photo_path = config.PHOTOS_PATH / Path(product.photo_path).name
        if photo_path.exists():
            photo_path.unlink()
    
    product.delete_instance()
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Товар удалён",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == '📊 Статистика')
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    total_products = Product.select().where(Product.is_active == True).count()
    total_orders = Order.select().count()
    total_revenue = sum([float(o.total_amount) for o in Order.select()])
    
    await message.answer(
        f"📊 Статистика:\n\n"
        f"📦 Товаров: {total_products}\n"
        f"🛒 Заказов: {total_orders}\n"
        f"💰 Выручка: {total_revenue:.2f} ₽",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == '👥 Клиенты')
async def show_clients(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    orders = Order.select().where(Order.username.is_null(False))
    usernames = list(set([o.username for o in orders]))
    
    if not usernames:
        await message.answer("❌ Нет клиентов с username", reply_markup=get_admin_keyboard())
        return
    
    keyboard = create_pagination_keyboard(
        items=usernames,
        page=0,
        per_page=10,
        callback_prefix='clients',
        get_button_text=lambda u: f"@{u}",
        get_button_data=lambda u: f"client_{u}"
    )
    
    await message.answer("👥 Клиенты:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('clients_page_'))
async def clients_pagination(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1])
    orders = Order.select().where(Order.username.is_null(False))
    usernames = list(set([o.username for o in orders]))
    
    keyboard = create_pagination_keyboard(
        items=usernames,
        page=page,
        per_page=10,
        callback_prefix='clients',
        get_button_text=lambda u: f"@{u}",
        get_button_data=lambda u: f"client_{u}"
    )
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(F.data.startswith('client_'))
async def show_client_stats(callback: CallbackQuery):
    username = callback.data.split('_', 1)[1]
    
    orders = Order.select().where(Order.username == username)
    total_revenue = sum([float(o.total_amount) for o in orders])
    
    text = f"👤 Клиент: @{username}\n\n"
    text += f"🛒 Заказов: {orders.count()}\n"
    text += f"💰 Выручка: {total_revenue:.2f} ₽\n\n"
    text += "📦 Заказы:"

    keyboard = []
    for order in orders:
        keyboard.append([InlineKeyboardButton(
            text=f"#{order.id} — {float(order.total_amount):.2f} ₽",
            callback_data=f"order_{order.id}"
        )])

    keyboard.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_clients')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data == 'back_to_clients')
async def back_to_clients(callback: CallbackQuery):
    orders = Order.select().where(Order.username.is_null(False))
    usernames = list(set([o.username for o in orders]))
    
    keyboard = create_pagination_keyboard(
        items=usernames,
        page=0,
        per_page=10,
        callback_prefix='clients',
        get_button_text=lambda u: f"@{u}",
        get_button_data=lambda u: f"client_{u}"
    )
    
    await callback.message.edit_text("👥 Клиенты:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('order_'))
async def show_order_details(callback: CallbackQuery):
    order_id = int(callback.data.split('_')[1])
    order = Order.get_by_id(order_id)
    
    text = f"📋 Заказ #{order.id}\n\n"
    text += f"👤 {order.first_name} {order.last_name}\n"
    text += f"📞 {order.phone}\n"
    if order.username:
        text += f"👤 @{order.username}\n"
    text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"💰 {float(order.total_amount):.2f} ₽\n\n"
    text += "📦 Товары:\n"
    
    for item in order.items:
        text += f"  • {item.product_name} — {item.quantity} шт × {float(item.price):.2f} ₽\n"
    
    if order.comment:
        text += f"\n💬 {order.comment}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Назад', callback_data=f'client_{order.username}')]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.message(F.text == '📥 Получить Excel')
async def download_excel(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        if config.EXCEL_PATH.exists():
            file = FSInputFile(config.EXCEL_PATH)
            await message.answer_document(file, caption="📥 Заказы")
        else:
            await message.answer("❌ Файл не найден", reply_markup=get_admin_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=get_admin_keyboard())
