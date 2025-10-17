#!/usr/bin/env python3
"""
MVP Telegram-бот по безопасности РПРЗ
Основной файл бота с 3 основными функциями безопасности
"""

import csv
import json
import os
import signal
import ssl
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psutil
import telebot
import urllib3
from dotenv import load_dotenv
from flask import Flask, jsonify
from loguru import logger
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

try:
    from bot.handlers import (
        finish_danger_report,
        get_back_keyboard,
        get_danger_keyboard,
        get_main_menu_keyboard,
        get_media_keyboard,
        handle_danger_report_location,
        handle_danger_report_media,
        handle_danger_report_text,
        handle_improvement_suggestion_text,
        handle_rprz_assistant_text,
        log_activity,
        set_bot_instance,
    )
except ImportError:
    from handlers import (
        finish_danger_report,
        get_back_keyboard,
        get_danger_keyboard,
        get_main_menu_keyboard,
        get_media_keyboard,
        handle_danger_report_location,
        handle_danger_report_media,
        handle_danger_report_text,
        handle_improvement_suggestion_text,
        handle_rprz_assistant_text,
        log_activity,
        set_bot_instance,
    )

# Отключаем SSL предупреждения для тестирования
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Добавляем корневую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт обработчиков

# Импорт системы безопасности
# ТЕСТИРОВАНИЕ: Отключаем все ограничения безопасности
SECURITY_ENABLED = False
logger.warning("🧪 РЕЖИМ ТЕСТИРОВАНИЯ: Все ограничения безопасности отключены")


# Заглушки для функций безопасности (всегда разрешать)
def check_user_security(user_id, action="general"):
    return True, None


def validate_user_text(text, user_id):
    return True, None


def validate_user_file(file_size, file_type, user_id, max_size_mb=20):
    return True, None


# Импорт системы кэширования
try:
    from bot.cache import (
        cache,
        cache_shelter_data,
        cache_user_data,
        cleanup_cache,
        get_cached_shelter_data,
        get_cached_user_data,
    )

    CACHE_ENABLED = True
    logger.info("✅ Модуль кэширования загружен")
except ImportError:
    try:
        from cache import (
            cache,
            cache_shelter_data,
            cache_user_data,
            cleanup_cache,
            get_cached_shelter_data,
            get_cached_user_data,
        )

        CACHE_ENABLED = True
        logger.info("✅ Модуль кэширования загружен")
    except ImportError as e:
        CACHE_ENABLED = False
        logger.warning(f"⚠️ Модуль кэширования не загружен: {e}")

        # Заглушки для функций кэширования
        def cache_user_data(user_id, data, ttl=3600):
            pass

        def get_cached_user_data(user_id):
            return None

        def cache_shelter_data(shelter_id, data, ttl=7200):
            pass

        def get_cached_shelter_data(shelter_id):
            return None

        def cleanup_cache():
            pass


# Импорт оптимизированного процессора медиафайлов
try:
    from bot.media_processor import (
        get_media_processing_stats,
        process_media_file,
        validate_media_file,
    )

    MEDIA_PROCESSOR_ENABLED = True
    logger.info("✅ Модуль обработки медиафайлов загружен")
except ImportError:
    try:
        from media_processor import (
            get_media_processing_stats,
            process_media_file,
            validate_media_file,
        )

        MEDIA_PROCESSOR_ENABLED = True
        logger.info("✅ Модуль обработки медиафайлов загружен")
    except ImportError as e:
        MEDIA_PROCESSOR_ENABLED = False
        logger.warning(f"⚠️ Модуль обработки медиафайлов не загружен: {e}")

        # Заглушки для функций обработки медиафайлов
        def validate_media_file(file_size, mime_type, user_id):
            return True, ""

        def process_media_file(file_path, mime_type):
            return {"error": "Модуль обработки медиафайлов недоступен"}

        def get_media_processing_stats():
            return {"error": "Модуль недоступен"}


# Загрузка переменных окружения
# Сначала загружаем .env файл (для локальной разработки)
load_dotenv(".env", override=False)
# Затем загружаем системные переменные окружения (для Railway/продакшена)
# override=True позволяет системным переменным перезаписать .env файл
load_dotenv(override=True)

# Система блокировки процесса
PROJECT_ROOT = Path(__file__).parent.parent
LOCK_FILE = PROJECT_ROOT / "bot.lock"
PID_FILE = PROJECT_ROOT / "bot.pid"

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Отладочная информация для Railway
logger.info("🔍 Отладка переменных окружения:")
logger.info(f"BOT_TOKEN: {'установлен' if BOT_TOKEN else 'НЕ НАЙДЕН'}")
logger.info(f"ADMIN_CHAT_ID: {'установлен' if ADMIN_CHAT_ID else 'НЕ НАЙДЕН'}")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "300"))

# Email конфигурация удалена - используется yandex_notifications.py

# Функция для детального логирования ошибок админа


def log_admin_error(error_type: str, error: Exception, context: dict = None):
    """Логирует ошибку с детальной информацией для админа"""
    try:
        import traceback
        from datetime import datetime

        # Безопасная обработка контекста
        safe_context = context if isinstance(context, dict) else {}

        # Получаем детальную информацию об ошибке
        error_traceback = traceback.format_exc()
        error_line = (
            traceback.extract_tb(error.__traceback__)[-1].lineno
            if error.__traceback__
            else 0
        )
        error_file = (
            traceback.extract_tb(error.__traceback__)[-1].filename
            if error.__traceback__
            else "unknown"
        )

        # Создаем детальную запись ошибки
        error_details = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "exception_type": type(error).__name__,
            "error_message": str(error),
            "error_file": error_file,
            "error_line": error_line,
            "context": safe_context,
            "traceback": error_traceback,
        }

        # Логируем в основной лог ошибок с деталями
        logger.error(
            f"ADMIN_ERROR | {error_type} | {type(error).__name__}: {str(error)} | "
            f"File: {error_file}:{error_line}"
        )

        # Логируем в системный лог с дополнительной информацией
        logger.bind(
            error_type=error_type, error_file=error_file, error_line=error_line
        ).error(
            f"{type(error).__name__}: {str(error)} | Context: {safe_context} | Traceback: {error_traceback}"
        )

        # Если это критическая ошибка, логируем отдельно и отправляем уведомление
        if error_type in ["BOT_CRASH", "API_FAILURE", "CONFIG_ERROR"]:
            logger.critical(f"🚨 КРИТИЧЕСКАЯ ОШИБКА | {error_type} | {str(error)}")

            # Сохраняем критическую ошибку в отдельный файл для быстрого доступа
            try:
                critical_log_file = "logs/critical_errors.json"
                os.makedirs("logs", exist_ok=True)

                # Читаем существующие критические ошибки
                critical_errors = []
                if os.path.exists(critical_log_file):
                    try:
                        with open(critical_log_file, "r", encoding="utf-8") as f:
                            critical_errors = json.load(f)
                    except (json.JSONDecodeError, Exception):
                        critical_errors = []

                # Добавляем новую ошибку
                critical_errors.append(error_details)

                # Оставляем только последние 50 ошибок
                if len(critical_errors) > 50:
                    critical_errors = critical_errors[-50:]

                # Сохраняем
                with open(critical_log_file, "w", encoding="utf-8") as f:
                    json.dump(critical_errors, f, ensure_ascii=False, indent=2)

            except Exception as save_error:
                logger.error(f"Не удалось сохранить критическую ошибку: {save_error}")

    except Exception as log_error:
        # Если даже логирование не работает - используем print как последний резерв
        print(f"ОШИБКА ЛОГИРОВАНИЯ: {log_error}")
        print(f"Оригинальная ошибка: {error_type} - {error}")


# Функции для работы с блокировкой процесса
def check_running_bots():
    """Проверяет запущенные процессы бота"""
    running_bots = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["name"] in ["python.exe", "python"]:
                cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""
                if any(
                    keyword in cmdline.lower()
                    for keyword in ["bot", "main.py", "run_bot.py"]
                ):
                    running_bots.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return running_bots


def create_process_lock():
    """Создает блокировку процесса"""
    try:
        current_pid = os.getpid()

        # Проверяем существующие процессы
        running_bots = check_running_bots()
        if len(running_bots) > 1:  # Больше одного (включая текущий)
            logger.error("❌ Обнаружено несколько запущенных экземпляров бота!")
            logger.error(f"Запущенные процессы: {running_bots}")
            return False

        # Создаем файл блокировки
        lock_data = {
            "pid": current_pid,
            "started_at": datetime.now().isoformat(),
            "project_path": str(PROJECT_ROOT),
        }

        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2, ensure_ascii=False)

        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(current_pid))

        logger.info(f"✅ Создана блокировка процесса: PID {current_pid}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка создания блокировки: {e}")
        return False


