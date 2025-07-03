from dotenv import load_dotenv
import os

# Загрузка данных из .env
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(map(int, os.getenv("ALLOWED_USERS", "").split(",")))
ALLOWED_DIRECTORIES = set(os.getenv("ALLOWED_DIRECTORIES", "").split(","))
FORBIDDEN_COMMANDS = set(os.getenv("FORBIDDEN_COMMANDS", "").split(","))
CPU_LOAD_THRESHOLD = int(os.getenv("CPU_LOAD_THRESHOLD"))
CPU_TEMP_THRESHOLD = int(os.getenv("CPU_TEMP_THRESHOLD"))
GPU_LOAD_THRESHOLD = int(os.getenv("GPU_LOAD_THRESHOLD"))
GPU_TEMP_THRESHOLD = int(os.getenv("GPU_TEMP_THRESHOLD"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"))

# Состояние для отслеживания уже отправленных уведомлений
notification_state = {
    'cpu_load': False,
    'cpu_temp': False,
    'gpu_load': False,
    'gpu_temp': False
} 