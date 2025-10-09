# 🚂 Деплой бота на Railway - Полная инструкция

## ⚡ БЫСТРЫЙ СТАРТ (5 минут)

### 1. Проверка готовности
```bash
python check_deploy_ready.py
```

### 2. Подготовка GitHub
```bash
git add .
git commit -m "Готов к Railway деплою"
git push origin main
```

### 3. Railway деплой
1. https://railway.app → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Выберите `RPRZbOT-main`
4. **Variables** → добавьте:
   ```
   BOT_TOKEN=ваш_токен_от_BotFather
   ADMIN_CHAT_ID=ваш_telegram_chat_id
   ```

### 4. Проверка
- Railway Dashboard → **View Logs** → ищите `✅ Бот подключен`
- Telegram → `/start` → проверьте работу

---

## 📚 Полная документация

### Основные документы:

1. **[DEPLOY_INDEX.md](DEPLOY_INDEX.md)** - Главная навигация по всем документам
2. **[RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)** - Быстрый старт (5 минут)
3. **[RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)** - Полное пошаговое руководство
4. **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Чеклист перед деплоем
5. **[RAILWAY_CLI_CHEATSHEET.md](RAILWAY_CLI_CHEATSHEET.md)** - Шпаргалка по CLI

### Автоматизация:

6. **[.github/workflows/README.md](.github/workflows/README.md)** - GitHub Actions CI/CD

---

## 🎯 Структура подготовки

### Созданные файлы для Railway:

```
RPRZbOT-main/
├── Procfile                       ✅ worker: python bot/main.py
├── runtime.txt                    ✅ python-3.10.12
├── railway.json                   ✅ Конфигурация Railway
├── .railwayignore                ✅ Исключения при деплое
├── check_deploy_ready.py          ✅ Скрипт проверки готовности
│
├── .github/workflows/             ✅ CI/CD
│   ├── tests.yml                 # Тесты + Code Quality
│   ├── railway-deploy.yml        # Проверка деплоя
│   └── README.md                 # Документация workflows
│
└── 📚 Документация:
    ├── RAILWAY_RU.md             ← Вы здесь (краткая версия)
    ├── DEPLOY_INDEX.md           # Навигация
    ├── RAILWAY_QUICKSTART.md     # 5 минут
    ├── RAILWAY_DEPLOY_GUIDE.md   # Полное руководство
    ├── RAILWAY_CLI_CHEATSHEET.md # CLI команды
    └── DEPLOY_CHECKLIST.md       # Чеклист
```

---

## 📖 ПОЛНОЕ ПОШАГОВОЕ РУКОВОДСТВО

### ЭТАП 1: Подготовка GitHub-репозитория

#### 1.1. Проверка файлов деплоя ✅

Все файлы уже созданы:
- `Procfile` - команда запуска бота
- `runtime.txt` - версия Python 3.10
- `railway.json` - конфигурация Railway
- `.railwayignore` - исключения (тесты, логи)
- `.gitignore` - защита секретов

#### 1.2. Проверка безопасности ✅

```bash
# Убедитесь, что .env НЕ в Git:
git ls-files .env
# Должно быть пусто!

# Если файл в Git - удалите:
git rm --cached .env
```

#### 1.3. Коммит и пуш

```bash
git add .
git commit -m "Подготовка к Railway деплою"
git push origin main
```

---

### ЭТАП 2: Настройки на Railway

#### 2.1. Создание проекта

1. Перейдите на https://railway.app
2. Войдите через GitHub
3. Нажмите **"New Project"**
4. Выберите **"Deploy from GitHub repo"**
5. Выберите репозиторий `RPRZbOT-main`
6. Railway автоматически обнаружит Python и начнёт сборку

#### 2.2. Добавление переменных окружения

**КРИТИЧНО:** Переменные добавляются ТОЛЬКО через Railway UI!

1. Railway Dashboard → **Variables**
2. Нажмите **"Add Variable"**
3. Добавьте (минимально):

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_CHAT_ID=123456789
```

**Опционально:**
```env
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=20
MAX_VIDEO_SIZE_MB=300
SPAM_LIMIT=5