def remove_process_lock():
    """Удаляет блокировку процесса"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        if PID_FILE.exists():
            PID_FILE.unlink()
        logger.info("✅ Блокировка процесса удалена")
    except Exception as e:
        logger.error(f"❌ Ошибка удаления блокировки: {e}")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"🛑 Получен сигнал {signum}, завершение работы...")
    remove_process_lock()
    sys.exit(0)


# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Flask приложение для Health Check
health_app = Flask(__name__)


@health_app.route("/health")
def health_check():
    """Health check endpoint для Railway с детальной информацией"""
    try:
        # Простая проверка рабочего времени без вызова функции
        moscow_offset = timedelta(hours=3)
        moscow_tz = timezone(moscow_offset)
        moscow_time = datetime.now(moscow_tz)
        current_hour = moscow_time.hour
        working_hours = 7 <= current_hour < 19

        # Собираем информацию о производительности
        health_data = {
            "status": "healthy",
            "service": "telegram-bot",
            "working_hours": working_hours,
            "current_time_moscow": moscow_time.strftime("%H:%M"),
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "security": SECURITY_ENABLED,
                "cache": CACHE_ENABLED,
                "media_processor": MEDIA_PROCESSOR_ENABLED,
                "notifications": getattr(
                    sys.modules.get("bot.handlers", None),
                    "NOTIFICATIONS_AVAILABLE",
                    False,
                ),
            },
        }

        # Добавляем статистику кэша если доступна
        if CACHE_ENABLED:
            try:
                cache_stats = cache.get_stats()
                health_data["cache_stats"] = {
                    "total_items": cache_stats["total_items"],
                    "valid_items": cache_stats["valid_items"],
                    "memory_usage": cache_stats["memory_usage"],
                }
            except Exception as e:
                health_data["cache_stats"] = {"error": str(e)}

        # Добавляем статистику обработки медиафайлов если доступна
        if MEDIA_PROCESSOR_ENABLED:
            try:
                media_stats = get_media_processing_stats()
                health_data["media_stats"] = media_stats
            except Exception as e:
                health_data["media_stats"] = {"error": str(e)}

        # Добавляем информацию о системе
        try:
            health_data["system"] = {
                "active_users": len(user_states) if "user_states" in globals() else 0,
                "uptime": time.time() - os.path.getctime(__file__)
                if os.path.exists(__file__)
                else 0,
            }
        except Exception:
            health_data["system"] = {
                "error": "Не удалось получить системную информацию"
            }

        return jsonify(health_data)

    except Exception as e:
        logger.error(f"Ошибка в health check: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@health_app.route("/")
def root():
    """Root endpoint"""
    return jsonify({"service": "RPRZ Telegram Bot", "status": "running"})


# Функция для маскирования чувствительных данных


def is_working_hours() -> bool:
    """Проверяет рабочее время: 7:00-19:00 МСК"""
    # МСК = UTC+3
    moscow_offset = timedelta(hours=3)
    moscow_tz = timezone(moscow_offset)
    moscow_time = datetime.now(moscow_tz)
    current_hour = moscow_time.hour

    # Рабочие часы: 7:00-19:00
    return 7 <= current_hour < 19


def check_and_shutdown_if_needed():
    """Проверяет время и останавливает бот если нерабочее время"""
    if not is_working_hours():
        moscow_offset = timedelta(hours=3)
        moscow_tz = timezone(moscow_offset)
        moscow_time = datetime.now(moscow_tz)
        logger.warning(
            f"⏰ Нерабочее время! Текущее время МСК: {moscow_time.strftime('%H:%M')}. "
            f"Бот останавливается для экономии ресурсов."
        )
        logger.info("🕐 Рабочие часы бота: 7:00-19:00 МСК")
        sys.exit(0)


def mask_sensitive_data(text: str) -> str:
    """Маскирует чувствительные данные в логах"""
    if not text:
        return ""

    # Маскируем токен бота (формат: BOT_ID:BOT_TOKEN)
    if ":" in text and len(text) > 20:
        parts = text.split(":")
        if len(parts) == 2 and parts[0].isdigit():
            return f"{parts[0]}:***{parts[1][-4:]}"

    # Маскируем длинные строки (возможно токены)
    if len(text) > 20:
        return f"{text[:8]}***{text[-4:]}"

    return text


# Функция для санитизации пользовательского ввода


def sanitize_user_input(text: str) -> str:
    """Санитизирует пользовательский ввод для предотвращения XSS и инъекций"""
    if not text:
        return ""

    # Удаляем потенциально опасные символы
    dangerous_chars = ["<", ">", '"', "'", "&", ";", "|", "`", "$", "(", ")", "{", "}"]
    sanitized = text

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Удаляем опасные ключевые слова
    dangerous_keywords = [
        "script",
        "javascript",
        "vbscript",
        "onload",
        "onerror",
        "onclick",
        "iframe",
        "object",
        "embed",
        "form",
        "input",
        "select",
        "option",
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
        "SELECT",
        "UNION",
        "OR",
        "AND",
        "rm",
        "del",
        "format",
        "shutdown",
        "reboot",
        "kill",
        "taskkill",
    ]

    for keyword in dangerous_keywords:
        sanitized = sanitized.replace(keyword, "")
        sanitized = sanitized.replace(keyword.upper(), "")
        sanitized = sanitized.replace(keyword.lower(), "")

    # Ограничиваем длину
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000] + "..."

    # Удаляем множественные пробелы
    sanitized = " ".join(sanitized.split())

    return sanitized.strip()


# Функция для валидации пользовательского ввода


def validate_user_input(
    text: str, min_length: int = 1, max_length: int = 1000
) -> tuple[bool, str]:
    """Валидирует пользовательский ввод"""
    if not text:
        return False, "Пустой ввод"

    if len(text) < min_length:
        return False, f"Слишком короткий ввод (минимум {min_length} символов)"

    if len(text) > max_length:
        return False, f"Слишком длинный ввод (максимум {max_length} символов)"

    # Проверяем на подозрительные паттерны
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"onload=",
        r"onerror=",
        r"onclick=",
        r"onmouseover=",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<form",
        r"SELECT.*FROM",
        r"INSERT.*INTO",
        r"UPDATE.*SET",
        r"DELETE.*FROM",
        r"DROP.*TABLE",
        r"UNION.*SELECT",
        r"OR.*1=1",
        r"AND.*1=1",
    ]

    import re

    text_lower = text.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            return False, "Обнаружен подозрительный контент"

    return True, "OK"


# Функция для показа всех убежищ
def show_all_shelters(chat_id: int):
    """Показывает список всех убежищ с кэшированием"""
    if not BOT_TOKEN or not bot:
        logger.warning("BOT_TOKEN не настроен, функция show_all_shelters недоступна")
        return

    # Проверяем кэш для пользователя
    if CACHE_ENABLED:
        cached_shelters = get_cached_user_data(f"shelters_{chat_id}")
        if cached_shelters is not None:
            logger.debug(f"📥 Список убежищ для {chat_id} загружен из кэша")
            shelters = cached_shelters
        else:
            shelters = placeholders.get("shelters", [])
            # Кэшируем на 1 час
            cache_user_data(f"shelters_{chat_id}", shelters, 3600)
    else:
        shelters = placeholders.get("shelters", [])

    if not shelters:
        bot.send_message(
            chat_id, "❌ Список убежищ недоступен", reply_markup=get_back_keyboard()
        )
        return

    # Создаем кнопки для каждого убежища
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for shelter in shelters:
        # Создаем кнопку для каждого убежища
        shelter_name = shelter.get("name", "Без названия")
        if "Главная проходная" in shelter_name:
            button_text = "🏢 Убежище Главная проходная Ростсельмаш"
        elif "Участок № 10" in shelter_name or "Убежище № 10" in shelter_name:
            button_text = "🏭 Убежище № 10 (РПРЗ, 12 пролет)"
        else:
            button_text = f"🏠 {shelter_name}"

        markup.add(types.KeyboardButton(button_text))

    # Добавляем кнопку "Назад"
    markup.add(types.KeyboardButton("⬅️ Назад"))

    try:
        bot.send_message(
            chat_id,
            "🏠 Выберите убежище для получения подробной информации:\n\n"
            f"📋 Доступно убежищ: {len(shelters)}\n"
            "🔍 Нажмите на название убежища для просмотра деталей",
            reply_markup=markup,
        )
        logger.info(
            f"📋 Пользователю {chat_id} показаны кнопки для {len(shelters)} убежищ"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки кнопок убежищ: {e}")


def show_specific_shelter(chat_id: int, shelter_name: str):
    """Показывает подробную информацию о конкретном убежище"""
    if not BOT_TOKEN or not bot:
        logger.warning(
            "BOT_TOKEN не настроен, функция show_specific_shelter недоступна"
        )
        return

    shelters = placeholders.get("shelters", [])
    selected_shelter = None

    # Находим убежище по названию или ключевым словам
    for shelter in shelters:
        shelter_full_name = shelter.get("name", "")
        if (
            "Главная проходная" in shelter_name
            and "Главная проходная" in shelter_full_name
        ) or (
            "№ 10" in shelter_name
            and (
                "Участок № 10" in shelter_full_name
                or "Убежище № 10" in shelter_full_name
            )
        ):
            selected_shelter = shelter
            break

    if not selected_shelter:
        bot.send_message(
            chat_id, "❌ Убежище не найдено", reply_markup=get_back_keyboard()
        )
        return

    try:
        # Отправляем основное изображение убежища
        photo_path = selected_shelter.get("photo_path", "")
        if photo_path and os.path.exists(photo_path):
            try:
                with open(photo_path, "rb") as photo_file:
                    bot.send_photo(
                        chat_id,
                        photo_file,
                        caption=f"📸 {selected_shelter['name']}",
                    )
            except Exception as photo_error:
                logger.warning(f"Не удалось отправить фото убежища: {photo_error}")

        # Для убежища №10 - отправляем дополнительные фото
        if "№ 10" in selected_shelter.get("name", ""):
            # Фото входа с 12 пролета
            entrance_path = "assets/images/shelter_2_entrance.jpg"
            if os.path.exists(entrance_path):
                try:
                    with open(entrance_path, "rb") as entrance_file:
                        bot.send_photo(
                            chat_id,
                            entrance_file,
                            caption="🚪 Вход в убежище с 12 пролета",
                        )
                except Exception as e:
                    logger.warning(f"Не удалось отправить фото входа: {e}")

            # Схема расположения убежища
            map_path = "assets/images/shelter_2_map.png"
            if os.path.exists(map_path):
                try:
                    with open(map_path, "rb") as map_file:
                        bot.send_photo(
                            chat_id,
                            map_file,
                            caption="🗺️ Схема расположения убежища № 10 на территории РПРЗ",
                        )
                except Exception as e:
                    logger.warning(f"Не удалось отправить схему: {e}")

        # Отправляем подробную информацию об убежище
        shelter_text = (
            f"🏠 {selected_shelter['name']}\n\n"
            f"📝 {selected_shelter['description']}\n\n"
            f"📍 Координаты: {selected_shelter['lat']}, {selected_shelter['lon']}\n"
            f"📞 Контакт: {selected_shelter.get('contact_phone', 'Не указан')}\n"
            f"👤 Ответственный: {selected_shelter.get('responsible_person', 'Не указан')}\n\n"
            f"🗺️ Ссылка на Яндекс.Карты: {selected_shelter.get('map_link', 'Недоступна')}"
        )

        # Создаем кнопки с действиями для убежища
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📋 Показать список убежищ"))
        markup.add(types.KeyboardButton("⬅️ Назад"))

        bot.send_message(chat_id, shelter_text, reply_markup=markup)

        logger.info(
            f"📋 Пользователю {chat_id} показано убежище: {selected_shelter['name']}"
        )

    except Exception as e:
        logger.error(f"Ошибка отправки информации об убежище: {e}")
        bot.send_message(
            chat_id,
            "❌ Ошибка получения информации об убежище",
            reply_markup=get_back_keyboard(),
        )


def show_shelter_map(chat_id: int):
    """Показывает карту с местоположением всех убежищ"""
    if not BOT_TOKEN or not bot:
        logger.warning("BOT_TOKEN не настроен, функция show_shelter_map недоступна")
        return

    shelters = placeholders.get("shelters", [])
    if not shelters:
        bot.send_message(
            chat_id, "❌ Данные об убежищах недоступны", reply_markup=get_back_keyboard()
        )
        return

    try:
        map_text = "🗺️ Местоположения убежищ РПРЗ:\n\n"

        for i, shelter in enumerate(shelters, 1):
            shelter_name = shelter.get("name", "Без названия")
            map_link = shelter.get("map_link", "")

            map_text += f"{i}. **{shelter_name}**\n"
            map_text += f"📍 {shelter.get('lat', 'N/A')}, {shelter.get('lon', 'N/A')}\n"
            if map_link:
                map_text += f"🔗 [Открыть на карте]({map_link})\n"
            map_text += "\n"

        # Добавляем общую ссылку на Яндекс.Карты с обеими точками
        if len(shelters) >= 2:
            shelter1 = shelters[0]
            shelter2 = shelters[1]
            combined_link = (
                f"https://yandex.ru/maps/?pt="
                f"{shelter1.get('lon', '39.763172')},{shelter1.get('lat', '47.258268')}"
                f"~{shelter2.get('lon', '39.765541')},{shelter2.get('lat', '47.264452')}"
                f"&z=15&l=map"
            )
            map_text += f"🗺️ [Показать все убежища на карте]({combined_link})"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📋 Показать список убежищ"))
        markup.add(types.KeyboardButton("⬅️ Назад"))

        bot.send_message(chat_id, map_text, reply_markup=markup, parse_mode="Markdown")
        logger.info(f"🗺️ Пользователю {chat_id} показана карта убежищ")

    except Exception as e:
        logger.error(f"Ошибка показа карты: {e}")
        bot.send_message(
            chat_id, "❌ Ошибка загрузки карты", reply_markup=get_back_keyboard()
        )


# Функция для поиска убежищ по геолокации (сортировка по близости)


def find_nearest_shelter(chat_id: int, user_lat: float, user_lon: float):
    """Находит и показывает все убежища по близости от пользователя"""
    if not BOT_TOKEN or not bot:
        logger.warning("BOT_TOKEN не настроен, функция find_nearest_shelter недоступна")
        return

    shelters = placeholders.get("shelters", [])

    if not shelters:
        bot.send_message(
            chat_id, "❌ Список убежищ недоступен", reply_markup=get_back_keyboard()
        )
        return

    # Простой расчет расстояния (для MVP)
    def calculate_distance(lat1, lon1, lat2, lon2):
        # Примерный расчет расстояния в километрах
        # 1 градус широты ≈ 111 км
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5 * 111

    # Рассчитываем расстояние до каждого убежища
    shelters_with_distance = []
    for shelter in shelters:
        try:
            shelter_lat = float(shelter.get("lat", 0))
            shelter_lon = float(shelter.get("lon", 0))
            distance = calculate_distance(user_lat, user_lon, shelter_lat, shelter_lon)
            shelters_with_distance.append((shelter, distance))
        except Exception as e:
            logger.warning(f"Ошибка расчета расстояния для убежища: {e}")
            continue

    if not shelters_with_distance:
        bot.send_message(
            chat_id,
            "❌ Не удалось рассчитать расстояния до убежищ",
            reply_markup=get_back_keyboard(),
        )
        return

    # Сортируем по расстоянию (от ближайшего к дальнему)
    shelters_with_distance.sort(key=lambda x: x[1])

    # Отправляем информацию о каждом убежище в порядке приоритета
    try:
        bot.send_message(
            chat_id, "📍 Убежища отсортированы по расстоянию от вашей локации:"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки заголовка: {e}")

    success_count = 0
    for i, (shelter, distance) in enumerate(shelters_with_distance, 1):
        try:
            # Отправляем изображение убежища
            photo_path = shelter.get("photo_path", "")
            if photo_path and os.path.exists(photo_path):
                try:
                    with open(photo_path, "rb") as photo_file:
                        caption = f"{'🎯' if i == 1 else '🏠'} #{i}"
                        bot.send_photo(chat_id, photo_file, caption=caption)
                except Exception as photo_error:
                    logger.warning(
                        f"Не удалось отправить фото убежища {i}: {photo_error}"
                    )

            # Формируем текст с приоритетом (без Markdown для стабильности)
            priority_marker = "🎯 БЛИЖАЙШЕЕ" if i == 1 else f"#{i}"
            shelter_text = (
                f"{priority_marker} - {shelter['name']}\n\n"
                f"📝 {shelter['description']}\n\n"
                f"📏 Расстояние: ~{distance:.2f} км\n"
                f"📍 Координаты: {shelter['lat']}, {shelter['lon']}\n"
                f"📞 Контакт: {shelter.get('contact_phone', 'Не указан')}\n"
                f"👤 Ответственный: {shelter.get('responsible_person', 'Не указан')}\n"
                f"🌐 Карта: {shelter['map_link']}"
            )

            bot.send_message(chat_id, shelter_text)
            success_count += 1

        except Exception as e:
            logger.error(f"Ошибка отправки информации об убежище {i}: {e}")
            continue

    # Финальное сообщение
    try:
        final_text = (
            f"✅ Показано убежищ: {success_count} из {len(shelters_with_distance)}\n\n"
            f"🎯 Ближайшее: {shelters_with_distance[0][0]['name']} (~{shelters_with_distance[0][1]:.2f} км)\n\n"
            f"Все убежища показаны в порядке приоритета от ближайшего к дальнему."
        )
        bot.send_message(chat_id, final_text, reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.error(f"Ошибка отправки финального сообщения: {e}")
        try:
            bot.send_message(
                chat_id, "✅ Поиск завершен", reply_markup=get_main_menu_keyboard()
            )
        except Exception:
            pass

    # Возвращаем в главное меню
    user_states[chat_id] = "main_menu"
    bot.set_state(chat_id, BotStates.main_menu)


# Проверка BOT_TOKEN перенесена в основной блок if __name__ == "__main__":

# Настройка логирования и инициализация бота перенесены в основной блок if
# __name__ == "__main__"

# Глобальные переменные для хранения состояния (инициализируются в
# основном блоке)
user_states = {}  # chat_id -> текущее состояние
user_data = {}  # chat_id -> данные пользователя
user_history = {}  # chat_id -> история действий
bot = None  # Будет инициализирован в основном блоке


# Состояния бота
class BotStates(StatesGroup):
    main_menu = State()
    danger_report = State()
    shelter_finder = State()
    rprz_assistant = State()
    improvement_suggestion = State()


# Загрузка заглушек


def load_placeholders():
    """Загружает данные-заглушки из JSON файла с кэшированием"""
    try:
        # Проверяем кэш
        if CACHE_ENABLED:
            cached_data = cache.get("placeholders_data")
            if cached_data is not None:
                logger.debug("📥 Данные убежищ загружены из кэша")
                return cached_data

        # Загружаем из файла
        with open("configs/data_placeholders.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Кэшируем на 2 часа
        if CACHE_ENABLED:
            cache.set("placeholders_data", data, 7200)
            logger.debug("💾 Данные убежищ сохранены в кэш")

        return data
    except Exception as e:
        log_admin_error(
            "CONFIG_LOAD_ERROR", e, {"config_file": "configs/data_placeholders.json"}
        )
        return {}


placeholders = load_placeholders()


# Обработчики команд (регистрируются только при инициализации бота)
# Обработчик для неинициализированных пользователей
def handle_uninitialized_user(message):
    """Обрабатывает сообщения от неинициализированных пользователей"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    logger.info(
        f"Неинициализированный пользователь {username} ({chat_id}) отправил: {message.text}"
    )

    # Инициализируем пользователя
    user_states[chat_id] = "main_menu"
    user_data[chat_id] = {}
    user_history[chat_id] = []
    bot.set_state(chat_id, BotStates.main_menu)

    # Отправляем приветствие
    welcome_text = (
        "👋 Добро пожаловать в бот безопасности РПРЗ!\n\n"
        "🕐 Время работы: каждый день с 7:00 до 19:00 МСК\n\n"
        "Я помогу вам:\n"
        "❗ Сообщить об опасности\n"
        "🏠 Найти ближайшее укрытие\n"
        "🤖 Помощник РПРЗ - ответы на вопросы\n"
        "💡 Предложить улучшения\n\n"
        "Выберите действие из меню:"
    )

    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu_keyboard())
    log_activity(chat_id, username, "auto_initialization")


