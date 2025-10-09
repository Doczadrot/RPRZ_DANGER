# ⚡ Railway Quick Start - Деплой за 5 минут

## 🎯 Быстрый старт

### 1️⃣ Пуш в GitHub (30 сек)

```bash
git add .
git commit -m "Подготовка к Railway"
git push origin main
```

### 2️⃣ Создание проекта Railway (1 мин)

1. https://railway.app → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Выберите репозиторий `RPRZbOT-main`

### 3️⃣ Добавление переменных (2 мин)

**Variables → Add Variables:**

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_CHAT_ID=ваш_telegram_id
LOG_LEVEL=INFO
```

### 4️⃣ Деплой (автоматически) (1 мин)

Railway автоматически:
- Устанавливает Python 3.10
- Устанавливает зависимости
- Запускает бота

### 5️⃣ Проверка (30 сек)

1. Railway → **View Logs** → ищите `✅ Бот подключен`
2. Telegram → `/start` → проверка работы

---

## 🚨 Быстрое решение проблем

### Бот не запускается?

```bash
# 1. Проверьте логи
Railway → View Logs

# 2. Проверьте переменные
Railway → Variables → BOT_TOKEN правильный?

# 3. Перезапустите
Railway → Redeploy
```

### Ошибка "Module not found"?

```bash
# Проверьте requirements.txt
git add requirements.txt
git commit -m "Fix deps"
git push
```

### Ошибка "409 Conflict"?

```bash
# Остановите все локальные версии бота
# Railway → Stop → Wait 30sec → Redeploy
```

---

## 🔄 Автообновление

```bash
# Каждый push = автодеплой
git add .
git commit -m "Обновление"
git push origin main
# Railway автоматически пересоберёт и перезапустит!
```

---

## 📞 Нужна помощь?

- Полная инструкция: `RAILWAY_DEPLOY_GUIDE.md`
- Railway Docs: https://docs.railway.app
- Telegram Bot API: https://core.telegram.org/bots

---

**Готово! Ваш бот работает 24/7! 🎉**