# Яндекс уведомления (если нужны)
YANDEX_SMTP_ENABLED=false
YANDEX_SMTP_HOST=smtp.yandex.ru
YANDEX_SMTP_PORT=587
YANDEX_SMTP_USER=your_email@yandex.com
YANDEX_SMTP_PASSWORD=your_app_password
```

#### 2.3. Где взять значения переменных?

**BOT_TOKEN:**
1. Telegram → [@BotFather](https://t.me/BotFather)
2. `/newbot` или `/token`
3. Скопируйте токен (формат: `123456:ABC-DEF...`)

**ADMIN_CHAT_ID:**
1. Telegram → [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш ID (например: `123456789`)

---

### ЭТАП 3: Деплой

#### 3.1. Автоматический деплой

После добавления переменных Railway автоматически:
1. ✅ Клонирует репозиторий
2. ✅ Устанавливает Python 3.10 (из `runtime.txt`)
3. ✅ Устанавливает зависимости (из `requirements.txt`)
4. ✅ Запускает бота (команда из `Procfile`)

#### 3.2. Мониторинг деплоя

1. Railway Dashboard → **View Logs**
2. Следите за логами сборки:
   ```
   Installing Python 3.10.12...
   Installing dependencies from requirements.txt...
   Starting worker: python bot/main.py...
   ```
3. Ожидайте:
   ```
   🚂 Запуск в Railway - пропуск блокировки процесса
   ✅ Бот подключен: @your_bot_username
   Запуск polling...
   ```

#### 3.3. Статусы деплоя

- 🟢 **Success** - бот работает
- 🔴 **Failed** - ошибка (смотрите логи)
- 🟡 **Building** - идёт сборка

---

### ЭТАП 4: Тест запуска бота

#### 4.1. Проверка в Telegram

1. Найдите бота: `@your_bot_username`
2. Отправьте `/start`
3. Должно появиться:
   ```
   👋 Добро пожаловать в систему безопасности РПРЗ!
   
   Выберите действие из меню:
   ```
4. Проверьте все кнопки:
   - ❗ Сообщите об опасности
   - 🏠 Ближайшее укрытие
   - 🧑‍🏫 Консультант по безопасности РПРЗ
   - 💡 Предложение по улучшению

#### 4.2. Проверка функций

**Сообщение об опасности:**
- Текст описания ✅
- Прикрепить фото ✅
- Геолокация ✅

**Поиск укрытия:**
- Текстовый адрес ✅
- Геолокация ✅
- Показывает ближайшие убежища ✅

**Консультант:**
- Отвечает на вопросы ✅
- Показывает источники ✅

**Предложения:**
- Принимает текст ✅
- Отправляет админу ✅

#### 4.3. Проверка логов Railway

В Railway → **View Logs** должны быть:
```
USER:123456789 | Команда /start
USER:123456789 | Переход в главное меню
USER:123456789 | Выбрана функция: danger_report
```

---

### ЭТАП 5: Автообновления через GitHub (Push = автодеплой)

#### 5.1. Как работает автодеплой?

Railway автоматически отслеживает ваш GitHub-репозиторий.

**При каждом `git push` в ветку `main`:**
1. Railway получает webhook от GitHub
2. Клонирует новый код
3. Пересобирает проект
4. Перезапускает бота

**Никаких дополнительных действий не требуется!**

#### 5.2. Процесс обновления

```bash
# 1. Внесли изменения в код
nano bot/main.py

# 2. Закоммитили
git add .
git commit -m "Улучшена функция поиска укрытий"

# 3. Запушили
git push origin main

