"""
Модуль для отправки email уведомлений
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра бота
bot_instance = None

def set_bot_instance(bot):
    """Устанавливает экземпляр бота для отправки уведомлений в Telegram"""
    global bot_instance
    bot_instance = bot
    logger.info("✅ Bot instance установлен для notifications")

def send_incident_notification(incident_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Отправляет уведомление об инциденте через email и Telegram
    
    Args:
        incident_data: Данные об инциденте
        
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        # Отправляем в Telegram админу
        telegram_success = send_telegram_notification(incident_data)
        
        # Отправляем email уведомление
        email_success = send_email_notification(incident_data)
        
        if telegram_success and email_success:
            return True, "Уведомления отправлены в Telegram и Email"
        elif telegram_success:
            return True, "Уведомление отправлено в Telegram (Email недоступен)"
        elif email_success:
            return True, "Уведомление отправлено в Email (Telegram недоступен)"
        else:
            return False, "Не удалось отправить уведомления"
            
    except Exception as e:
        logger.error(f"Ошибка отправки уведомлений: {e}")
        return False, f"Ошибка: {str(e)}"

def send_telegram_notification(incident_data: Dict[str, Any]) -> bool:
    """Отправляет уведомление в Telegram админу"""
    try:
        if not bot_instance:
            logger.warning("⚠️ Bot instance не установлен для Telegram уведомлений")
            return False
            
        admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        if not admin_chat_id:
            logger.warning("⚠️ ADMIN_CHAT_ID не настроен")
            return False
            
        # Формируем сообщение
        message = format_incident_message(incident_data)
        
        # Отправляем сообщение
        bot_instance.send_message(
            chat_id=admin_chat_id,
            text=message,
            parse_mode='HTML'
        )
        
        logger.info("✅ Уведомление админу в Telegram отправлено")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки Telegram уведомления: {e}")
        return False

def send_email_notification(incident_data: Dict[str, Any]) -> bool:
    """Отправляет email уведомление"""
    try:
        # Получаем настройки SMTP (проверяем все возможные переменные)
        smtp_server = (os.getenv('YANDEX_SMTP_HOST') or 
                      os.getenv('SMTP_SERVER') or 
                      os.getenv('SMTP_HOST'))
        smtp_port = int(os.getenv('YANDEX_SMTP_PORT') or 
                       os.getenv('SMTP_PORT') or 
                       os.getenv('PORT', 587))
        smtp_username = (os.getenv('YANDEX_SMTP_USER') or 
                        os.getenv('SMTP_USERNAME') or 
                        os.getenv('SMTP_USER'))
        smtp_password = (os.getenv('YANDEX_SMTP_PASSWORD') or 
                        os.getenv('SMTP_PASSWORD') or 
                        os.getenv('SMTP_PASS'))
        email_to = (os.getenv('ADMIN_EMAIL') or 
                   os.getenv('INCIDENT_NOTIFICATION_EMAILS') or 
                   os.getenv('NOTIFICATION_EMAIL'))
        
        # Отладочная информация о всех переменных
        logger.info("🔍 Отладка SMTP переменных:")
        logger.info(f"YANDEX_SMTP_HOST: {os.getenv('YANDEX_SMTP_HOST', 'НЕТ')}")
        logger.info(f"YANDEX_SMTP_PORT: {os.getenv('YANDEX_SMTP_PORT', 'НЕТ')}")
        logger.info(f"YANDEX_SMTP_USER: {os.getenv('YANDEX_SMTP_USER', 'НЕТ')}")
        logger.info(f"YANDEX_SMTP_PASSWORD: {'ЕСТЬ' if os.getenv('YANDEX_SMTP_PASSWORD') else 'НЕТ'}")
        logger.info(f"ADMIN_EMAIL: {os.getenv('ADMIN_EMAIL', 'НЕТ')}")
        logger.info(f"INCIDENT_NOTIFICATION_EMAILS: {os.getenv('INCIDENT_NOTIFICATION_EMAILS', 'НЕТ')}")
        logger.info(f"🔍 SMTP настройки: server={smtp_server}, port={smtp_port}, user={smtp_username}, to={email_to}")
        
        # Проверяем все переменные окружения
        all_env_vars = {k: v for k, v in os.environ.items() if 'SMTP' in k or 'EMAIL' in k or 'YANDEX' in k}
        logger.info(f"🔍 Все SMTP/EMAIL переменные: {all_env_vars}")
        
        if not all([smtp_server, smtp_username, smtp_password, email_to]):
            missing = []
            if not smtp_server: missing.append("YANDEX_SMTP_HOST или SMTP_SERVER")
            if not smtp_port: missing.append("YANDEX_SMTP_PORT или SMTP_PORT") 
            if not smtp_username: missing.append("YANDEX_SMTP_USER или SMTP_USERNAME")
            if not smtp_password: missing.append("YANDEX_SMTP_PASSWORD или SMTP_PASSWORD")
            if not email_to: missing.append("ADMIN_EMAIL или INCIDENT_NOTIFICATION_EMAILS")
            logger.warning(f"⚠️ SMTP настройки не полные. Отсутствуют: {', '.join(missing)}")
            return False
            
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email_to
        msg['Subject'] = f"🚨 Инцидент в RPRZ боте - {incident_data.get('type', 'Неизвестно')}"
        
        # Формируем текст письма
        body = format_incident_email(incident_data)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Отправляем письмо
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        logger.info("✅ Email уведомление отправлено")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки email уведомления: {e}")
        return False

def format_incident_message(incident_data: Dict[str, Any]) -> str:
    """Форматирует сообщение об инциденте для Telegram"""
    from datetime import datetime
    
    message = f"🚨 <b>Новый инцидент в RPRZ боте</b>\n\n"
    message += f"📋 <b>Тип:</b> {incident_data.get('type', 'Сообщение об опасности')}\n"
    message += f"👤 <b>Пользователь:</b> {incident_data.get('username', 'Неизвестно')}\n"
    message += f"🆔 <b>ID:</b> {incident_data.get('user_id', 'Неизвестно')}\n"
    message += f"⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} МСК\n"
    message += f"📝 <b>Описание:</b> {incident_data.get('description', 'Не указано')}\n"
    
    if incident_data.get('location'):
        lat = incident_data['location'].get('latitude', '')
        lon = incident_data['location'].get('longitude', '')
        message += f"📍 <b>Координаты:</b> {lat}, {lon}\n"
    elif incident_data.get('location_text'):
        message += f"📍 <b>Место:</b> {incident_data['location_text']}\n"
    else:
        message += f"📍 <b>Место:</b> Не указано\n"
        
    message += f"📷 <b>Медиафайлов:</b> {incident_data.get('media_count', 0)}\n"
        
    if incident_data.get('severity'):
        message += f"⚠️ <b>Критичность:</b> {incident_data['severity']}\n"
        
    return message

def format_incident_email(incident_data: Dict[str, Any]) -> str:
    """Форматирует текст письма об инциденте"""
    from datetime import datetime
    
    body = f"Новый инцидент в RPRZ боте\n\n"
    body += f"Тип: {incident_data.get('type', 'Сообщение об опасности')}\n"
    body += f"Пользователь: {incident_data.get('username', 'Неизвестно')}\n"
    body += f"ID: {incident_data.get('user_id', 'Неизвестно')}\n"
    body += f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} МСК\n"
    body += f"Описание: {incident_data.get('description', 'Не указано')}\n"
    
    if incident_data.get('location'):
        lat = incident_data['location'].get('latitude', '')
        lon = incident_data['location'].get('longitude', '')
        body += f"Координаты: {lat}, {lon}\n"
    elif incident_data.get('location_text'):
        body += f"Место: {incident_data['location_text']}\n"
    else:
        body += f"Место: Не указано\n"
        
    body += f"Медиафайлов: {incident_data.get('media_count', 0)}\n"
        
    if incident_data.get('severity'):
        body += f"Критичность: {incident_data['severity']}\n"
        
    body += f"\n\nЭто автоматическое уведомление от RPRZ бота."
    
    return body
