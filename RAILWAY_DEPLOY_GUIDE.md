# 🚂 Гайд по деплою RPRZ Safety Bot на Railway.app

## 📦 1. Подготовка GitHub-репозитория

### 1.1. Удалите секреты из Git (если случайно закоммитили)

```bash
# Убедитесь, что .env НЕ в репозитории
git rm --cached .env
git rm --cached .env.local
```

### 1.2. Проверьте файлы проекта

Убедитесь, что созданы файлы:
- ✅ `Procfile` - команда запуска
- ✅ `runtime.txt` - версия Python
- ✅ `railway.json` - конфигурация Railway
- ✅ `.railwayignore` - исключения для деплоя
- ✅ `.gitignore` - защита секретов

### 1.3. Закоммитьте изменения

```bash
git add Procfile runtime.txt railway.json .railwayignore .gitignore
git commit -m "Подготовка к деплою на Railway"
git push origin main
```

**⚠️ КРИТИЧНО: Никогда не коммитьте файл .env с секретами!**

---

## 🚀 2. Настройка Railway.app

### 2.1. Создание проекта

1. Перейдите на https://railway.app
2. Войдите через GitHub
3. Нажмите **"New Project"**
4. Выберите **"Deploy from GitHub repo"**
5. Выберите ваш репозиторий `RPRZbOT-main`
6. Railway автоматически обнаружит Python-проект

### 2.2. Настройка переменных окружения

**В интерфейсе Railway перейдите: Project → Variables → Add Variable**

Добавьте переменные (используя значения из вашего локального `.env`):

```env
# ОБЯЗАТЕЛЬНЫЕ переменные
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_CHAT_ID=123456789

# Логирование и лимиты
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=20
MAX_VIDEO_SIZE_MB=300
SPAM_LIMIT=5

# Яндекс уведомления (опционально)
YANDEX_SMTP_ENABLED=false
YANDEX_SMTP_HOST=smtp.yandex.ru
YANDEX_SMTP_PORT=587
YANDEX_SMTP_USER=your_email@yandex.com
YANDEX_SMTP_PASSWORD=your_app_password
YANDEX_SMTP_USE_TLS=true

# Получатели уведомлений
INCIDENT_NOTIFICATION_EMAILS=admin@company.com
INCIDENT_NOTIFICATION_SMS_NUMBERS=+79000000000
```

**🔒 ВАЖНО:** Добавляйте переменные ТОЛЬКО через интерфейс Railway, не коммитьте их!

---

## 🔧 3. Деплой и запуск

### 3.1. Первый деплой

После добавления переменных:
1. Railway автоматически начнёт сборку
2. Следите за логами: **View Logs** → **Deploy Logs**
3. Ожидайте сообщения: `✅ Бот подключен: @your_bot_name`

### 3.2. Проверка статуса

В Railway Dashboard:
- **Зелёный статус** = бот работает ✅
- **Красный статус** = ошибка ❌ (смотрите логи)

### 3.3. Проверка логов

```bash
# В Railway Dashboard → View Logs
```

Ищите строки:
```
🚂 Запуск в Railway - пропуск блокировки процесса
✅ Бот подключен: @your_bot_username
Запуск polling...
```

---

## 🧪 4. Тест запуска бота

### 4.1. В Telegram

1. Найдите вашего бота: `@your_bot_username`
2. Отправьте `/start`
3. Проверьте все функции:
   - ❗ Сообщите об опасности
   - 🏠 Ближайшее укрытие
   - 🧑‍🏫 Консультант по безопасности
   - 💡 Предложение по улучшению

### 4.2. Проверка логов Railway

В Railway Dashboard → View Logs найдите:
```
USER:123456789 | Команда /start
USER:123456789 | Переход в главное меню
```

---

## 🔄 5. Автообновления через GitHub (Push = автодеплой)

### 5.1. Настройка автодеплоя

Railway автоматически отслеживает ваш GitHub-репозиторий.