# 4. Railway автоматически деплоит!
```

#### 5.3. Мониторинг автодеплоя

1. Railway Dashboard → **Deployments**
2. Видите список всех деплоев:
   - Commit message
   - Commit hash
   - Время
   - Статус (Success/Failed)
   - Логи

#### 5.4. Откат к предыдущей версии

Если что-то сломалось:
1. Railway → **Deployments**
2. Найдите рабочую версию
3. Нажмите **"Redeploy"**

Или через Git:
```bash
git revert HEAD
git push origin main
```

---

### ЭТАП 6: CI/CD через GitHub Actions (опционально, но рекомендуется)

#### 6.1. Что уже настроено

В проекте созданы workflows:

**`.github/workflows/tests.yml`** - Запускается при каждом push/PR:
- ✅ Тесты (pytest)
- ✅ Покрытие кода (coverage)
- ✅ Качество кода (flake8, black, isort)
- ✅ Проверка безопасности (секреты, уязвимости)
- ✅ Готовность к деплою

**`.github/workflows/railway-deploy.yml`** - Проверка перед деплоем:
- ✅ Smoke tests
- ✅ Deploy readiness check
- ✅ Уведомления

#### 6.2. Как работает CI/CD

```
Разработчик → git push → GitHub
                             ↓
                    GitHub Actions запускаются
                             ↓
                    [Тесты] [Code Quality] [Security]
                             ↓
                       Все тесты ✅
                             ↓
                    Railway деплоит автоматически
                             ↓
                    Бот обновлён! 🎉
```

#### 6.3. Просмотр результатов

1. GitHub → **Actions** (вкладка)
2. Видите запущенные workflows
3. Зелёная галочка ✅ = всё ок
4. Красный крестик ❌ = есть ошибки (клик для деталей)

#### 6.4. Настройка защиты main ветки

Для продакшена рекомендуется:
1. GitHub → **Settings** → **Branches**
2. **Add rule** для `main`
3. Включите:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass (выберите tests.yml)
   - ✅ Include administrators

Теперь нельзя пушить напрямую в main без прохождения тестов!

---

## 🆘 FAQ ПО СТАНДАРТНЫМ ОШИБКАМ

### ❌ Ошибка импорта: "ModuleNotFoundError"

**Причина:** Зависимость не установлена

**Решение:**
```bash
# Локально проверьте requirements.txt:
cat requirements.txt

# Должны быть все пакеты:
pyTelegramBotAPI>=4.12.0
python-dotenv>=1.0.0
loguru>=0.7.0
requests>=2.31.0
psutil>=5.9.0

# Если чего-то не хватает:
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Обновление зависимостей"
git push origin main
```

---

### ❌ Ошибка логина: "401 Unauthorized"

**Причина:** Неверный BOT_TOKEN

**Решение:**
1. Проверьте токен в Railway Variables:
   - Формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Без пробелов, кавычек, переносов строк
2. Получите новый токен:
   - Telegram → [@BotFather](https://t.me/BotFather)
   - `/token` → выберите бота
3. Обновите в Railway:
   - Variables → BOT_TOKEN → Edit → Save
4. Перезапустите:
   - Railway → **Restart**

---

### ❌ Ошибка доступа к токену: "BOT_TOKEN не настроен"

**Причина:** Переменная не установлена в Railway

**Решение:**
1. Railway → Variables
2. Добавьте `BOT_TOKEN`
3. Добавьте `ADMIN_CHAT_ID`
4. Railway автоматически перезапустит бота

---

### ❌ Сбои pip: "ERROR: Could not install packages"

**Причина:** Конфликт зависимостей или проблемы с сетью

**Решение 1:** Закрепите версии
```
# requirements.txt
pyTelegramBotAPI==4.12.0
python-dotenv==1.0.0
loguru==0.7.2
requests==2.31.0
psutil==5.9.5
```

**Решение 2:** Очистите кэш Railway
```
Railway → Settings → Reset Build Cache → Redeploy
```

**Решение 3:** Проверьте Python версию
```
# runtime.txt должен быть:
python-3.10.12
```

---

### ❌ Конфликт: "409 Conflict: terminated by other getUpdates request"

**Причина:** Несколько экземпляров бота запущено

**Решение:**
1. Остановите локальный бот (если запущен)
2. Подождите 30-60 секунд
3. Railway → **Restart**
4. Проверьте, что токен не используется в других местах

**Примечание:** Код бота уже адаптирован для Railway (проверка `IS_RAILWAY`)

---

### ❌ Ошибка: ".env file in repository"

**Причина:** .env закоммичен в Git

**Решение:**
```bash
# Удалите из Git (НЕ из файловой системы):
git rm --cached .env

# Убедитесь, что в .gitignore есть:
echo ".env" >> .gitignore