def start_command(message):
    """Обработчик команды /start"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    user_id = message.from_user.id

    # Проверка рабочего времени
    if not is_working_hours():
        moscow_offset = timedelta(hours=3)
        moscow_tz = timezone(moscow_offset)
        moscow_time = datetime.now(moscow_tz)
        bot.send_message(
            chat_id,
            f"⏰ Бот работает с 7:00 до 19:00 МСК\n\n"
            f"🕐 Текущее время МСК: {moscow_time.strftime('%H:%M')}\n\n"
            f"Пожалуйста, обратитесь в рабочие часы.\n"
            f"В экстренных случаях звоните:\n"
            f"📞 Служба безопасности: {placeholders.get('contacts', {}).get('security', 'Не указан')}\n"
            f"📞 Охрана труда: {placeholders.get('contacts', {}).get('safety', 'Не указан')}",
        )
        logger.info(
            f"⏰ Пользователь {username} ({chat_id}) попытался запустить бота "
            f"вне рабочих часов: {moscow_time.strftime('%H:%M')} МСК"
        )
        return

    # Проверка безопасности
    if SECURITY_ENABLED:
        is_allowed, error_msg = check_user_security(user_id, action="start")
        if not is_allowed:
            bot.send_message(chat_id, error_msg)
            logger.warning(f"🚫 Заблокирован /start от {user_id}: {error_msg}")
            return

    logger.info(f"Пользователь {username} ({chat_id}) запустил бота")
    logger.bind(user_id=user_id).info(f"Команда /start от пользователя {username}")

    log_activity(chat_id, username, "start")

    # Сброс состояния
    user_states[chat_id] = "main_menu"
    user_data[chat_id] = {}
    user_history[chat_id] = []

    logger.debug(f"Состояние пользователя {chat_id} сброшено в main_menu")

    bot.set_state(chat_id, BotStates.main_menu)

    welcome_text = (
        "👋 Добро пожаловать в бот безопасности РПРЗ!\n\n"
        "🕐 Время работы: каждый день с 7:00 до 19:00 МСК\n\n"
        "Я помогу вам:\n"
        "❗ Сообщить об опасности\n"
        "🏠 Найти ближайшее укрытие\n"
        "🤖 Помощник РПРЗ - ответы на вопросы\n"
        "💡 Предложить улучшения\n\n"
        "Выберите действие из меню:"
    )

    logger.debug(f"Отправка приветственного сообщения пользователю {chat_id}")
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu_keyboard())


def help_command(message):
    """Обработчик команды /help"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    user_id = message.from_user.id

    # Проверка безопасности
    if SECURITY_ENABLED:
        is_allowed, error_msg = check_user_security(user_id, action="help")
        if not is_allowed:
            bot.send_message(chat_id, error_msg)
            return

    log_activity(chat_id, username, "help")

    help_text = (
        "🤖 Справка по боту безопасности РПРЗ\n\n"
        "❗ Сообщите об опасности - зарегистрировать инцидент\n"
        "🏠 Ближайшее укрытие - найти убежище рядом\n"
        "💡 Предложение по улучшению - отправить идею\n\n"
        "Назад - вернуться в главное меню\n"
        "/start - перезапустить бота\n"
        "/help - эта справка"
    )

    bot.send_message(chat_id, help_text, reply_markup=get_main_menu_keyboard())


