from peewee import SqliteDatabase
from web.models import database_proxy, User, Product, Order, OrderItem
from config import config

class DatabaseManager:
    def __init__(self):
        self.db = None
        self.models = [User, Product, Order, OrderItem]
    
    def initialize(self):
        self.db = SqliteDatabase(config.DATABASE_PATH)
        database_proxy.initialize(self.db)
        return self.db
    
    def create_tables(self):
        with self.db:
            self.db.create_tables(self.models, safe=True)
    
    def close(self):
        if self.db and not self.db.is_closed():
            self.db.close()

db_manager = DatabaseManager()
