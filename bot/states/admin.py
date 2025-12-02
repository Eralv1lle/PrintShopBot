from aiogram.fsm.state import State, StatesGroup

class AdminAuth(StatesGroup):
    waiting_password = State()

class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    photo = State()

class EditProduct(StatesGroup):
    edit_name = State()
    edit_description = State()
    edit_price = State()
    edit_photo = State()

class ImportProducts(StatesGroup):
    waiting_file = State()

class UserOrders(StatesGroup):
    waiting_username = State()
