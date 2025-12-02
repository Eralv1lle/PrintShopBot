import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import commands, admin, user_orders
from database import db_manager
from config import config

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        config.validate()
        db_manager.initialize()
        db_manager.create_tables()
        
        storage = MemoryStorage()
        bot = Bot(token=config.BOT_TOKEN)
        dp = Dispatcher(storage=storage)
        
        dp.include_router(admin.router)
        dp.include_router(user_orders.router)
        dp.include_router(commands.router)

        print("Bot started")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        db_manager.close()

if __name__ == '__main__':
    asyncio.run(main())
