# Print Shop Bot

Telegram-бот с веб-интерфейсом для управления интернет-магазином печатной продукции.

Бот: [@shops3d_bot](https://t.me/shops3d_bot)

## Возможности

### Для пользователей

- **Веб-магазин** - современный интерфейс с поиском и фильтрацией товаров
- **Корзина** - добавление товаров, изменение количества, просмотр итоговой суммы
- **Оформление заказа** - форма с валидацией полей (имя, фамилия, телефон, username, комментарий)
- **Мои заказы** - автоматический поиск заказов по username из Telegram, просмотр истории с pagination
- **Уведомления** - toast-сообщения при ошибках ввода и успешных действиях

### Для администраторов

#### Вход в админку (пароль: admin)

1. Отправить `/admin` боту
2. Ввести пароль (указывается в `.env`, на данный момент пароль: admin)
3. После успешного входа статус `is_admin` сохраняется навсегда в базе данных
4. Кнопка "Выйти из меню" возвращает в главное меню, но НЕ убирает права администратора

#### Управление товарами

**Добавление товаров:**
- Вручную - пошаговый ввод: название → описание → цена → фото (можно пропустить)
- Из Excel - массовый импорт, формат файла: Название | Описание | Цена
- Валидация: название ≤100 символов, описание ≤500, цена 0.01-1000000

**Редактирование товаров:**
- Список товаров с pagination (10 на странице)
- Клик на товар → карточка с фото и inline-кнопками:
  - Изменить название
  - Изменить описание
  - Изменить цену
  - Изменить фото (старое автоматически удаляется)
  - Удалить товар (с удалением фото)

#### Управление заказами

**Статистика:**
- Количество активных товаров
- Общее количество заказов
- Общая выручка

**Клиенты:**
- Список всех клиентов с username (pagination 10 шт)
- Клик на клиента → статистика:
  - Количество заказов
  - Общая сумма покупок
  - Список всех заказов с inline-кнопками
- Клик на заказ → детали с составом и ценами

**Экспорт в Excel:**
- Выгрузка всех заказов с динамическими столбцами
- Формат: Дата | Имя | Фамилия | Телефон | Username | Название товара 1 | Количество 1 | Название товара 2 | Количество 2 | ...

**Уведомления:**
- При создании заказа ВСЕ администраторы получают сообщение с деталями

### Технические особенности

#### База данных (SQLite) + ORM Peewee

**Таблицы:**
- `User` - пользователи (telegram_id, username, is_admin, created_at)
- `Product` - товары (name, description, price, photo_path, is_active)
- `Order` - заказы (first_name, last_name, phone, username, total_amount, status, comment)
- `OrderItem` - позиции заказа (order, product, product_name, quantity, price)

**Важно:** `product_name` сохраняется в `OrderItem` для истории, чтобы при удалении товара заказы оставались корректными.

#### Бот (aiogram 3)

**FSM состояния:**
- `AdminAuth` - авторизация администратора
- `AddProduct` - добавление товара вручную
- `ImportProducts` - импорт из Excel
- `EditProduct` - редактирование товара
- `UserOrders` - поиск заказов пользователя (НЕ используется, заменено автоматическим поиском)

**Pagination:**
- Универсальная функция `create_pagination_keyboard()` в `bot/utils/pagination.py`
- Используется для товаров, заказов, клиентов
- Параметры: items, page, per_page, callback_prefix, get_button_text, get_button_data

**Валидация:**
- Название товара: max 100 символов
- Описание: max 500 символов
- Цена: 0.01 - 1000000, поддержка копеек
- Импорт Excel: пропуск невалидных строк с выводом ошибок

#### Веб-интерфейс (Flask)

**Дизайн:**
- Цветовая схема: сине-темный, бежевый и белый
- Анимации: fadeInDown, fadeInUp, slideInRight, zoomIn
- Блокировка скролла при модальных окнах (без сдвига страницы)

**Функционал:**
- Поиск товаров в реальном времени
- Корзина (slide-over с правой стороны)
- Модальные окна для товаров и оформления заказа
- Валидация полей:
  - Телефон: только цифры и +
  - Username: только латиница, цифры и _
  - Префикс @ добавляется автоматически
- Toast-уведомления при ошибках ввода

**API endpoints:**
- `GET /api/products` - список активных товаров
- `POST /api/checkout` - создание заказа
  - Валидация обязательных полей
  - Сохранение в БД + Excel
  - Уведомление всем админам через asyncio

## Установка

### Требования

- Python 3.10+
- pip

### Клонирование репозитория

```bash
git clone https://github.com/Eralv1lle/PrintShopBot.git
```

### Зависимости

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
aiofiles==24.1.0
aiogram==3.22.0
aiohappyeyeballs==2.6.1
aiohttp==3.12.15
aiosignal==1.4.0
annotated-types==0.7.0
attrs==25.4.0
blinker==1.9.0
certifi==2025.11.12
cffi==2.0.0
click==8.3.1
colorama==0.4.6
cryptography==46.0.3
et_xmlfile==2.0.0
Flask==3.1.2
flask-cors==6.0.1
frozenlist==1.8.0
idna==3.11
itsdangerous==2.2.0
Jinja2==3.1.6
magic-filter==1.0.12
MarkupSafe==3.0.3
multidict==6.7.0
openpyxl==3.1.5
peewee==3.18.3
propcache==0.4.1
pycparser==2.23
pydantic==2.11.10
pydantic_core==2.33.2
pyOpenSSL==25.3.0
python-dotenv==1.2.1
typing-inspection==0.4.2
typing_extensions==4.15.0
Werkzeug==3.1.4
yarl==1.22.0
```

### Настройка

1. Скопировать `.env.example` в `.env`:

```bash
cp .env.example .env
```

2. Заполнить переменные окружения:

```env
BOT_TOKEN=
WEBAPP_URL=
ADMIN_PASSWORD=
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

3. Получить токен бота у [@BotFather](https://t.me/BotFather)

4. Настроить WebApp URL в BotFather (для продакшена)

### Запуск

#### Локальная разработка

**Два терминала**

Терминал 1 - Flask:
```bash
python app.py
```

Терминал 2 - Бот:
```bash
python main.py
```

#### Продакшен

Для продакшена рекомендуется:
- Использовать nginx как reverse proxy
- Настроить SSL сертификаты (Let's Encrypt)
- Запустить Flask через gunicorn или uwsgi
- Использовать systemd для автозапуска

Пример systemd service:

```ini
[Unit]
Description=Print Shop Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/print_shop
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Структура проекта

```
print_shop_v4/
├── bot/
│   ├── handlers/
│   │   ├── commands.py      # Основные команды (/start, /help, мои заказы)
│   │   ├── admin.py          # Админка (500+ строк)
│   │   └── user_orders.py    # Поиск заказов
│   ├── keyboards/
│   │   └── main.py           # Клавиатуры (главная, админ, inline)
│   ├── states/
│   │   └── states.py         # FSM состояния
│   └── utils/
│       └── pagination.py     # Универсальная pagination
├── web/
│   ├── api/
│   │   └── orders.py         # API для заказов
│   ├── models/
│   │   └── models.py         # ORM модели (Peewee)
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css    # Все стили (~900 строк)
│   │   └── js/
│   │       └── app.js        # Логика фронтенда
│   ├── templates/
│   │   └── index.html        # Главная страница
│   ├── utils/
│   │   └── excel_helper.py   # Работа с Excel
│
├── app.py                    # Точка входа сервера
├── config.py                 # Конфигурация
├── main.py                   # Точка входа бота
├── requirements.txt
├── .env.example
└── README.md
```

## База данных

### Миграции

База данных создаётся автоматически при первом запуске через `models.py`.

### Бэкап

Для бэкапа просто скопируйте файл `shop.db`:

```bash
cp shop.db shop_backup_$(date +%Y%m%d).db
```

### Сброс

Для полного сброса удалите `shop.db` и `orders.xlsx`, они будут пересозданы:

```bash
rm shop.db orders.xlsx
```

## Особенности реализации

### Постоянная админка

После ввода пароля флаг `is_admin=True` сохраняется в БД и не сбрасывается при выходе из меню. Проверка прав:

```python
user = User.get_or_none(User.telegram_id == user_id)
if user and user.is_admin:
    # Показать админку
```

### Поиск заказов по username

При нажатии "Мои заказы" бот автоматически берёт username из Telegram (`message.from_user.username`) и выполняет ТОЧНОЕ совпадение:

```python
orders = Order.select().where(Order.username == username)
```

Это удобнее чем запрашивать ввод, и исключает ошибки в написании.

### Редактирование с удалением фото

При замене фото товара старое удаляется из файловой системы:

```python
if product.photo_path:
    old_photo = Path(product.photo_path)
    if old_photo.exists():
        old_photo.unlink()
```

### Импорт из Excel

Формат файла: 3 колонки без заголовков (Название | Описание | Цена).

Валидация каждой строки:
- Пропуск пустых строк
- Проверка длины полей
- Проверка диапазона цены
- Вывод списка пропущенных строк с причинами

### Уведомления админам

При создании заказа через веб-интерфейс все админы получают уведомление:

```python
async def notify_admins(order_text):
    bot = Bot(token=config.BOT_TOKEN)
    admins = User.select().where(User.is_admin == True)
    for admin in admins:
        try:
            await bot.send_message(admin.telegram_id, order_text)
        except:
            pass
```

Используется `asyncio.run()` для синхронного вызова из Flask.

### Блокировка скролла

При открытии модальных окон скролл блокируется без сдвига контента:

```javascript
function calculateScrollbarWidth() {
    const outer = document.createElement('div');
    outer.style.visibility = 'hidden';
    outer.style.overflow = 'scroll';
    document.body.appendChild(outer);
    const inner = document.createElement('div');
    outer.appendChild(inner);
    const scrollbarWidth = outer.offsetWidth - inner.offsetWidth;
    document.body.removeChild(outer);
    return scrollbarWidth;
}

const scrollbarWidth = calculateScrollbarWidth();
document.documentElement.style.setProperty('--scrollbar-width', `${scrollbarWidth}px`);
```

CSS:
```css
body.modal-open {
    overflow: hidden;
    padding-right: var(--scrollbar-width, 0);
}
```

## API документация

### GET /api/products

Возвращает список активных товаров.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Футболка Print Shop",
        "description": "Качественная печать на 100% хлопке",
        "price": 1500.00,
        "photo_url": "/static/products/photo_123.jpg"
    }
]
```

### POST /api/checkout

Создаёт новый заказ.

**Request:**
```json
{
    "first_name": "Иван",
    "last_name": "Петров",
    "phone": "+79991234567",
    "username": "ivanpetrov",
    "comment": "Доставка после 18:00",
    "cart": [
        {
            "product_id": 1,
            "quantity": 2
        }
    ]
}
```

**Response (success):**
```json
{
    "success": true,
    "order_id": 42,
    "total_amount": 3000.00
}
```

**Response (error):**
```json
{
    "error": "Не указаны обязательные поля"
}
```

## Устранение неполадок

### Бот не отвечает

1. Проверьте токен в `.env`
2. Убедитесь что бот запущен: `python main.py`
3. Проверьте логи на наличие ошибок

### WebApp не открывается

1. Проверьте WEBAPP_URL в `.env`
2. Убедитесь что Flask запущен на правильном порту
3. Для локальной разработки используйте ngrok или localtunnel

### Фото не загружаются

1. Проверьте права на папку `web/static/assets/`
2. Убедитесь что путь `PHOTOS_PATH` в config.py правильный

### Заказы не сохраняются в Excel

1. Проверьте права на запись в текущую директорию
2. Убедитесь что файл `orders.xlsx` не открыт в Excel

## Автор

Разработано для [@shops3d_bot](https://t.me/shops3d_bot)

## Поддержка

По вопросам работы бота обращайтесь к администратору в Telegram: @pitonovichh
