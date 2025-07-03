# Eye Of The Server (EOTS)

**Eye Of The Server (EOTS)** — это Telegram-бот для мониторинга состояния Linux-сервера в реальном времени.
Бот предоставляет информацию о загрузке и температуре CPU/GPU, состоянии памяти, дисков, сети, процессах, а также позволяет выполнять команды на сервере (с ограничениями по безопасности).

---

## Возможности

- Получение общей информации о системе (CPU, GPU, память, аптайм и др.)
- Мониторинг температуры и загрузки CPU/GPU
- Просмотр состояния оперативной памяти и swap
- Информация о дисках и сетевой статистике
- Просмотр списка процессов
- График загрузки CPU
- Выполнение команд в консоли (с фильтрацией опасных команд)
- Уведомления в Telegram при превышении пороговых значений загрузки/температуры
- Ведение логов использования бота

---

## Быстрый старт

1. **Клонируйте репозиторий:**
   ```sh
   git clone https://github.com/ВАШ_ЛОГИН/Eye_Of_The_Server_EOTS.git
   cd Eye_Of_The_Server_EOTS
   ```

2. **Установите зависимости:**
   ```sh
   pip install pipenv
   pipenv install
   ```

3. **Создайте файл `.env` в корне проекта и заполните его:**
   ```
   BOT_TOKEN=ваш_токен_бота
   ALLOWED_USERS=123456789,987654321
   ALLOWED_DIRECTORIES=/var/log,/tmp,/home,/opt,/usr/local
   FORBIDDEN_COMMANDS=rm -rf,mkfs,dd,fork,chmod 777,chmod -R 777,iptables,passwd,mount,umount,sudo,su,shutdown,init 0,init 6
   CPU_LOAD_THRESHOLD=90
   CPU_TEMP_THRESHOLD=80
   GPU_LOAD_THRESHOLD=90
   GPU_TEMP_THRESHOLD=80
   CHECK_INTERVAL=60
   ```

4. **Запустите бота:**
   ```sh
   pipenv run python main.py
   ```

---

## Структура проекта

- `main.py` — точка входа, запуск бота и мониторинга
- `src/bot_handlers.py` — обработчики команд и сообщений Telegram
- `src/hardware_monitor.py` — функции мониторинга железа и уведомлений
- `src/config.py` — загрузка конфигурации из `.env`
- `src/utils.py` — вспомогательные функции и логирование
- `logs/` — логи и графики

---

## Требования

- Python 3.8+
- Linux-сервер (бот ориентирован на Linux)
- Telegram-бот (создайте через @BotFather)
- Для мониторинга GPU: установленный пакет `pynvml` и поддерживаемая видеокарта NVIDIA

---

## Безопасность

- Доступ к боту ограничен по списку пользователей (`ALLOWED_USERS`)
- Опасные команды запрещены через переменную `FORBIDDEN_COMMANDS`
- Все действия логируются
