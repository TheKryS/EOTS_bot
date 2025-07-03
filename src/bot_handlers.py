from aiogram import Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import psutil
from datetime import datetime
import re

from .utils import log_command, is_user_allowed, execute_command
from .hardware_monitor import (get_system_info, get_cpu_temp, get_gpu_info,
                            plot_cpu_graph)
from .config import FORBIDDEN_COMMANDS

class ConsoleStates(StatesGroup):
    waiting_for_command = State()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Общая информация")],
            [KeyboardButton(text="🖥️ CPU"), KeyboardButton(text="🧠 RAM")],
            [KeyboardButton(text="🎮 GPU"), KeyboardButton(text="🔥 Температура")],
            [KeyboardButton(text="💾 Диск"), KeyboardButton(text="🌐 Сеть")],
            [KeyboardButton(text="📋 Процессы"), KeyboardButton(text="⏱️ Аптайм")],
            [KeyboardButton(text="⌨️ Консоль")],
        ],
        resize_keyboard=True
    )
    return keyboard

async def cmd_start(message: Message):
    log_command(message.from_user.id, "/start")
    
    if not is_user_allowed(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я бот для мониторинга состояния Linux-сервера.\n"
        f"Выберите опцию из меню ниже:",
        reply_markup=get_main_keyboard()
    )

async def cmd_help(message: Message):
    log_command(message.from_user.id, "/help")
    
    help_text = """
*Команды бота:*
/start - Запустить бота
/help - Показать справку
/status - Показать общую информацию о сервере

*Доступные функции через кнопки:*
📊 Общая информация - Базовая информация о системе
🖥️ CPU - Информация о загрузке процессора
🧠 RAM - Состояние оперативной памяти
🎮 GPU - Информация о загрузке графического ускорителя
🔥 Температура - Информация о температуре системы
💾 Диск - Информация о дисковом пространстве
🌐 Сеть - Сетевая статистика
📋 Процессы - Список активных процессов
⏱️ Аптайм - Время работы сервера
⌨️ Консоль - Консоль для управления сервером
"""
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

async def cmd_status(message: Message):
    if message.text == "/status":
        log_command(message.from_user.id, "/status")
    else:
        log_command(message.from_user.id, "📊 Общая информация")
    
    status_message = await message.answer("⏳ Сбор информации о системе...")
    system_info = await get_system_info()
    await message.bot.delete_message(chat_id=message.chat.id, message_id=status_message.message_id)
    await message.answer(system_info, parse_mode=ParseMode.MARKDOWN)

async def cpu_info(message: Message):
    log_command(message.from_user.id, "🖥️ CPU")
    
    cpu_message = await message.answer("⏳ Сбор информации о CPU...")
    
    physical_cores = psutil.cpu_count(logical=False)
    total_cores = psutil.cpu_count(logical=True)
    
    avg_temp, core_temps = await get_cpu_temp()
    
    cpu_freq = psutil.cpu_freq()
    
    cpu_usage_per_core = psutil.cpu_percent(percpu=True, interval=1)
    
    cpu_info = f"*Информация о CPU:*\n"
    cpu_info += f"*Температура CPU:* {avg_temp:.1f}°C\n"
    cpu_info += f"*Физические ядра:* {physical_cores}\n"
    cpu_info += f"*Всего ядер:* {total_cores}\n"
    
    if cpu_freq:
        cpu_info += f"*Максимальная частота:* {cpu_freq.max:.2f}MHz\n"
        cpu_info += f"*Минимальная частота:* {cpu_freq.min:.2f}MHz\n"
        cpu_info += f"*Текущая частота:* {cpu_freq.current:.2f}MHz\n"
    
    cpu_info += f"*Общая загрузка CPU:* {psutil.cpu_percent()}%\n\n"
    
    cpu_info += "*Загрузка по ядрам:*\n"
    for i, percentage in enumerate(cpu_usage_per_core):
        cpu_info += f"*Ядро {i+1}:* {percentage}%\n"
    
    plot_cpu_graph()
    photo = FSInputFile("logs/cpu_graph.png")
    await message.answer_photo(photo)
    
    await message.bot.delete_message(chat_id=message.chat.id, message_id=cpu_message.message_id)
    await message.answer(cpu_info, parse_mode=ParseMode.MARKDOWN)

