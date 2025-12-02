from peewee import *
from datetime import datetime

database_proxy = DatabaseProxy()

class BaseModel(Model):
    class Meta:
        database = database_proxy

class User(BaseModel):
    telegram_id = BigIntegerField(unique=True)
    username = CharField(null=True)
    is_admin = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'users'

class Product(BaseModel):
    name = CharField()
    description = TextField(null=True)
    price = DecimalField(max_digits=10, decimal_places=2)
    photo_path = CharField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'products'

class Order(BaseModel):
    first_name = CharField()
    last_name = CharField()
    phone = CharField()
    username = CharField(null=True)
    total_amount = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(default='pending')
    comment = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'orders'

class OrderItem(BaseModel):
    order = ForeignKeyField(Order, backref='items')
    product = ForeignKeyField(Product)
    product_name = CharField()
    quantity = IntegerField()
    price = DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        table_name = 'order_items'
