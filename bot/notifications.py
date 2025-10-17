"""
Модуль для отправки email уведомлений
"""
import logging
import os
from typing import Any, Dict, Tuple

import resend

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра бота
bot_instance = None


def set_bot_instance(bot):
    """Устанавливает экземпляр бота для отправки уведомлений в Telegram"""
    global bot_instance
    bot_instance = bot
    logger.info("✅ Bot instance установлен для notifications")


def send_incident_notification(
    incident_data: Dict[str, Any], media_files: list = None
) -> Tuple[bool, str]:
    """
    Отправляет уведомление об инциденте через email и Telegram

    Args:
        incident_data: Данные об инциденте

    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    logger.info("🔍 Начало send_incident_notification")
    try:
        # Отправляем в Telegram админу
        telegram_success = send_telegram_notification(incident_data)

        # Отправляем email уведомление с медиафайлами
        email_success = send_email_notification(incident_data, media_files)

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

        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        if not admin_chat_id:
            logger.warning("⚠️ ADMIN_CHAT_ID не настроен")
            return False

        # Формируем сообщение
        message = format_incident_message(incident_data)

        # Отправляем сообщение
        bot_instance.send_message(
            chat_id=admin_chat_id, text=message, parse_mode="HTML"
        )

        logger.info("✅ Уведомление админу в Telegram отправлено")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки Telegram уведомления: {e}")
        return False


def send_email_via_smtp(
    incident_data: Dict[str, Any], media_files: list = None
) -> bool:
    """Fallback: отправка через SMTP если Resend недоступен"""
    try:
        import smtplib
        from email import encoders
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Настройки SMTP (из env.example)
        smtp_host = os.getenv("YANDEX_SMTP_HOST", "smtp.yandex.ru")
        smtp_port = int(os.getenv("YANDEX_SMTP_PORT", "587"))
        smtp_user = os.getenv("YANDEX_SMTP_USER")
        smtp_password = os.getenv("YANDEX_SMTP_PASSWORD")
        admin_email = os.getenv("ADMIN_EMAIL") or os.getenv(
            "INCIDENT_NOTIFICATION_EMAILS"
        )

        logger.info("🔍 Попытка отправки через SMTP fallback...")
        logger.info(f"SMTP Host: {smtp_host}:{smtp_port}")
        logger.info(f"SMTP User: {smtp_user or 'НЕТ'}")

        if not all([smtp_user, smtp_password, admin_email]):
            logger.warning("⚠️ SMTP credentials не настроены полностью")
            return False

        # Создаем multipart сообщение
        msg = MIMEMultipart("mixed")
        msg["From"] = smtp_user
        msg["To"] = admin_email
        msg[
            "Subject"
        ] = f"🚨 Инцидент в RPRZ боте - {incident_data.get('description', '')[:30]}"

        # Добавляем HTML body
        body_text = format_incident_email(incident_data)
        html_body = _format_incident_html(incident_data, media_files)

        # Добавляем альтернативную часть (plain text + HTML)
        msg_alternative = MIMEMultipart("alternative")
        msg_alternative.attach(MIMEText(body_text, "plain", "utf-8"))
        msg_alternative.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(msg_alternative)

        # Прикрепляем медиафайлы
        if media_files:
            logger.info(f"📎 Прикрепление {len(media_files)} файлов через SMTP")
            for idx, media in enumerate(media_files):
                try:
                    filename = media.get("filename", f"attachment_{idx+1}.jpg")
                    mime_type = media.get("mime_type", "application/octet-stream")

                    # Определяем maintype и subtype
                    if "/" in mime_type:
                        maintype, subtype = mime_type.split("/", 1)
                    else:
                        maintype, subtype = "application", "octet-stream"

                    part = MIMEBase(maintype, subtype)
                    part.set_payload(media["data"])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition", f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)
                    logger.info(f"✅ SMTP: прикреплен файл {filename}")
                except Exception as e:
                    logger.error(f"❌ SMTP: ошибка прикрепления файла {idx+1}: {e}")

        # Отправка через SMTP
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"✅ Email отправлен через SMTP fallback на {admin_email}")
        return True

    except Exception as e:
        logger.error(f"❌ SMTP fallback ошибка: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def _format_incident_html(
    incident_data: Dict[str, Any], media_files: list = None
) -> str:
    """Форматирует HTML для письма об инциденте"""
    from datetime import datetime

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #d32f2f; margin-top: 0;">🚨 НОВЫЙ ИНЦИДЕНТ</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <strong>👤 Пользователь:</strong>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        {incident_data.get('username', 'Неизвестно')} (ID: {incident_data.get('user_id', 'Неизвестно')})
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <strong>📝 Описание:</strong>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        {incident_data.get('description', 'Не указано')}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <strong>📍 Место:</strong>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        {incident_data.get('location_text') or 'Не указано'}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <strong>🕐 Время:</strong>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} МСК
                    </td>
                </tr>
            </table>
    """

    if media_files:
        media_count = len(media_files)
        html_content += f"""
            <div style="margin-top: 20px; padding: 15px; background-color: #e3f2fd;
                        border-left: 4px solid #2196f3; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #1976d2;">
                    📎 Прикрепленные файлы ({media_count}):
                </h3>
                <ul style="list-style: none; padding: 0;">
        """
        for idx, media in enumerate(media_files, 1):
            media_type = media.get("type", "photo")
            filename = media.get("filename", f"attachment_{idx}")

            if media_type == "photo":
                icon, type_name = "📷", "Фотография"
            elif media_type == "video":
                icon, type_name = "🎥", "Видео"
            elif media_type == "document":
                icon, type_name = "📄", "Документ"
            else:
                icon, type_name = "📎", "Файл"

            file_line = (
                f'<li style="padding: 5px 0;">{icon} '
                f"<strong>{type_name} {idx}:</strong> "
                f"<code>{filename}</code></li>"
            )
            html_content += file_line

        html_content += """
                </ul>
                <p style="margin-bottom: 0; color: #666; font-size: 0.9em;">
                    💡 Медиафайлы прикреплены к письму. Смотрите вложения ниже.
                </p>
            </div>
        """

    html_content += """
            <div style="margin-top: 20px; padding: 10px;
                        background-color: #f5f5f5; border-radius: 4px;
                        font-size: 0.85em; color: #666;">
                <p style="margin: 0;">
                    Это автоматическое уведомление от RPRZ Бота.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


def send_email_notification(
    incident_data: Dict[str, Any], media_files: list = None
) -> bool:
    """Отправляет email уведомление через Resend API с fallback на SMTP"""
    try:
        # Получаем настройки Resend
        resend_api_key = os.getenv("RESEND_API_KEY")
        email_from = os.getenv("RESEND_FROM_EMAIL") or os.getenv("ADMIN_EMAIL")
        email_to = os.getenv("ADMIN_EMAIL") or os.getenv("INCIDENT_NOTIFICATION_EMAILS")

        logger.info("🔍 Отладка Resend переменных:")
        logger.info(f"RESEND_API_KEY: {'ЕСТЬ' if resend_api_key else 'НЕТ'}")
        logger.info(f"RESEND_FROM_EMAIL: {email_from or 'НЕТ'}")
        logger.info(f"ADMIN_EMAIL: {email_to or 'НЕТ'}")

        if not all([resend_api_key, email_from, email_to]):
            missing = []
            if not resend_api_key:
                missing.append("RESEND_API_KEY")
            if not email_from:
                missing.append("RESEND_FROM_EMAIL или ADMIN_EMAIL")
            if not email_to:
                missing.append("ADMIN_EMAIL")
            logger.warning(
                f"⚠️ Resend настройки не полные. Отсутствуют: {', '.join(missing)}"
            )
            logger.info("🔄 Переключение на SMTP fallback...")
            return send_email_via_smtp(incident_data, media_files)

        # Настраиваем Resend
        resend.api_key = resend_api_key

        # Формируем письмо
        subject = f"🚨 Инцидент в RPRZ боте - {incident_data.get('type', 'Сообщение об опасности')}"
        body = format_incident_email(incident_data)
        html_content = _format_incident_html(incident_data, media_files)

        # Формируем attachments для Resend API
        attachments = []
        if media_files:
            import base64

            logger.info(f"📎 Формирование {len(media_files)} вложений для Resend API")

            for idx, media in enumerate(media_files):
                try:
                    # Resend API принимает attachments в формате:
                    # {"filename": str, "content": base64_encoded_bytes}
                    filename = media.get("filename", f"attachment_{idx+1}.jpg")
                    content_base64 = base64.b64encode(media["data"]).decode("utf-8")

                    attachments.append(
                        {"filename": filename, "content": content_base64}
                    )
                    logger.info(
                        f"✅ Вложение {idx+1} подготовлено: {filename} ({len(media['data'])} bytes)"
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка подготовки вложения {idx+1}: {e}")

        # Отправляем через Resend API
        params = {
            "from": email_from,
            "to": [email_to],
            "subject": subject,
            "text": body,
            "html": html_content,
        }

        # Добавляем attachments только если они есть
        if attachments:
            params["attachments"] = attachments
            logger.info(f"📎 Добавлено {len(attachments)} вложений в письмо")

        email = resend.Emails.send(params)
        logger.info(f"✅ Email уведомление отправлено через Resend: {email}")
        logger.info(f"📧 Email ID: {email.get('id', 'N/A')}")
        logger.info(f"📧 Отправлено с: {email_from} на: {email_to}")
        logger.info(f"📧 Вложений в письме: {len(attachments)}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка отправки email через Resend: {e}")
        import traceback

        logger.error(traceback.format_exc())

        # Fallback на SMTP при ошибке Resend
        logger.warning("🔄 Resend не удалось, пробуем SMTP fallback...")
        return send_email_via_smtp(incident_data, media_files)


def format_incident_message(incident_data: Dict[str, Any]) -> str:
    """Форматирует сообщение об инциденте для Telegram"""
    from datetime import datetime

    message = "🚨 <b>Новый инцидент в RPRZ боте</b>\n\n"
    message += f"📋 <b>Тип:</b> {incident_data.get('type', 'Сообщение об опасности')}\n"
    message += f"👤 <b>Пользователь:</b> {incident_data.get('username', 'Неизвестно')}\n"
    message += f"🆔 <b>ID:</b> {incident_data.get('user_id', 'Неизвестно')}\n"
    message += f"⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} МСК\n"
    message += f"📝 <b>Описание:</b> {incident_data.get('description', 'Не указано')}\n"

    if incident_data.get("location"):
        lat = incident_data["location"].get("latitude", "")
        lon = incident_data["location"].get("longitude", "")
        message += f"📍 <b>Координаты:</b> {lat}, {lon}\n"
    elif (
        incident_data.get("location_text") and incident_data["location_text"] != "None"
    ):
        message += f"📍 <b>Место:</b> {incident_data['location_text']}\n"
    else:
        message += "📍 <b>Место:</b> Не указано\n"

    message += f"📷 <b>Медиафайлов:</b> {incident_data.get('media_count', 0)}\n"

    if incident_data.get("severity"):
        message += f"⚠️ <b>Критичность:</b> {incident_data['severity']}\n"

    return message


def format_incident_email(incident_data: Dict[str, Any]) -> str:
    """Форматирует текст письма об инциденте"""
    from datetime import datetime

    body = "Новый инцидент в RPRZ боте\n\n"
    body += f"Тип: {incident_data.get('type', 'Сообщение об опасности')}\n"
    body += f"Пользователь: {incident_data.get('username', 'Неизвестно')}\n"
    body += f"ID: {incident_data.get('user_id', 'Неизвестно')}\n"
    body += f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} МСК\n"
    body += f"Описание: {incident_data.get('description', 'Не указано')}\n"

    if incident_data.get("location"):
        lat = incident_data["location"].get("latitude", "")
        lon = incident_data["location"].get("longitude", "")
        body += f"Координаты: {lat}, {lon}\n"
    elif (
        incident_data.get("location_text") and incident_data["location_text"] != "None"
    ):
        body += f"Место: {incident_data['location_text']}\n"
    else:
        body += "Место: Не указано\n"

    body += f"Медиафайлов: {incident_data.get('media_count', 0)}\n"

    if incident_data.get("severity"):
        body += f"Критичность: {incident_data['severity']}\n"

    body += "\n\nЭто автоматическое уведомление от RPRZ бота."

    return body