def history_command(message):
    """Показывает историю действий пользователя"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    log_activity(chat_id, username, "history_request")

    try:
        # Читаем историю из CSV
        history_text = "📋 Ваша история действий:\n\n"

        if os.path.exists("logs/activity.csv"):
            with open("logs/activity.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                user_actions = [row for row in reader if int(row["user_id"]) == chat_id]

                if user_actions:
                    for action in user_actions[-10:]:  # Последние 10 действий
                        # Убираем микросекунды
                        timestamp = action["timestamp"][:19]
                        history_text += f"🕐 {timestamp}\n"
                        history_text += f"📝 {action['action']}\n"
                        if action["payload"]:
                            history_text += f"📄 {action['payload'][:50]}...\n"
                        history_text += "\n"
                else:
                    history_text += "История пуста"
        else:
            history_text += "История не найдена"

        bot.send_message(chat_id, history_text, reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        bot.send_message(
            chat_id,
            "❌ Ошибка при получении истории",
            reply_markup=get_main_menu_keyboard(),
        )


# Обработчик текстовых сообщений


def handle_text(message):
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    user_id = message.from_user.id
    text = message.text

    # Логируем каждое текстовое сообщение
    logger.info(
        f"📝 Текст от {username} ({user_id}): {text[:50]}{'...' if len(text) > 50 else ''}"
    )

    # Проверка безопасности (rate limiting, flood control)
    if SECURITY_ENABLED:
        is_allowed, error_msg = check_user_security(user_id, action="text_message")
        if not is_allowed:
            bot.send_message(chat_id, error_msg)
            logger.warning(f"🚫 Заблокировано сообщение от {user_id}: {error_msg}")
            return

        # Валидация текста на вредоносный контент
        is_valid_text, text_error = validate_user_text(text, user_id)
        if not is_valid_text:
            bot.send_message(chat_id, text_error)
            logger.warning(f"🚫 Невалидный текст от {user_id}: {text_error}")
            return

    # Санитизируем и валидируем пользовательский ввод
    sanitized_text = sanitize_user_input(text)
    is_valid, validation_error = validate_user_input(
        sanitized_text, min_length=1, max_length=1000
    )

    if not is_valid:
        logger.warning(f"Невалидный ввод от {username}: {validation_error}")
        bot.send_message(chat_id, f"❌ {validation_error}")
        return

    logger.bind(user_id=user_id).info(
        f"Получено текстовое сообщение от {username}: {sanitized_text[:100]}..."
    )
    logger.debug(
        f"Детали сообщения: chat_id={chat_id}, user_id={user_id}, "
        f"username={username}, text_length={len(sanitized_text)}"
    )
    logger.debug(f"Текущее состояние пользователя: {user_states.get(chat_id, 'None')}")

    log_activity(chat_id, username, "text_message", sanitized_text)

    # Если пользователь не инициализирован, инициализируем его
    if chat_id not in user_states:
        user_states[chat_id] = "main_menu"
        user_data[chat_id] = {}
        user_history[chat_id] = []
        bot.set_state(chat_id, BotStates.main_menu)
        logger.info(
            f"Пользователь {username} ({chat_id}) автоматически инициализирован"
        )

    # Обработка кнопки "Назад"
    if sanitized_text == "⬅️ Назад":
        logger.info(f"⬅️ {username} ({chat_id}) вернулся в главное меню")
        user_states[chat_id] = "main_menu"
        bot.set_state(chat_id, BotStates.main_menu)
        bot.send_message(
            chat_id, "🏠 Главное меню:", reply_markup=get_main_menu_keyboard()
        )
        return

    # Обработка главного меню (включая случай когда состояние None)
    if user_states.get(chat_id) in ["main_menu", None]:
        logger.bind(user_id=user_id).debug(
            f"Обработка главного меню для пользователя {username}, состояние: {user_states.get(chat_id)}"
        )

        # Если состояние None, устанавливаем main_menu
        if user_states.get(chat_id) is None:
            user_states[chat_id] = "main_menu"
            bot.set_state(chat_id, BotStates.main_menu)

        if sanitized_text == "❗ Сообщите об опасности":
            logger.bind(user_id=user_id).info(
                "Пользователь выбрал 'Сообщить об опасности'"
            )
            start_danger_report(message)
        elif sanitized_text == "🏠 Ближайшее укрытие":
            logger.bind(user_id=user_id).info("Пользователь выбрал 'Ближайшее укрытие'")
            start_shelter_finder(message)
        elif sanitized_text == "🤖 Помощник РПРЗ":
            logger.bind(user_id=user_id).info("Пользователь выбрал 'Помощник РПРЗ'")
            start_rprz_assistant(message)
        elif sanitized_text == "💡 Предложение по улучшению":
            logger.bind(user_id=user_id).info(
                "Пользователь выбрал 'Предложение по улучшению'"
            )
            start_improvement_suggestion(message)
        else:
            # Любой другой текст в главном меню - показываем подсказку
            logger.bind(user_id=user_id).warning(
                f"Неизвестная команда в главном меню: {sanitized_text}"
            )
            bot.send_message(
                chat_id,
                "❓ Выберите действие из меню:",
                reply_markup=get_main_menu_keyboard(),
            )

    # Обработка состояний
    elif user_states.get(chat_id) == "danger_report":
        logger.info(f"🚨 {username} ({chat_id}) в процессе сообщения об опасности")

        # Обработка кнопки "Ключевые контакты"
        if text == "📞 Ключевые контакты":
            logger.info(
                f"📞 {username} ({chat_id}) запросил ключевые контакты из danger_report"
            )
            show_key_contacts(chat_id)
            return

        logger.bind(user_id=user_id).debug(
            f"Обработка состояния 'danger_report' для пользователя {username}"
        )
        result = handle_danger_report_text(message, user_data[chat_id], placeholders)
        if isinstance(result, tuple):
            new_state, response = result
            logger.bind(user_id=user_id).info(
                f"Переход состояния: {user_states[chat_id]} -> {new_state}"
            )
            user_states[chat_id] = new_state
            if new_state == "main_menu":
                bot.set_state(chat_id, BotStates.main_menu)
                if isinstance(response, dict):
                    bot.send_message(
                        chat_id,
                        response["text"],
                        reply_markup=response.get("reply_markup"),
                        parse_mode=response.get("parse_mode"),
                    )
                elif response is not None:
                    bot.send_message(
                        chat_id, response, reply_markup=get_main_menu_keyboard()
                    )
                else:
                    bot.send_message(
                        chat_id,
                        "🏠 Главное меню:",
                        reply_markup=get_main_menu_keyboard(),
                    )
            else:
                if isinstance(response, dict):
                    bot.send_message(
                        chat_id,
                        response["text"],
                        reply_markup=response.get("reply_markup"),
                        parse_mode=response.get("parse_mode"),
                    )
                elif response is not None:
                    bot.send_message(
                        chat_id, response, reply_markup=get_back_keyboard()
                    )
                else:
                    bot.send_message(
                        chat_id,
                        "❓ Выберите действие:",
                        reply_markup=get_back_keyboard(),
                    )
        else:
            bot.send_message(chat_id, result, reply_markup=get_back_keyboard())

    elif user_states.get(chat_id) == "shelter_finder":
        logger.info(f"🏠 {username} ({chat_id}) работает с поиском убежищ")
        if text == "⬅️ Назад":
            user_states[chat_id] = "main_menu"
            bot.set_state(chat_id, BotStates.main_menu)
            bot.send_message(
                chat_id, "🏠 Главное меню:", reply_markup=get_main_menu_keyboard()
            )
        elif text == "📋 Показать список убежищ":
            logger.info(f"📋 {username} ({chat_id}) запросил список всех убежищ")
            show_all_shelters(chat_id)
        elif text == "📍 Отправить геолокацию":
            bot.send_message(
                chat_id,
                "📍 Нажмите кнопку 'Отправить геолокацию' для поиска ближайшего убежища",
            )
        elif text == "🏢 Убежище Главная проходная Ростсельмаш":
            logger.info(f"🏢 {username} ({chat_id}) выбрал убежище на главной проходной")
            show_specific_shelter(chat_id, text)
        elif text == "🏭 Убежище № 10 (РПРЗ, 12 пролет)":
            logger.info(f"🏭 {username} ({chat_id}) выбрал убежище № 10")
            show_specific_shelter(chat_id, text)
        else:
            bot.send_message(
                chat_id,
                "❓ Выберите действие из меню:",
                reply_markup=get_back_keyboard(),
            )

    elif user_states.get(chat_id) == "rprz_assistant":
        logger.info(f"🤖 {username} ({chat_id}) задаёт вопрос помощнику")

        # Обработка кнопки "Расписание автобусов"
        if text == "🚌 Расписание автобусов":
            logger.info(f"🚌 {username} ({chat_id}) запросил расписание автобусов")
            show_bus_schedule(chat_id)
        # Обработка кнопки "Ключевые контакты"
        elif text == "📞 Ключевые контакты":
            logger.info(f"📞 {username} ({chat_id}) запросил ключевые контакты")
            show_key_contacts(chat_id)
        else:
            result = handle_rprz_assistant_text(message, placeholders)
            if isinstance(result, tuple):
                new_state, response = result
                user_states[chat_id] = new_state
                if new_state == "main_menu":
                    bot.set_state(chat_id, BotStates.main_menu)
                    bot.send_message(
                        chat_id, response, reply_markup=get_main_menu_keyboard()
                    )
                else:
                    # Создаем клавиатуру с кнопками для rprz_assistant
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add(types.KeyboardButton("🚌 Расписание автобусов"))
                    markup.add(types.KeyboardButton("📞 Ключевые контакты"))
                    markup.add(types.KeyboardButton("⬅️ Назад"))
                    bot.send_message(chat_id, response, reply_markup=markup)
            else:
                # Создаем клавиатуру с кнопками для rprz_assistant
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton("🚌 Расписание автобусов"))
                markup.add(types.KeyboardButton("📞 Ключевые контакты"))
                markup.add(types.KeyboardButton("⬅️ Назад"))
                bot.send_message(chat_id, result, reply_markup=markup)

    elif user_states.get(chat_id) == "improvement_suggestion":
        logger.info(f"💡 {username} ({chat_id}) отправляет предложение")
        result = handle_improvement_suggestion_text(message, placeholders, user_data)
        if isinstance(result, tuple):
            new_state, response = result
            user_states[chat_id] = new_state
            if new_state == "main_menu":
                bot.set_state(chat_id, BotStates.main_menu)
                if isinstance(response, dict):
                    bot.send_message(
                        chat_id,
                        response["text"],
                        reply_markup=response.get("reply_markup"),
                    )
                elif response is not None:
                    bot.send_message(
                        chat_id, response, reply_markup=get_main_menu_keyboard()
                    )
                else:
                    bot.send_message(
                        chat_id,
                        "🏠 Главное меню:",
                        reply_markup=get_main_menu_keyboard(),
                    )
            else:
                if isinstance(response, dict):
                    bot.send_message(
                        chat_id,
                        response["text"],
                        reply_markup=response.get("reply_markup"),
                    )
                elif response is not None:
                    bot.send_message(
                        chat_id, response, reply_markup=get_back_keyboard()
                    )
                else:
                    bot.send_message(
                        chat_id,
                        "❓ Выберите действие:",
                        reply_markup=get_back_keyboard(),
                    )
        else:
            bot.send_message(chat_id, result, reply_markup=get_back_keyboard())


# Функции для каждого раздела будут добавлены в следующих этапах


def start_danger_report(message):
    """Начало процесса сообщения об опасности"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    logger.info(f"🚨 {username} ({chat_id}) начал сообщение об опасности")
    log_activity(chat_id, username, "danger_report_start")

    # Устанавливаем состояние для сообщения об опасности
    user_states[chat_id] = "danger_report"
    user_data[chat_id] = {"step": "description", "description": "", "location": None}
    bot.set_state(chat_id, BotStates.danger_report)

    bot.send_message(
        chat_id,
        "❗ Сообщите об опасности\n\n"
        "📝 Опишите, что произошло, максимум 500 символов, и написать "
        "«Ваше сообщение будет отправлено в службу безопасности для оперативного реагирования». "
        "Пожалуйста, не используйте это сообщение просто так или как спам-рассылку.\n\n"
        "Введите текст с описанием места. Пример: – ЦГТ-025, 4-й участок.\n"
        "Прикрепите, пожалуйста, фото или видео. Ваше фото облегчит или ускорит решение вопроса.\n\n"
        "📝 Опишите что произошло (максимум 500 символов):",
        reply_markup=get_danger_keyboard(),
    )


