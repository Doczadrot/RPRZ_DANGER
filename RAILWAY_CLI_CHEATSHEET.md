# 🚂 Railway CLI - Шпаргалка

## 📦 Установка Railway CLI

### Windows (PowerShell)
```powershell
iwr https://railway.app/install.ps1 | iex
```

### Linux/Mac
```bash
sh -c "$(curl -fsSL https://railway.app/install.sh)"
```

### Проверка установки
```bash
railway --version
```

---

## 🔐 Аутентификация

### Вход в Railway
```bash
railway login
```
*Откроется браузер для авторизации через GitHub*

### Проверка авторизации
```bash
railway whoami
```

---

## 📁 Работа с проектами

### Список проектов
```bash
railway list
```

### Привязать проект к текущей папке
```bash
railway link
```
*Выберите проект из списка*

### Создать новый проект
```bash
railway init
```

### Информация о проекте
```bash
railway status
```

---

## 🚀 Деплой

### Деплой текущей папки
```bash
railway up
```

### Деплой из конкретной ветки
```bash
railway up --detach
```

### Просмотр деплоев
```bash
railway deployment list
```

---

## 🔧 Переменные окружения

### Список переменных
```bash
railway variables
```

### Добавить переменную
```bash
railway variables set BOT_TOKEN=1234567890:ABCdefGHI
```

### Удалить переменную
```bash
railway variables delete BOT_TOKEN
```

### Импорт из .env (локально)
```bash
railway variables set $(cat .env | xargs)
```

**⚠️ ОСТОРОЖНО:** Убедитесь, что .env не содержит чувствительных данных перед публикацией!

---

## 📊 Логи

### Просмотр логов (real-time)
```bash
railway logs
```

### Логи за последний час
```bash
railway logs --time 1h
```

### Сохранить логи в файл
```bash
railway logs > railway_logs.txt
```

---

## 🔄 Управление сервисом

### Перезапуск
```bash
railway restart
```

### Остановка
```bash
railway down
```

### Запуск
```bash
railway up
```

---

## 🌐 Подключение к окружению

### Локальный запуск с переменными Railway
```bash
railway run python bot/main.py
```
*Загружает переменные из Railway и запускает локально*

### Открыть shell с переменными Railway
```bash
railway run bash
```

### Выполнить команду с переменными Railway
```bash
railway run python check_deploy_ready.py
```

---

## 🔍 Отладка

### Подключение к базе данных (если есть)
```bash
railway connect
```

### Проверка окружения
```bash
railway run env
```

### Проверка сборки
```bash
railway logs --deployment
```

---

## ⚙️ Расширенные команды

### Открыть проект в браузере
```bash
railway open
```

### Открыть Dashboard
```bash
railway dashboard
```

### Открыть логи в браузере
```bash
railway logs --web
```

### Генерация конфига
```bash
railway init --config
```

---

## 🐛 Troubleshooting

### Ошибка: "No project found"
```bash
# Привяжите проект:
railway link

# Или создайте новый:
railway init
```

### Ошибка: "Not authenticated"
```bash
# Войдите снова:
railway login
```

### Деплой зависает
```bash
# Проверьте логи:
railway logs

# Остановите и перезапустите:
railway down
railway up
```

---

## 📖 Полезные сочетания команд

### Деплой с просмотром логов
```bash
railway up && railway logs
```

### Быстрая проверка статуса и логов
```bash
railway status && railway logs --time 5m
```

### Обновление переменных и перезапуск
```bash
railway variables set KEY=VALUE && railway restart
```

---

## 🔒 Безопасность

### НЕ делайте так:
```bash
# НЕ коммитьте .env!
git add .env  # ❌

# НЕ публикуйте токены в логах!
echo $BOT_TOKEN  # ❌

# НЕ используйте production токены локально!
export BOT_TOKEN=prod_token  # ❌
```

### Делайте так:
```bash
# Используйте Railway для production секретов ✅
railway variables set BOT_TOKEN=...

# Используйте .env.local для локальной разработки ✅
# (добавьте в .gitignore)

# Используйте railway run для локального тестирования ✅
railway run python bot/main.py
```

---

## 📚 Дополнительные ресурсы

- 📖 [Railway CLI Docs](https://docs.railway.app/develop/cli)
- 🎓 [Railway Guides](https://docs.railway.app/guides)
- 💬 [Railway Discord](https://discord.gg/railway)

---

## 🎯 Типичный workflow

```bash
# 1. Инициализация (один раз)
railway login
railway link

# 2. Разработка
# Работаете над кодом локально

# 3. Тестирование с Railway переменными
railway run python bot/main.py

# 4. Деплой
git add .
git commit -m "Новая функция"
git push origin main
# Railway автоматически задеплоит

# 5. Проверка
railway logs

# 6. При необходимости - ручной деплой
railway up
```

---

**💡 Совет:** Railway CLI удобен для разработки, но для production лучше использовать автодеплой из GitHub!

*Последнее обновление: Октябрь 2025*

