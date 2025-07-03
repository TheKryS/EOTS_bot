import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import API_TOKEN
from src.utils import logger
from src.bot_handlers import register_handlers
from src.hardware_monitor import check_thresholds

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Регистрация обработчиков
register_handlers(router)

# Запуск бота
async def main():
    # Запуск мониторинга
    asyncio.create_task(check_thresholds(bot))
    
    # Запуск бота
    logging.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен") 