def start_shelter_finder(message):
    """Начало поиска ближайшего укрытия"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    logger.info(f"🏠 {username} ({chat_id}) ищет ближайшее укрытие")
    log_activity(chat_id, username, "shelter_finder_start")

    user_states[chat_id] = "shelter_finder"
    bot.set_state(chat_id, BotStates.shelter_finder)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📍 Отправить геолокацию", request_location=True))
    markup.add(types.KeyboardButton("📋 Показать список убежищ"))
    markup.add(types.KeyboardButton("⬅️ Назад"))

    bot.send_message(
        chat_id,
        "🏠 Поиск ближайшего укрытия\n\n"
        "⚠️ В случае опасности БПЛА или ракетной опасности "
        "немедленно переместитесь в ближайшее укрытие или бомбоубежище!\n\n"
        "🎒 Обязательно возьмите с собой:\n"
        "• 📄 Документы (паспорт, удостоверение)\n"
        "• 💊 Медикаменты (личные лекарства)\n"
        "• 💧 Воду (минимум 0.5л на человека)\n"
        "• 📱 Заряженный телефон с PowerBank\n\n"
        "Выберите действие:",
        reply_markup=markup,
    )


def show_bus_schedule(chat_id: int):
    """Показывает расписание автобусов"""
    if not BOT_TOKEN or not bot:
        logger.warning("BOT_TOKEN не настроен, функция show_bus_schedule недоступна")
        return

    try:
        # Отправляем фото расписания
        photo_path = "assets/images/bus_schedule.jpg"
        if os.path.exists(photo_path):
            try:
                with open(photo_path, "rb") as photo_file:
                    bot.send_photo(
                        chat_id,
                        photo_file,
                        caption="🚌 Расписание внутризаводского общественного транспорта РПРЗ",
                    )
                logger.info(f"✅ Расписание автобусов отправлено пользователю {chat_id}")
            except Exception as photo_error:
                logger.error(f"❌ Не удалось отправить фото расписания: {photo_error}")
                bot.send_message(
                    chat_id, "❌ Ошибка загрузки фото расписания. Попробуйте позже."
                )
                return
        else:
            logger.warning(f"⚠️ Файл расписания не найден: {photo_path}")
            bot.send_message(chat_id, "❌ Расписание временно недоступно.")
            return

        # Добавляем текстовую информацию
        info_text = (
            "🚌 Расписание внутризаводского транспорта\n\n"
            "📍 Основные остановки:\n"
            "• Главная проходная ДМО\n"
            "• Комбинат питания\n"
            "• МСЦ-8\n"
            "• ДМО (СОК-1)\n\n"
            "🕐 Режим работы: ежедневно"
        )

        # Создаем клавиатуру с кнопками
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🚌 Расписание автобусов"))
        markup.add(types.KeyboardButton("📞 Ключевые контакты"))
        markup.add(types.KeyboardButton("⬅️ Назад"))

        bot.send_message(chat_id, info_text, reply_markup=markup)
        log_activity(chat_id, "user", "bus_schedule_viewed")

    except Exception as e:
        logger.error(f"❌ Ошибка показа расписания автобусов: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка при загрузке расписания")


def show_key_contacts(chat_id: int):
    """Показывает ключевые контакты РПРЗ"""
    if not BOT_TOKEN or not bot:
        logger.warning("BOT_TOKEN не настроен, функция show_key_contacts недоступна")
        return

    try:
        # Получаем ключевые контакты из placeholders
        key_contacts = placeholders.get("key_contacts", {})

        if not key_contacts:
            bot.send_message(chat_id, "❌ Ключевые контакты временно недоступны.")
            return

        # Формируем сообщение с контактами
        contacts_text = "📞 Ключевые контакты РПРЗ\n\n"
        contacts_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Травмпункт
        if "trauma_center" in key_contacts:
            name = key_contacts["trauma_center"]["name"]
            phone = key_contacts["trauma_center"]["phone"]
            contacts_text += f"🏥 {name}\n"
            contacts_text += f"📞 Внутренний: {phone}\n\n"

        # Пожарная часть
        if "fire_department" in key_contacts:
            name = key_contacts["fire_department"]["name"]
            phone = key_contacts["fire_department"]["phone"]
            contacts_text += f"🚒 {name}\n"
            contacts_text += f"📞 Внутренний: {phone}\n\n"

        # Пост охраны
        if "security_post" in key_contacts:
            name = key_contacts["security_post"]["name"]
            phone = key_contacts["security_post"]["phone"]
            contacts_text += f"🛡️ {name}\n"
            contacts_text += f"📞 Внутренний: {phone}\n\n"

        # Профсоюзный комитет
        if "union" in key_contacts:
            name = key_contacts["union"]["name"]
            phone = key_contacts["union"]["phone"]
            contacts_text += f"👥 {name}\n"
            contacts_text += f"📞 Внутренний: {phone}\n\n"

        # Отдел развития и оценки персонала
        if "hr_development" in key_contacts:
            name = key_contacts["hr_development"]["name"]
            phone = key_contacts["hr_development"]["phone"]
            contacts_text += f"📋 {name}\n"
            contacts_text += f"📞 Внутренний: {phone}\n\n"

        # Служба поддержки пользователей
        if "user_support" in key_contacts:
            name = key_contacts["user_support"]["name"]
            phone = key_contacts["user_support"]["phone"]
            contacts_text += f"💻 {name}\n"
            contacts_text += f"📞 Внутренний: {phone}\n\n"

        contacts_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        contacts_text += "📱 Для звонка с мобильного телефона:\n\n"
        contacts_text += "📞 Позвоните: +7 (863) 300-02-28\n"
        contacts_text += "Затем в тональном режиме наберите внутренний номер\n\n"
        contacts_text += "💡 Скопируйте номер выше для быстрого вызова"

        # Создаем клавиатуру с кнопками навигации
        keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard_markup.add(types.KeyboardButton("🚌 Расписание автобусов"))
        keyboard_markup.add(types.KeyboardButton("📞 Ключевые контакты"))
        keyboard_markup.add(types.KeyboardButton("⬅️ Назад"))

        bot.send_message(chat_id, contacts_text, reply_markup=keyboard_markup)

        log_activity(chat_id, "user", "key_contacts_viewed")
        logger.info(f"✅ Ключевые контакты отправлены пользователю {chat_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка показа ключевых контактов: {e}")
        import traceback

        logger.error(traceback.format_exc())
        bot.send_message(chat_id, "❌ Произошла ошибка при загрузке контактов")


def start_rprz_assistant(message):
    """Начало работы с помощником РПРЗ"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    logger.info(f"🤖 {username} ({chat_id}) открыл Помощник РПРЗ")
    log_activity(chat_id, username, "rprz_assistant_start")

    user_states[chat_id] = "rprz_assistant"
    user_data[chat_id] = {"step": "question"}
    bot.set_state(chat_id, BotStates.rprz_assistant)

    welcome_text = (
        "🤖 Помощник РПРЗ\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Я помогу вам найти информацию по:\n\n"
        "📋 Инструкциям по технике безопасности\n"
        "🏭 Правилам работы на производстве\n"
        "⚠️ Процедурам при ЧС\n"
        "📞 Контактам служб безопасности\n"
        "🏠 Расположению убежищ\n"
        "🚌 Расписанию автобусов\n\n"
        "❓ Примеры вопросов:\n"
        "• Где находится ближайшее убежище?\n"
        "• Как действовать при пожаре?\n"
        "• Контакты службы безопасности?\n"
        "• Инструкции по охране труда\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 Задайте ваш вопрос или нажмите кнопку:"
    )

    # Создаем клавиатуру с кнопками
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚌 Расписание автобусов"))
    markup.add(types.KeyboardButton("📞 Ключевые контакты"))
    markup.add(types.KeyboardButton("⬅️ Назад"))

    bot.send_message(chat_id, welcome_text, reply_markup=markup)