**При каждом `git push` в ветку `main`:**
1. Railway обнаруживает изменения
2. Пересобирает проект
3. Перезапускает бота

### 5.2. Процесс обновления

```bash
# Внесли изменения в код
git add .
git commit -m "Улучшение функции X"
git push origin main

# Railway автоматически:
# 1. Клонирует новый код
# 2. Устанавливает зависимости
# 3. Перезапускает бота
```

### 5.3. Мониторинг деплоя

В Railway Dashboard:
- Следите за **Deployments** (список всех деплоев)
- Каждый деплой имеет:
  - Commit hash
  - Время
  - Статус (Success/Failed)

---

## 🛠️ 6. FAQ по стандартным ошибкам

### ❌ Ошибка: "Module not found"

**Причина:** Не установлены зависимости

**Решение:**
```bash
# Проверьте requirements.txt
cat requirements.txt

# Убедитесь, что все зависимости указаны:
pyTelegramBotAPI>=4.12.0
python-dotenv>=1.0.0
loguru>=0.7.0
requests>=2.31.0
psutil>=5.9.0
```

Закоммитьте изменения и запушьте:
```bash
git add requirements.txt
git commit -m "Обновление зависимостей"
git push origin main
```

---

### ❌ Ошибка: "401 Unauthorized" или "BOT_TOKEN не настроен"

**Причина:** Неверный токен или не установлена переменная

**Решение:**
1. Перейдите в Railway → Variables
2. Проверьте `BOT_TOKEN`:
   - Формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Без пробелов, кавычек
