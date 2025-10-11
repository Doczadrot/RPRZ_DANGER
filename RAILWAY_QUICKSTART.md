# ⚡ Railway Quickstart - Деплой за 5 минут

## Шаг 1: Подготовка (1 минута)

```bash
# Проверьте, что все готово
python check_deploy_ready.py

# Если check_deploy_ready.py не существует, пропустите этот шаг
```

## Шаг 2: Запушьте в GitHub (1 минута)

```bash
# Если репозиторий ещё не создан
git init
git add .
git commit -m "Готов к Railway деплою"

# Создайте репозиторий на GitHub: https://github.com/new

# Запушьте код
git remote add origin https://github.com/ваш-username/репозиторий.git
git branch -M main
git push -u origin main
```

## Шаг 3: Деплой на Railway (3 минуты)

### 3.1 Создайте проект

1. Откройте https://railway.app
2. Войдите через GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Выберите ваш репозиторий

### 3.2 Добавьте переменные

На вкладке **Variables** добавьте:

```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_CHAT_ID=your_telegram_chat_id
```

**Где взять?**
- `BOT_TOKEN`: Отправьте `/newbot` в @BotFather
- `ADMIN_CHAT_ID`: Отправьте `/start` в @userinfobot

### 3.3 Дождитесь деплоя

Railway автоматически:
1. ✅ Установит Python 3.10
2. ✅ Установит зависимости из `requirements.txt`
3. ✅ Запустит бота командой из `Procfile`

**Готово!** Через 2-3 минуты бот заработает 24/7.

## Проверка

1. Найдите бота в Telegram по username
2. Отправьте `/start`
3. Получите приветствие ✅

## Мониторинг

**Логи в реальном времени:**
Railway → Ваш проект → Deployments → View Logs

## Обновление бота

```bash
# Внесите изменения
git add .
git commit -m "Обновление"
git push origin main

# Railway автоматически обновит бота!
```

## Проблемы?

### Бот не отвечает

1. Проверьте логи в Railway
2. Убедитесь, что `BOT_TOKEN` правильный
3. Попробуйте **Redeploy** в Railway

### 409 Error (Conflict)

Остановите локальную версию бота, если запущена:

```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
pkill -f "python bot/main.py"
```

Затем **Restart** в Railway (Settings → Service → Restart)

## Полный гайд

Подробная инструкция: [RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)

---

**Вопросы?** Создайте issue в репозитории.

**Успешного деплоя!** 🚀