def start_improvement_suggestion(message):
    """Начало отправки предложения по улучшению"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    logger.info(f"💡 {username} ({chat_id}) начал отправку предложения по улучшению")
    log_activity(chat_id, username, "improvement_suggestion_start")

    user_states[chat_id] = "improvement_suggestion"
    user_data[chat_id] = {"step": "text"}
    bot.set_state(chat_id, BotStates.improvement_suggestion)

    welcome_text = (
        "💡 Предложение по улучшению бота\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 Как правильно заполнить предложение:\n\n"
        "✅ Опишите вашу идею четко и понятно\n"
        "✅ Укажите, что конкретно нужно улучшить\n"
        "✅ Объясните, какую пользу это принесет\n"
        "✅ Минимум 10 символов, максимум 1000\n\n"
        "📝 Примеры предложений:\n"
        "• Добавить карту завода с убежищами\n"
        "• Улучшить систему оповещения об опасности\n"
        "• Добавить базу знаний по технике безопасности\n"
        "• Упростить навигацию в боте\n"
        "• Добавить историю всех инцидентов\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 Напишите ваше предложение:"
    )

    bot.send_message(chat_id, welcome_text, reply_markup=get_back_keyboard())


# Обработчик геолокации


def handle_location(message):
    """Обработчик геолокации"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    user_id = message.from_user.id
    user_lat = message.location.latitude
    user_lon = message.location.longitude

    logger.info(
        f"📍 {username} ({chat_id}) отправил геолокацию: {user_lat:.4f}, {user_lon:.4f}"
    )

    # Проверка безопасности
    if SECURITY_ENABLED:
        is_allowed, error_msg = check_user_security(user_id, action="location")
        if not is_allowed:
            bot.send_message(chat_id, error_msg)
            logger.warning(f"🚫 Заблокирована геолокация от {user_id}: {error_msg}")
            return

    logger.bind(user_id=user_id).info(
        f"Получена геолокация от {username}: {user_lat}, {user_lon}"
    )

    if user_states.get(chat_id) == "shelter_finder":
        # Ищем ближайшее убежище по геолокации
        logger.bind(user_id=user_id).info("Поиск ближайшего убежища по геолокации")
        find_nearest_shelter(chat_id, user_lat, user_lon)
    elif user_states.get(chat_id) == "danger_report":
        # Обрабатываем геолокацию через handlers
        logger.bind(user_id=user_id).info(
            "Обработка геолокации для сообщения об опасности"
        )
        result = handle_danger_report_location(message, user_data[chat_id])
        if isinstance(result, dict):
            bot.send_message(
                chat_id,
                result["text"],
                reply_markup=result.get("reply_markup"),
                parse_mode=result.get("parse_mode"),
            )
    else:
        logger.bind(user_id=user_id).warning(
            f"Геолокация получена в неподходящем состоянии: {user_states.get(chat_id)}"
        )
        bot.send_message(chat_id, "❌ Геолокация не нужна в текущем режиме")


# Обработчик медиафайлов