async def ram_info(message: Message):
    log_command(message.from_user.id, "🧠 RAM")
    
    ram_message = await message.answer("⏳ Сбор информации о RAM...")
    
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    ram_info = f"*Информация о RAM:*\n"
    ram_info += f"*Всего:* {memory.total / (1024**3):.2f} GB\n"
    ram_info += f"*Доступно:* {memory.available / (1024**3):.2f} GB\n"
    ram_info += f"*Использовано:* {memory.used / (1024**3):.2f} GB\n"
    ram_info += f"*Процент использования:* {memory.percent}%\n\n"
    
    ram_info += f"*Информация о SWAP:*\n"
    ram_info += f"*Всего:* {swap.total / (1024**3):.2f} GB\n"
    ram_info += f"*Использовано:* {swap.used / (1024**3):.2f} GB\n"
    ram_info += f"*Свободно:* {swap.free / (1024**3):.2f} GB\n"
    ram_info += f"*Процент использования:* {swap.percent}%\n"
    
    await message.bot.delete_message(chat_id=message.chat.id, message_id=ram_message.message_id)
    await message.answer(ram_info, parse_mode=ParseMode.MARKDOWN)

async def gpu_info(message: Message):
    log_command(message.from_user.id, "🎮 GPU")
    
    temp_message = await message.answer("⏳ Сбор информации о GPU...")
    gpu_utilization, gpu_temp = get_gpu_info()
    await message.bot.delete_message(chat_id=message.chat.id, message_id=temp_message.message_id)
    if gpu_utilization is not None:
        info = (
            f"*Информация о GPU:*\n"
            f"Загрузка GPU: {gpu_utilization}\n"
            f"Температура GPU: {gpu_temp}"
        )
    else:
        info = "❌ Данные о GPU недоступны."
    await message.answer(info, parse_mode=ParseMode.MARKDOWN)

async def temp_info(message: Message):
    log_command(message.from_user.id, "🔥 Температура")
    
    temp_message = await message.answer("⏳ Сбор информации о температуре...")
    avg_temp, core_temps = await get_cpu_temp()
    gpu_utilization, gpu_temp = get_gpu_info()
    
    if avg_temp is None and gpu_temp is None:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=temp_message.message_id)
        await message.answer("❌ Температура недоступна.", parse_mode=ParseMode.MARKDOWN)
        return
        
    temp_info = "*Информация о температуре:*\n"
    if avg_temp is not None:
        temp_info += f"*Общая температура процессора:* {avg_temp:.1f}°C\n\n"
        temp_info += "*Температура по ядрам:*\n"
        for i, temp in core_temps.items():
            temp_info += f"*Ядро {i+1}:* {temp:.1f}°C\n"
        temp_info += "\n"
    if gpu_temp is not None:
        temp_info += f"*Температура GPU:* {gpu_temp}\n"
        
    await message.bot.delete_message(chat_id=message.chat.id, message_id=temp_message.message_id)
    await message.answer(temp_info, parse_mode=ParseMode.MARKDOWN)

async def disk_info(message: Message):
    log_command(message.from_user.id, "💾 Диск")
    
    disk_message = await message.answer("⏳ Сбор информации о дисках...")
    
    disk_info = "*Информация о дисках:*\n\n"
    
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk_info += f"*Раздел:* {partition.mountpoint}\n"
            disk_info += f"*Файловая система:* {partition.fstype}\n"
            disk_info += f"*Всего:* {partition_usage.total / (1024**3):.2f} GB\n"
            disk_info += f"*Использовано:* {partition_usage.used / (1024**3):.2f} GB\n"
            disk_info += f"*Свободно:* {partition_usage.free / (1024**3):.2f} GB\n"
            disk_info += f"*Процент использования:* {partition_usage.percent}%\n\n"
        except:
            continue
    
    disk_io = psutil.disk_io_counters()
    if disk_io:
        disk_info += "*Статистика дисковых операций:*\n"
        disk_info += f"*Всего прочитано:* {disk_io.read_bytes / (1024**3):.2f} GB\n"
        disk_info += f"*Всего записано:* {disk_io.write_bytes / (1024**3):.2f} GB\n"
    
    await message.bot.delete_message(chat_id=message.chat.id, message_id=disk_message.message_id)
    await message.answer(disk_info, parse_mode=ParseMode.MARKDOWN)

async def network_info(message: Message):
    log_command(message.from_user.id, "🌐 Сеть")
    
    network_message = await message.answer("⏳ Сбор информации о сети...")
    
    network_info = "*Информация о сети:*\n\n"
    
    net_if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in net_if_addrs.items():
        network_info += f"*Интерфейс:* {interface_name}\n"
        for address in interface_addresses:
            if address.family == psutil.AF_LINK:
                network_info += f"*MAC-адрес:* {address.address}\n"
            elif address.family == 2:  # IPv4
                network_info += f"*IPv4-адрес:* {address.address}\n"
            elif address.family == 30:  # IPv6
                network_info += f"*IPv6-адрес:* {address.address}\n"
        network_info += "\n"
    
    net_io = psutil.net_io_counters()
    if net_io:
        network_info += "*Статистика сетевого ввода-вывода:*\n"
        network_info += f"*Всего байт отправлено:* {net_io.bytes_sent / (1024**2):.2f} MB\n"
        network_info += f"*Всего байт получено:* {net_io.bytes_recv / (1024**2):.2f} MB\n"
        network_info += f"*Пакетов отправлено:* {net_io.packets_sent}\n"
        network_info += f"*Пакетов получено:* {net_io.packets_recv}\n"
    
    await message.bot.delete_message(chat_id=message.chat.id, message_id=network_message.message_id)
    await message.answer(network_info, parse_mode=ParseMode.MARKDOWN)