3. Получите новый токен у [@BotFather](https://t.me/BotFather), если нужно:
   ```
   /newbot - создать нового бота
   /token - получить токен существующего
   ```
4. Обновите переменную → **Restart Deployment**

---

### ❌ Ошибка: "409 Conflict: terminated by other getUpdates request"

**Причина:** Запущено несколько экземпляров бота

**Решение:**
1. Остановите локальную версию бота (если запущена)
2. В Railway: **Stop Deployment** → подождите 30 секунд → **Redeploy**
3. Проверьте, что токен не используется в других сервисах

---

### ❌ Ошибка: "pip install failed"

**Причина:** Проблема с зависимостями или версией Python

**Решение 1:** Проверьте `runtime.txt`
```bash
# Используйте стабильную версию
python-3.10.12
```

**Решение 2:** Закрепите версии зависимостей в `requirements.txt`
```
pyTelegramBotAPI==4.12.0
python-dotenv==1.0.0
loguru==0.7.2
requests==2.31.0
psutil==5.9.5
```

**Решение 3:** Очистите кэш Railway
```
Railway Dashboard → Settings → Reset Build Cache
```

---

### ❌ Ошибка: "Application failed to respond"

**Причина:** Бот не может запуститься (скорее всего ошибка в коде)

**Решение:**
1. Проверьте логи Railway: **View Logs** → **Deploy Logs**
2. Найдите трейсбэк ошибки
3. Исправьте код локально
4. Запушьте исправления:
   ```bash
   git add .
   git commit -m "Исправление ошибки"
   git push origin main
   ```

---

### ❌ Ошибка: "SSL Certificate verify failed"

**Причина:** Проблемы с SSL-сертификатами (редко на Railway)

**Решение:**
```python
# Уже есть в bot/main.py:
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

Если проблема сохраняется, добавьте переменную окружения:
```env
PYTHONHTTPSVERIFY=0
```

---

## 🔧 7. Полная команда для восстановления работы

### Если бот упал или не работает:

```bash
# Шаг 1: Проверьте статус в Railway Dashboard
# Шаг 2: Проверьте логи (View Logs)

# Шаг 3: Перезапуск через Railway UI
# Railway Dashboard → Redeploy

# Шаг 4: Если не помогло - ручной перезапуск
# Railway Dashboard → Settings → Restart

# Шаг 5: Если проблема сохраняется - пересоберите
# Railway Dashboard → Settings → Reset Build Cache → Redeploy
```

### Проверка переменных:

```bash
# В Railway Dashboard → Variables
# Убедитесь, что установлены:
BOT_TOKEN=ваш_токен
ADMIN_CHAT_ID=ваш_id
```

### Проверка логов:

```bash
# Ищите в логах Railway:
"❌" - ошибки
"⚠️" - предупреждения  
"✅" - успешные операции
```

---

## 🤖 8. CI/CD через GitHub Actions (Bonus)

### 8.1. Создайте `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --tb=short
      env:
        BOT_TOKEN: test_token
        ADMIN_CHAT_ID: 123456789
    
    - name: Check code quality
      run: |
        pip install flake8
        flake8 bot/ --max-line-length=120 --ignore=E501,W503
```

### 8.2. Активация:

```bash
mkdir -p .github/workflows
# Создайте файл test.yml с содержимым выше
git add .github/workflows/test.yml
git commit -m "Добавить CI/CD pipeline"
git push origin main
```

### 8.3. Результат:

- ✅ При каждом push запускаются тесты
- ✅ Pull Request не мержится без прохождения тестов
- ✅ Видите статус в GitHub (зелёная галочка или красный крестик)

---

## 📊 9. Мониторинг и аналитика

### 9.1. Метрики Railway

В Dashboard отслеживайте:
- **CPU Usage** - использование процессора
- **Memory Usage** - память
- **Network** - сетевая активность

### 9.2. Логи бота

Бот сохраняет логи в Railway (эфемерное хранилище):
```
logs/app.log - все события
logs/errors.log - ошибки
logs/user_actions.log - действия пользователей
```

**⚠️ ВАЖНО:** Railway не хранит файлы постоянно. Для постоянного хранения логов подключите:
- Railway Volumes (платно)
- Внешний сервис логирования (Sentry, LogDNA)

---

## 🎯 10. Checklist перед деплоем

- [ ] .env НЕ в репозитории
- [ ] .gitignore содержит `.env`, `*.log`, `bot.lock`, `bot.pid`
- [ ] Созданы файлы: Procfile, runtime.txt, railway.json
- [ ] requirements.txt содержит все зависимости
- [ ] Код работает локально: `python bot/main.py`
- [ ] Тесты проходят: `python -m pytest tests/`
- [ ] Токен бота действителен
- [ ] Переменные добавлены в Railway (Variables)
- [ ] GitHub репозиторий актуален: `git push`

---

## 🔐 11. Безопасность (Best Practice)

### ✅ DO:
- Используйте Railway Variables для всех секретов
- Используйте `.gitignore` для .env файлов
- Регулярно ротируйте токены (раз в 3-6 месяцев)
- Включите 2FA на GitHub
- Ограничьте доступ к Railway проекту

### ❌ DON'T:
- Никогда не коммитьте .env в Git
- Не храните токены в коде
- Не шарьте токены в чатах/email
- Не используйте один токен на dev и prod

---

## 📞 12. Поддержка

### Проблемы с Railway:
- Документация: https://docs.railway.app
- Discord: https://discord.gg/railway

### Проблемы с ботом:
- Telegram Bot API: https://core.telegram.org/bots/api
- pyTelegramBotAPI: https://github.com/eternnoir/pyTelegramBotAPI

### Ошибки в проекте:
- GitHub Issues: создайте issue в репозитории
- Логи: всегда проверяйте `logs/errors.log`

---

## ✅ Готово!

Ваш бот теперь работает на Railway 24/7 с автодеплоем из GitHub! 🎉

**Полезные команды:**
```bash
# Проверка статуса
git status

# Обновление бота
git add .
git commit -m "Описание изменений"
git push origin main

# Просмотр логов Railway
# Railway Dashboard → View Logs

# Перезапуск
# Railway Dashboard → Redeploy
```

---

*Последнее обновление: Октябрь 2025*