def handle_media(message):
    """Обработчик медиафайлов"""
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"
    user_id = message.from_user.id
    content_type = message.content_type

    logger.info(f"📷 {username} ({chat_id}) отправил медиафайл: {content_type}")

    # Проверка безопасности
    if SECURITY_ENABLED:
        is_allowed, error_msg = check_user_security(user_id, action="media")
        if not is_allowed:
            bot.send_message(chat_id, error_msg)
            logger.warning(f"🚫 Заблокирован медиафайл от {user_id}: {error_msg}")
            return

        # Оптимизированная валидация файла
        file_size = 0
        mime_type = None

        if content_type == "photo":
            file_size = message.photo[-1].file_size
            mime_type = "image/jpeg"
        elif content_type == "video":
            file_size = message.video.file_size
            mime_type = message.video.mime_type
        elif content_type == "document":
            file_size = message.document.file_size
            mime_type = message.document.mime_type

        # Используем оптимизированную валидацию если доступна
        if MEDIA_PROCESSOR_ENABLED and file_size and mime_type:
            is_valid, file_error = validate_media_file(file_size, mime_type, user_id)
            if not is_valid:
                bot.send_message(chat_id, file_error)
                logger.warning(f"🚫 Невалидный файл от {user_id}: {file_error}")
                return
        elif file_size and mime_type:
            # Fallback к старой системе валидации
            max_size = (
                MAX_VIDEO_SIZE_MB if content_type == "video" else MAX_FILE_SIZE_MB
            )
            is_valid, file_error = validate_user_file(
                file_size, mime_type, user_id, max_size
            )
            if not is_valid:
                bot.send_message(chat_id, file_error)
                logger.warning(f"🚫 Невалидный файл от {user_id}: {file_error}")
                return

    logger.bind(user_id=user_id).info(
        f"Получен медиафайл от {username}: {content_type}"
    )

    if user_states.get(chat_id) == "danger_report":
        # Проверяем этап - медиафайлы принимаются только на этапе "media"
        current_step = user_data.get(chat_id, {}).get("step", "")

        if current_step in ["location", "location_text"]:
            # Отклоняем медиафайлы на этапе указания места
            bot.send_message(
                chat_id,
                "❌ Пожалуйста, укажите местоположение инцидента текстом или "
                "отправьте геолокацию. Файлы не принимаются для поля 'Место'.",
            )
            logger.bind(user_id=user_id).warning(
                f"Отклонен медиафайл на этапе указания места: {current_step}"
            )
            return

        elif current_step == "media":
            # Обрабатываем медиафайлы только на этапе "media"
            logger.bind(user_id=user_id).info(
                "Обработка медиафайла для сообщения об опасности"
            )
            result = handle_danger_report_media(
                message, user_data[chat_id], MAX_FILE_SIZE_MB, MAX_VIDEO_SIZE_MB
            )
            bot.send_message(chat_id, result, reply_markup=get_media_keyboard())
        else:
            # Медиафайлы не принимаются на других этапах
            bot.send_message(
                chat_id,
                "❌ Медиафайлы можно прикреплять только на этапе добавления фото/видео к инциденту.",
            )
            logger.bind(user_id=user_id).warning(
                f"Отклонен медиафайл на этапе: {current_step}"
            )
    else:
        logger.bind(user_id=user_id).warning(
            f"Медиафайл получен в неподходящем состоянии: {user_states.get(chat_id)}"
        )
        bot.send_message(
            chat_id, "❌ Медиафайлы можно прикреплять только при сообщении об опасности"
        )


# Обработчик колбэков (inline кнопок)
def handle_callback(call):
    """Обработчик всех callback запросов от inline кнопок"""
    chat_id = call.message.chat.id
    username = call.from_user.username or "Unknown"
    user_id = call.from_user.id
    data = call.data

    logger.info(f"🔘 {username} ({chat_id}) нажал кнопку: {data}")
    logger.bind(user_id=user_id).info(f"Получен callback от {username}: {data}")

    try:
        # Обработка callback'ов для разных функций
        if data == "back_to_menu":
            user_states[chat_id] = "main_menu"
            bot.set_state(chat_id, BotStates.main_menu)
            bot.edit_message_text(
                "🏠 Главное меню:", chat_id=chat_id, message_id=call.message.message_id
            )
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=get_inline_main_menu(),
            )
            bot.answer_callback_query(call.id, "Возврат в главное меню")

        # Callback'и для сообщения об опасности
        elif data.startswith("danger_"):
            handle_danger_callback(call)

        # Callback'и для предложений
        elif data.startswith("vote_") or data.startswith("suggestion_"):
            handle_suggestion_callback(call)

        else:
            bot.answer_callback_query(call.id, "Неизвестное действие")
            logger.warning(f"Неизвестный callback: {data}")

    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка обработки")


def handle_danger_callback(call):
    """Обработка callback'ов для сообщений об опасности"""
    chat_id = call.message.chat.id
    data = call.data

    if data == "danger_add_photo":
        bot.answer_callback_query(call.id, "📷 Отправьте фото")
        bot.send_message(chat_id, "📷 Отправьте фото инцидента:")

    elif data == "danger_add_location":
        bot.answer_callback_query(call.id, "📍 Отправьте геолокацию")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            types.KeyboardButton("📍 Отправить геолокацию", request_location=True)
        )
        bot.send_message(
            chat_id, "📍 Нажмите кнопку для отправки геолокации:", reply_markup=markup
        )

    elif data == "danger_submit":
        bot.answer_callback_query(call.id, "✅ Отправка...")
        result = finish_danger_report(call.message, user_data[chat_id], placeholders)
        if isinstance(result, tuple):
            new_state, response = result
            user_states[chat_id] = new_state
            if isinstance(response, dict):
                bot.send_message(
                    chat_id, response["text"], reply_markup=response.get("reply_markup")
                )
            else:
                bot.send_message(
                    chat_id, response, reply_markup=get_main_menu_keyboard()
                )

    elif data == "danger_cancel":
        bot.answer_callback_query(call.id, "❌ Отменено")
        user_data[chat_id].clear()
        user_states[chat_id] = "main_menu"
        bot.set_state(chat_id, BotStates.main_menu)
        bot.send_message(
            chat_id,
            "❌ Сообщение об опасности отменено",
            reply_markup=get_main_menu_keyboard(),
        )


def handle_suggestion_callback(call):
    """Обработка callback'ов для предложений"""
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("vote_"):
        # Формат: vote_yes_123 или vote_no_123
        parts = data.split("_")
        vote_type = parts[1]  # 'yes' или 'no'
        suggestion_id = int(parts[2])

        # Обработка голосования
        success = process_vote(chat_id, suggestion_id, vote_type)

        if success:
            emoji = "👍" if vote_type == "yes" else "👎"
            bot.answer_callback_query(call.id, f"{emoji} Ваш голос учтён!")

            # Обновляем сообщение с новым количеством голосов
            try:
                suggestions_file = "logs/enhanced_suggestions.json"
                if os.path.exists(suggestions_file):
                    with open(suggestions_file, "r", encoding="utf-8") as f:
                        suggestions = json.load(f)

                    suggestion = next(
                        (s for s in suggestions if s["id"] == suggestion_id), None
                    )
                    if suggestion:
                        markup = types.InlineKeyboardMarkup()
                        markup.add(
                            types.InlineKeyboardButton(
                                f"👍 {suggestion.get('votes', 0)}",
                                callback_data=f"vote_yes_{suggestion_id}",
                            ),
                            types.InlineKeyboardButton(
                                f"👎 {suggestion.get('downvotes', 0)}",
                                callback_data=f"vote_no_{suggestion_id}",
                            ),
                        )
                        bot.edit_message_reply_markup(
                            chat_id=chat_id,
                            message_id=call.message.message_id,
                            reply_markup=markup,
                        )
            except Exception as e:
                logger.error(f"Ошибка обновления голосов: {e}")
        else:
            bot.answer_callback_query(call.id, "❌ Вы уже голосовали")

    elif data == "suggestion_my":
        bot.answer_callback_query(call.id, "📊 Загрузка ваших предложений...")
        # TODO: Показать предложения пользователя

    elif data == "suggestion_popular":
        bot.answer_callback_query(call.id, "🏆 Загрузка популярных...")
        # TODO: Показать популярные предложения