def escape_markdown_v2(text: str) -> str:
    """Экранирует специальные символы для Markdown V2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def process_info(message: Message):
    log_command(message.from_user.id, "📋 Процессы")
    
    process_message = await message.answer("⏳ Сбор информации о процессах...")
    
    processes_info = "<b>Информация о процессах:</b>\n\n"
    processes_info += "<b>Топ-10 процессов по использованию CPU:</b>\n"
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            proc_info = proc.info
            proc_info['cpu_percent'] = proc.cpu_percent(interval=0.1)
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    
    for i, proc in enumerate(processes[:10], 1):
        processes_info += f"{i}. <b>PID:</b> {proc['pid']}, <b>Имя:</b> {proc['name']}, <b>CPU:</b> {proc['cpu_percent']:.1f}%, <b>RAM:</b> {proc['memory_percent']:.1f}%\n"
    
    processes_info += f"\n<b>Всего процессов:</b> {len(processes)}"
    
    await message.bot.delete_message(chat_id=message.chat.id, message_id=process_message.message_id)
    await message.answer(processes_info, parse_mode=ParseMode.HTML)

async def uptime_info(message: Message):
    log_command(message.from_user.id, "⏱️ Аптайм")
    
    uptime_message = await message.answer("⏳ Сбор информации об аптайме...")
    
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_info = "*Информация об аптайме:*\n\n"
    uptime_info += f"*Время запуска:* {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    uptime_info += f"*Аптайм:* {days} дн. {hours} ч. {minutes} мин. {seconds} сек."
    
    await message.bot.delete_message(chat_id=message.chat.id, message_id=uptime_message.message_id)
    await message.answer(uptime_info, parse_mode=ParseMode.MARKDOWN)

async def console_command(message: Message, state: FSMContext):
    log_command(message.from_user.id, "⌨️ Консоль")
    
    if not is_user_allowed(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к консоли.")
        return
    
    await state.set_state(ConsoleStates.waiting_for_command)
    await message.answer(
        "🖥️ Режим консоли активирован.\n\n"
        "Введите команду для выполнения.\n"
        "Для выхода введите 'exit' или 'quit'.\n\n"
        "⚠️ Примечание: некоторые команды заблокированы в целях безопасности."
    )

async def handle_console_command(message: Message, state: FSMContext):
    command = message.text.strip()
    
    if command.lower() in ['exit', 'quit']:
        await state.clear()
        await message.answer(
            "Выход из режима консоли.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Проверка на запрещённые команды
    base_cmd = command.split()[0].lower()
    if base_cmd in FORBIDDEN_COMMANDS:
        await message.answer(f"⛔ Команда '{base_cmd}' запрещена к выполнению.")
        return

    log_command(message.from_user.id, f"Console: {command}")
    
    result = await execute_command(command)
    
    if len(result) > 4000:
        result = result[:4000] + "\n... (вывод обрезан)"
    
    await message.answer(f"📝 Результат выполнения команды:\n\n```\n{result}\n```", parse_mode=ParseMode.MARKDOWN)

async def unknown_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return
        
    log_command(message.from_user.id, f"Неизвестная команда: {message.text}")
    
    await message.answer(
        "Извините, я не понимаю эту команду.\nВоспользуйтесь кнопками меню или введите /help для справки.",
        reply_markup=get_main_keyboard()
    )

def register_handlers(router: Router):
    router.message.register(cmd_start, CommandStart())
    router.message.register(cmd_help, Command("help"))
    router.message.register(cmd_status, Command("status"))
    router.message.register(cmd_status, F.text == "📊 Общая информация")
    router.message.register(cpu_info, F.text == "🖥️ CPU")
    router.message.register(ram_info, F.text == "🧠 RAM")
    router.message.register(gpu_info, F.text == "🎮 GPU")
    router.message.register(temp_info, F.text == "🔥 Температура")
    router.message.register(disk_info, F.text == "💾 Диск")
    router.message.register(network_info, F.text == "🌐 Сеть")
    router.message.register(process_info, F.text == "📋 Процессы")
    router.message.register(uptime_info, F.text == "⏱️ Аптайм")
    router.message.register(console_command, F.text == "⌨️ Консоль")
    router.message.register(handle_console_command, ConsoleStates.waiting_for_command)
    router.message.register(unknown_message) 