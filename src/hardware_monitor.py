import psutil
import platform
from datetime import datetime
import matplotlib.pyplot as plt
import time
import asyncio
from aiogram.enums import ParseMode
from .utils import logger

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except (ImportError, pynvml.NVMLError, pynvml.NVMLError_LibraryNotFound):
    GPU_AVAILABLE = False

async def get_cpu_temp():
    if hasattr(psutil, "sensors_temperatures"):
        temperatures = psutil.sensors_temperatures()
        if not temperatures:
            return 0, {}
        temp_values = []
        core_temps = {}
        for sensor, entries in temperatures.items():
            for i, entry in enumerate(entries):
                    temp_values.append(entry.current)
                    core_temps[i] = entry.current
        if temp_values:
            avg_temp = sum(temp_values) / len(temp_values)  # Средняя температура
            return avg_temp, core_temps
    return 0, {}

def get_gpu_info():
    if not GPU_AVAILABLE:
        return "N/A", "N/A"

    try:
        gpu_count = pynvml.nvmlDeviceGetCount()
        if gpu_count == 0:
            return "Нет доступных видеокарт", "N/A"
        total_utilization = 0
        total_temperature = 0
        for i in range(gpu_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

            total_utilization += utilization
            total_temperature += temperature
        avg_utilization = total_utilization / gpu_count
        avg_temperature = total_temperature / gpu_count
        return f"{avg_utilization:.1f}%", f"{avg_temperature:.1f}°C"
    except pynvml.NVMLError:
        return "Ошибка GPU", "Ошибка"

def collect_cpu_data(duration=10, interval=1):
    timestamps = []
    cpu_usage = []
    for i in range(duration):
        timestamps.append(i * interval)
        cpu_usage.append(psutil.cpu_percent())
        time.sleep(interval)
    return timestamps, cpu_usage

def plot_cpu_graph():
    timestamps, cpu_usage = collect_cpu_data()
    plt.figure(figsize=(6, 3))
    plt.plot(timestamps, cpu_usage, marker='o', linestyle='-', color='b', label='CPU %')
    plt.xlabel('Время (сек)')
    plt.ylabel('Загрузка CPU (%)')
    plt.title('График загрузки CPU')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig("logs/cpu_graph.png")
    plt.close()

async def get_system_info():
    uname = platform.uname()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    avg_temp, core_temps = await get_cpu_temp()
    gpu_utilization, gpu_temp = get_gpu_info()
    
    system_info = f"*Информация о системе:*\n"
    system_info += f"*Система:* {uname.system}\n"
    system_info += f"*Имя узла:* {uname.node}\n"
    system_info += f"*Релиз:* {uname.release}\n"
    system_info += f"*Версия:* {uname.version}\n"
    system_info += f"*Машина:* {uname.machine}\n"
    system_info += f"*Процессор:* {uname.processor}\n"
    system_info += f"*Загрузка CPU:* {psutil.cpu_percent()}%\n"
    system_info += f"*Температура CPU:* {avg_temp:.1f}°C\n"
    system_info += f"*Загрузка GPU:* {gpu_utilization}\n"
    system_info += f"*Температура GPU:* {gpu_temp}\n"
    system_info += f"*Память:* {psutil.virtual_memory().percent}% использовано\n"
    system_info += f"*Время запуска:* {boot_time.strftime('%d.%m.%Y %H:%M:%S')}"
    
    return system_info

async def check_thresholds(bot):
    """Проверяет пороговые значения и отправляет уведомления"""
    from .config import (CPU_LOAD_THRESHOLD, CPU_TEMP_THRESHOLD, 
                       GPU_LOAD_THRESHOLD, GPU_TEMP_THRESHOLD,
                       CHECK_INTERVAL, ALLOWED_USERS, notification_state)
    
    while True:
        try:
            # Проверка CPU
            cpu_load = psutil.cpu_percent()
            avg_temp, _ = await get_cpu_temp()
            
            # Проверка GPU
            gpu_utilization, gpu_temp = get_gpu_info()
            gpu_utilization = float(gpu_utilization.replace('%', '')) if gpu_utilization != 'N/A' else 0
            gpu_temp = float(gpu_temp.replace('°C', '')) if gpu_temp != 'N/A' else 0
            
            # Формирование сообщения об уведомлениях
            notifications = []
            
            # CPU Load
            if cpu_load > CPU_LOAD_THRESHOLD and not notification_state['cpu_load']:
                notifications.append(f"⚠️ Высокая загрузка CPU: {cpu_load}%")
                notification_state['cpu_load'] = True
            elif cpu_load <= CPU_LOAD_THRESHOLD:
                notification_state['cpu_load'] = False
                
            # CPU Temp
            if avg_temp > CPU_TEMP_THRESHOLD and not notification_state['cpu_temp']:
                notifications.append(f"🌡️ Высокая температура CPU: {avg_temp:.1f}°C")
                notification_state['cpu_temp'] = True
            elif avg_temp <= CPU_TEMP_THRESHOLD:
                notification_state['cpu_temp'] = False
                
            # GPU Load
            if gpu_utilization > GPU_LOAD_THRESHOLD and not notification_state['gpu_load']:
                notifications.append(f"⚠️ Высокая загрузка GPU: {gpu_utilization}%")
                notification_state['gpu_load'] = True
            elif gpu_utilization <= GPU_LOAD_THRESHOLD:
                notification_state['gpu_load'] = False
                
            # GPU Temp
            if gpu_temp > GPU_TEMP_THRESHOLD and not notification_state['gpu_temp']:
                notifications.append(f"🌡️ Высокая температура GPU: {gpu_temp:.1f}°C")
                notification_state['gpu_temp'] = True
            elif gpu_temp <= GPU_TEMP_THRESHOLD:
                notification_state['gpu_temp'] = False
                
            # Отправка уведомлений
            if notifications:
                message = "🔔 *Уведомление о состоянии системы:*\n\n" + "\n".join(notifications)
                for user_id in ALLOWED_USERS:
                    try:
                        await bot.send_message(user_id, message, parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Ошибка при проверке пороговых значений: {str(e)}")
            
        await asyncio.sleep(CHECK_INTERVAL) 