def process_vote(user_id: int, suggestion_id: int, vote_type: str) -> bool:
    """Обрабатывает голосование за предложение"""
    try:
        suggestions_file = "logs/enhanced_suggestions.json"
        if not os.path.exists(suggestions_file):
            return False

        with open(suggestions_file, "r", encoding="utf-8") as f:
            suggestions = json.load(f)

        # Находим предложение
        suggestion = next((s for s in suggestions if s["id"] == suggestion_id), None)
        if not suggestion:
            return False

        # Проверяем, голосовал ли уже пользователь
        voters = suggestion.get("voters", [])
        if user_id in voters:
            return False

        # Добавляем голос
        voters.append(user_id)
        suggestion["voters"] = voters

        if vote_type == "yes":
            suggestion["votes"] = suggestion.get("votes", 0) + 1
        else:
            suggestion["downvotes"] = suggestion.get("downvotes", 0) + 1

        # Сохраняем
        with open(suggestions_file, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        logger.error(f"Ошибка обработки голоса: {e}")
        return False


def get_inline_main_menu():
    """Создаёт inline клавиатуру главного меню"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "❗ Сообщить об опасности", callback_data="start_danger_report"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "🏠 Ближайшее укрытие", callback_data="start_shelter_finder"
        )
    )
    markup.add(
        types.InlineKeyboardButton("💡 Предложение", callback_data="start_improvement")
    )
    return markup


# Основной цикл
if __name__ == "__main__":
    # Проверка рабочего времени (экономия ресурсов Railway)
    check_and_shutdown_if_needed()

    # Проверка блокировки процесса (пропускаем для Railway/контейнеров)
    IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID")

    if not IS_RAILWAY:
        logger.info("🔍 Проверка блокировки процесса...")
        if not create_process_lock():
            logger.error("❌ Не удалось создать блокировку процесса")
            logger.info("💡 Возможно, уже запущен другой экземпляр бота")
            sys.exit(1)
    else:
        logger.info("🚂 Запуск в Railway - пропуск блокировки процесса")

    # Настройка подробного логирования
    os.makedirs("logs", exist_ok=True)

    # Основной лог файл
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
        encoding="utf-8",
        errors="replace",
    )

    # Отдельный лог для ошибок с детальной информацией
    logger.add(
        "logs/errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        compression="zip",
        encoding="utf-8",
        errors="replace",
    )

    # Лог для критических ошибок админа
    logger.add(
        "logs/admin_critical.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | CRITICAL | {name}:{function}:{line} - {message}",
        level="CRITICAL",
        rotation="5 MB",
        compression="zip",
        encoding="utf-8",
        errors="replace",
        filter=lambda record: record["level"].name == "CRITICAL",
    )

    # Лог для системных ошибок
    logger.add(
        "logs/system_errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | SYSTEM | {extra[error_type]} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        compression="zip",
        encoding="utf-8",
        errors="replace",
        filter=lambda record: "error_type" in record["extra"],
    )

    # Лог для пользовательских действий
    logger.add(
        "logs/user_actions.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | USER:{extra[user_id]} | {message}",
        level="INFO",
        rotation="5 MB",
        compression="zip",
        encoding="utf-8",
        errors="replace",
        filter=lambda record: "user_id" in record["extra"],
    )

    # Лог для API запросов
    logger.add(
        "logs/api_requests.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | API | {message}",
        level="DEBUG",
        rotation="5 MB",
        compression="zip",
        encoding="utf-8",
        errors="replace",
    )

    logger.info("Запуск MVP бота безопасности РПРЗ")

    # Проверяем наличие токена
    if not BOT_TOKEN or len(BOT_TOKEN) < 10:
        log_admin_error(
            "CONFIG_ERROR",
            Exception("BOT_TOKEN не найден"),
            {"config_file": ".env", "required_vars": ["BOT_TOKEN", "ADMIN_CHAT_ID"]},
        )
        logger.error("❌ BOT_TOKEN не настроен!")
        logger.info("📝 Для локальной разработки создайте файл .env:")
        logger.info("BOT_TOKEN=<ваш_токен>")
        logger.info("ADMIN_CHAT_ID=<ваш_chat_id>")
        logger.info("📝 Для Railway добавьте переменные окружения в панели Variables")
        sys.exit(1)

    # Инициализация бота
    state_storage = StateMemoryStorage()
    bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)

    # Устанавливаем глобальный экземпляр бота для handlers
    set_bot_instance(bot)

    # Устанавливаем глобальный экземпляр бота для notifications
    try:
        from bot.notifications import set_bot_instance

        set_bot_instance(bot)
        logger.info("✅ Bot instance установлен для notifications")
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось установить bot instance для notifications: {e}")

    # Регистрируем обработчики
    bot.message_handler(
        func=lambda message: message.chat.id not in user_states
        and message.content_type == "text"
        and not message.text.startswith("/")
    )(handle_uninitialized_user)
    bot.message_handler(commands=["start"])(start_command)
    bot.message_handler(commands=["help"])(help_command)
    bot.message_handler(commands=["my_history"])(history_command)
    bot.message_handler(content_types=["text"])(handle_text)
    bot.message_handler(content_types=["location"])(handle_location)
    bot.message_handler(content_types=["photo", "video", "document"])(handle_media)

    # Регистрируем обработчик колбэков (inline кнопок)
    bot.callback_query_handler(func=lambda call: True)(handle_callback)

    try:
        # Тестируем подключение к боту
        logger.info("Проверка подключения к Telegram API...")
        bot_info = bot.get_me()
        logger.info(f"Бот подключен: @{bot_info.username}")
        logger.info(f"Токен: {mask_sensitive_data(BOT_TOKEN)}")

        # Очищаем webhook перед запуском polling
        logger.info("Очистка webhook...")
        try:
            bot.remove_webhook()
            logger.info("Webhook очищен")
        except Exception as e:
            logger.warning(f"Не удалось очистить webhook: {e}")

        # Проверяем и останавливаем другие экземпляры бота
        logger.info("Проверка на конфликтующие экземпляры...")
        try:
            python_processes = [
                p
                for p in psutil.process_iter(["pid", "name", "cmdline"])
                if p.info["name"] == "python.exe"
                and "main.py" in " ".join(p.info["cmdline"] or [])
            ]

            if len(python_processes) > 1:
                logger.warning(
                    f"Найдено {len(python_processes)} экземпляров Python с main.py"
                )
                # Оставляем первый, остальные убиваем
                for proc in python_processes[1:]:
                    try:
                        proc.terminate()
                        logger.info(f"Остановлен процесс {proc.info['pid']}")
                    except Exception:
                        pass
                time.sleep(2)
        except ImportError:
            logger.warning("psutil не установлен, пропускаем проверку процессов")
        except Exception as e:
            logger.warning(f"Ошибка проверки процессов: {e}")

        # Ждем немного перед запуском
        logger.info("Ожидание 3 секунды...")
        time.sleep(3)

        # Запускаем периодическую очистку кэша
        if CACHE_ENABLED:
            import threading

            def cache_cleanup_scheduler():
                """Периодическая очистка кэша каждые 10 минут"""
                while True:
                    try:
                        time.sleep(600)  # 10 минут
                        cleanup_cache()
                    except Exception as e:
                        logger.error(f"Ошибка очистки кэша: {e}")

            cache_thread = threading.Thread(target=cache_cleanup_scheduler, daemon=True)
            cache_thread.start()
            logger.info("✅ Планировщик очистки кэша запущен")

        # Запуск Flask сервера для Health Check в отдельном потоке
        import threading

        def run_flask():
            health_app.run(
                host="0.0.0.0",
                port=int(os.getenv("PORT", 8000)),
                debug=False,
                use_reloader=False,
            )

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("✅ Flask Health Check сервер запущен на порту 8000")

        logger.info("Запуск polling...")
        logger.info("Настройки polling: interval=3, timeout=20, none_stop=True")

        try:
            bot.polling(none_stop=True, interval=3, timeout=20)
        except Exception as polling_error:
            error_str = str(polling_error)
            log_admin_error(
                "BOT_POLLING_ERROR",
                polling_error,
                {
                    "error_type": "polling_critical",
                    "bot_token_masked": mask_sensitive_data(BOT_TOKEN),
                },
            )

            if "409" in error_str or "Conflict" in error_str:
                log_admin_error(
                    "BOT_INSTANCE_CONFLICT",
                    polling_error,
                    {
                        "error_type": "instance_conflict",
                        "recommended_actions": [
                            "Остановить все процессы Python",
                            "Перезагрузить компьютер",
                            "Подождать 2-3 минуты",
                        ],
                    },
                )

                # Пытаемся остановить процессы автоматически
                try:
                    logger.info("🔄 Попытка автоматической остановки процессов...")

                    # Безопасная остановка процессов через psutil
                    try:
                        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                            if proc.info[
                                "name"
                            ] == "python.exe" and "main.py" in " ".join(
                                proc.info["cmdline"] or []
                            ):
                                try:
                                    proc.terminate()
                                    logger.info(
                                        f"Остановлен процесс {proc.info['pid']}"
                                    )
                                except Exception:
                                    pass
                    except (ImportError, Exception) as e:
                        logger.warning(f"Ошибка остановки процессов: {e}")

                    logger.info("⏳ Ожидание 5 секунд...")
                    time.sleep(5)

                    # Очищаем webhook еще раз
                    try:
                        bot.remove_webhook()
                        logger.info("Webhook очищен повторно")
                    except Exception:
                        pass

                    logger.info("🔄 Повторная попытка запуска...")
                    bot.polling(none_stop=True, interval=3, timeout=20)

                except Exception as auto_stop_error:
                    logger.error(
                        f"❌ Ошибка автоматической остановки: {auto_stop_error}"
                    )
                    logger.info("🔄 Попробуйте запустить restart_clean.py")
                    sys.exit(1)
            else:
                logger.error(f"❌ Неизвестная ошибка polling: {polling_error}")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("⏹️ Остановка бота пользователем")
        if not IS_RAILWAY:
            remove_process_lock()
        sys.exit(0)
    except ssl.SSLError as e:
        logger.error(f"❌ SSL ошибка: {e}")
        logger.info("💡 Попробуйте обновить сертификаты или использовать VPN")
        if not IS_RAILWAY:
            remove_process_lock()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        logger.info("💡 Проверьте правильность BOT_TOKEN в файле .env")
        if not IS_RAILWAY:
            remove_process_lock()
        sys.exit(1)
