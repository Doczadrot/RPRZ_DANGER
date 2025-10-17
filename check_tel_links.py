#!/usr/bin/env python3
"""
Pre-commit хук для проверки отсутствия tel: ссылок в Telegram inline кнопках
"""
import re
import sys


def check_tel_links_in_inline_buttons():
    """Проверяет что в коде нет tel: ссылок в InlineKeyboardButton"""

    # Читаем bot/main.py
    try:
        with open("bot/main.py", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("[ERROR] File bot/main.py not found")
        return 1

    # Ищем паттерн InlineKeyboardButton с tel: URL
    pattern = r'InlineKeyboardButton\([^)]*url\s*=\s*["\']tel:'

    if re.search(pattern, content):
        print("\n" + "=" * 70)
        print("[ERROR] CRITICAL: Found tel: links in InlineKeyboardButton!")
        print("=" * 70)
        print("\nTelegram API does NOT support tel: protocol in inline buttons.")
        print("This will cause error: 'Wrong port number specified in the URL'")
        print("\nSolution: Use plain text for phone numbers instead of inline buttons.")
        print("=" * 70 + "\n")
        return 1

    print("[OK] No tel: links found in inline buttons")
    return 0


if __name__ == "__main__":
    sys.exit(check_tel_links_in_inline_buttons())