# Закоммитьте:
git add .gitignore
git commit -m "Удалить .env из репозитория"
git push origin main
```

---

## 🔧 ПОЛНАЯ КОМАНДА ДЛЯ ВОССТАНОВЛЕНИЯ РАБОТЫ

### Бот упал или не работает?

```bash
# ШАГ 1: Проверка логов
# Railway Dashboard → View Logs
# Найдите ошибку (строки с ❌)

# ШАГ 2: Проверка переменных
# Railway → Variables → убедитесь:
# BOT_TOKEN=правильный_токен
# ADMIN_CHAT_ID=ваш_id

# ШАГ 3: Перезапуск
# Railway Dashboard → Restart

# ШАГ 4: Если не помогло - Redeploy
# Railway Dashboard → Deployments → Latest → Redeploy

# ШАГ 5: Если проблема сохраняется - пересборка
# Railway → Settings → Reset Build Cache
# Railway → Redeploy

# ШАГ 6: Локальная проверка
python check_deploy_ready.py
python bot/main.py  # Проверьте локально

# ШАГ 7: Откат к предыдущей версии
# Railway → Deployments → выберите рабочую → Redeploy
```

---

## 💡 СОВЕТЫ ПО АВТООБНОВЛЕНИЯМ

### Best Practices:

#### 1. Используйте ветки для разработки
```bash
# Создайте dev ветку:
git checkout -b develop
# Работайте в ней
git add .
git commit -m "WIP: новая функция"
git push origin develop

# После тестирования мержьте в main:
git checkout main
git merge develop
git push origin main  # Автодеплой!
```

#### 2. Используйте Pull Requests
- Создавайте PR из develop в main
- Проверяйте результаты CI/CD
- Мержьте только после прохождения тестов

#### 3. Мониторьте деплои
- После каждого push проверяйте Railway логи
- Первые 5-10 минут следите за ошибками
- Держите открытым Telegram бота для быстрой проверки

#### 4. Semantic Commit Messages
```bash
git commit -m "feat: добавлена функция X"
git commit -m "fix: исправлена ошибка Y"
git commit -m "docs: обновлена документация"
git commit -m "refactor: улучшен код Z"
```

#### 5. Versioning (опционально)
```bash
# Создавайте теги для релизов:
git tag -a v1.0.0 -m "Релиз 1.0.0"
git push origin v1.0.0
```

---

## 🎓 ИТОГОВЫЙ ЧЕКЛИСТ

### Перед деплоем:
- [ ] `python check_deploy_ready.py` проходит
- [ ] .env НЕ в Git
- [ ] Все файлы закоммичены
- [ ] `git push origin main` выполнен

### В Railway:
- [ ] Проект создан из GitHub
- [ ] BOT_TOKEN добавлен в Variables
- [ ] ADMIN_CHAT_ID добавлен в Variables
- [ ] Деплой завершился успешно (зелёный статус)
- [ ] В логах видно "✅ Бот подключен"

### После деплоя:
- [ ] `/start` в Telegram работает
- [ ] Все 4 функции бота работают
- [ ] Нет критических ошибок в логах
- [ ] Автодеплой настроен (GitHub → Railway)
- [ ] CI/CD работает (GitHub Actions)

---

## 📞 ПОЛЕЗНЫЕ ССЫЛКИ

- 🚂 **Railway:** https://railway.app
- 📖 **Railway Docs:** https://docs.railway.app
- 💬 **Railway Discord:** https://discord.gg/railway
- 🤖 **Telegram Bot API:** https://core.telegram.org/bots/api
- 🐍 **pyTelegramBotAPI:** https://github.com/eternnoir/pyTelegramBotAPI
- 🔧 **GitHub Actions:** https://docs.github.com/actions

---

## 🎉 ГОТОВО!

Ваш бот теперь работает на Railway 24/7 с автообновлениями из GitHub!

**Следующие шаги:**
1. Поделитесь ботом с пользователями
2. Мониторьте логи первые дни
3. Собирайте обратную связь
4. Планируйте новые функции
5. Масштабируйте по необходимости

---

**Полные инструкции:** [RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)

**Быстрый старт:** [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)

**Навигация:** [DEPLOY_INDEX.md](DEPLOY_INDEX.md)

---

*Создано для проекта RPRZ Safety Bot | Октябрь 2025*
