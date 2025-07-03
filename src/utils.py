import logging
from logging.handlers import TimedRotatingFileHandler
import asyncio
import subprocess
import shlex

# Настройка логирования
handler = TimedRotatingFileHandler(
    "logs/bot_usage.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_command(user, command):
    logger.info(f"Пользователь: {user}, Команда: {command}")

def is_user_allowed(user_id: int) -> bool:
    from .config import ALLOWED_USERS
    return user_id in ALLOWED_USERS

async def execute_command(command: str) -> str:
    """Выполняет команду и возвращает результат"""
    try:
        # Устанавливаем ограничение на размер вывода (1MB)
        process = await asyncio.create_subprocess_exec(
            *shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            limit=1024*1024  # 1MB
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
            
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='replace')
                return output if output else "Команда выполнена успешно (нет вывода)"
            else:
                error = stderr.decode('utf-8', errors='replace')
                return f"Ошибка: {error}"
                
        except asyncio.TimeoutError:
            process.kill()
            return "Ошибка: превышено время выполнения команды (10 секунд)"
            
    except Exception as e:
        return f"Ошибка при выполнении команды: {str(e)}" 