# 📚 Документация по деплою RPRZ Safety Bot

## 🎯 Быстрая навигация

### Для новичков - начните здесь:
1. ⚡ **[RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)** - Деплой за 5 минут
2. ✅ **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Чеклист перед деплоем

### Полная документация:
3. 📖 **[RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)** - Подробное руководство
4. 🚂 **[RAILWAY_CLI_CHEATSHEET.md](RAILWAY_CLI_CHEATSHEET.md)** - Шпаргалка по CLI

### Автоматизация:
5. 🤖 **[.github/workflows/README.md](.github/workflows/README.md)** - CI/CD с GitHub Actions

---

## 🚀 Три способа деплоя

### 1. 🌐 Через Railway Web UI (Рекомендуется)
**Лучше для:** Новичков, быстрого старта

**Преимущества:**
- ✅ Визуальный интерфейс
- ✅ Не нужно устанавливать CLI
- ✅ Автодеплой из GitHub

**Инструкция:** [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)

---

### 2. 💻 Через Railway CLI
**Лучше для:** Разработчиков, частых деплоев

**Преимущества:**
- ✅ Быстрые команды из терминала
- ✅ Локальное тестирование с production переменными
- ✅ Просмотр логов в терминале

**Инструкция:** [RAILWAY_CLI_CHEATSHEET.md](RAILWAY_CLI_CHEATSHEET.md)

---

### 3. 🤖 Через GitHub Actions (CI/CD)
**Лучше для:** Команд, production проектов

**Преимущества:**
- ✅ Автоматическое тестирование
- ✅ Проверка качества кода
- ✅ Автодеплой после успешных тестов

**Инструкция:** [.github/workflows/README.md](.github/workflows/README.md)

---

## 📋 Структура файлов деплоя

```
RPRZbOT-main/
├── 📄 Procfile                    # Команда запуска для Railway
├── 📄 runtime.txt                 # Версия Python
├── 📄 railway.json                # Конфигурация Railway
├── 📄 .railwayignore             # Исключения при деплое
├── 📄 requirements.txt            # Python зависимости
├── 📄 check_deploy_ready.py      # Скрипт проверки готовности
│
├── 📁 .github/workflows/          # CI/CD автоматизация
│   ├── tests.yml                 # Тесты и проверки качества
│   ├── railway-deploy.yml        # Проверка деплоя
│   └── README.md                 # Документация workflows
│
└── 📚 Документация:
    ├── DEPLOY_INDEX.md           # ← Вы здесь
    ├── RAILWAY_QUICKSTART.md     # Быстрый старт
    ├── RAILWAY_DEPLOY_GUIDE.md   # Полное руководство
    ├── RAILWAY_CLI_CHEATSHEET.md # CLI команды
    └── DEPLOY_CHECKLIST.md       # Чеклист
```

---

## ⚡ Быстрый старт (5 минут)

### Шаг 1: Проверка готовности
```bash
python check_deploy_ready.py
```

### Шаг 2: Пуш в GitHub
```bash
git add .
git commit -m "Готов к деплою"
git push origin main
```

### Шаг 3: Деплой на Railway
1. Перейдите на https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Выберите `RPRZbOT-main`
4. **Variables** → добавьте `BOT_TOKEN` и `ADMIN_CHAT_ID`
5. Railway автоматически задеплоит бота

### Шаг 4: Проверка
```bash
# В Telegram:
/start

# В Railway:
View Logs → ищите "✅ Бот подключен"
```

---

## 🆘 Частые проблемы

| Проблема | Решение | Документ |
|----------|---------|----------|
| Бот не запускается | Проверьте `BOT_TOKEN` | [FAQ в RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md#6-faq-по-стандартным-ошибкам) |
| Ошибка зависимостей | Проверьте `requirements.txt` | [FAQ в RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md#-ошибка-pip-install-failed) |
| 409 Conflict | Остановите локальный бот | [FAQ в RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md#-ошибка-409-conflict-terminated-by-other-getupdates-request) |
| .env в Git | `git rm --cached .env` | [Безопасность в RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md#-11-безопасность-best-practice) |

---

## 🎓 Рекомендуемый порядок изучения

### Для новичков:
1. 📖 Прочитайте [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)
2. ✅ Пройдите [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
3. 🚀 Задеплойте бота
4. 📚 При проблемах: [RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)

### Для опытных:
1. 💻 Установите Railway CLI: [RAILWAY_CLI_CHEATSHEET.md](RAILWAY_CLI_CHEATSHEET.md)
2. 🤖 Настройте CI/CD: [.github/workflows/README.md](.github/workflows/README.md)
3. 🔄 Автоматизируйте деплой

---

## 🔒 Безопасность - ВАЖНО!

### ✅ ВСЕГДА:
- Используйте Railway Variables для секретов
- Добавляйте .env в .gitignore
- Проверяйте `git ls-files .env` перед push

### ❌ НИКОГДА:
- Не коммитьте .env в Git
- Не храните токены в коде
- Не используйте production токены локально

**Подробнее:** [Раздел Безопасность в RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md#-11-безопасность-best-practice)

---

## 📊 Checklist успешного деплоя

После деплоя убедитесь:

- [ ] Бот отвечает на `/start` в Telegram
- [ ] В Railway логах нет критических ошибок
- [ ] Все 4 функции бота работают
- [ ] Автодеплой из GitHub настроен
- [ ] GitHub Actions тесты проходят (если настроены)
- [ ] Переменные окружения корректны

---

## 🛠️ Инструменты

### Проверка готовности к деплою
```bash
python check_deploy_ready.py
```

### Локальный запуск с Railway переменными
```bash
railway run python bot/main.py
```

### Просмотр логов Railway
```bash
railway logs
```

---

## 📞 Поддержка

### Проблемы с Railway:
- 📖 [Railway Docs](https://docs.railway.app)
- 💬 [Railway Discord](https://discord.gg/railway)

### Проблемы с ботом:
- 📖 [Telegram Bot API](https://core.telegram.org/bots/api)
- 📚 [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)

### Проблемы с проектом:
- 🐛 GitHub Issues в репозитории
- 📧 Свяжитесь с командой разработки

---

## 🎯 Следующие шаги после деплоя

1. ⭐ Мониторьте логи первые 24 часа
2. 📊 Соберите обратную связь от пользователей
3. 🔄 Настройте автодеплой (если ещё не сделано)
4. 🤖 Настройте CI/CD с тестами
5. 📈 Планируйте новые функции

---

## 📝 История изменений

### Версия 1.0 (Октябрь 2025)
- ✅ Полная документация по деплою на Railway
- ✅ CI/CD с GitHub Actions
- ✅ Скрипты автоматизации
- ✅ FAQ и troubleshooting
- ✅ Railway CLI шпаргалка

---

**🎉 Готово! Выберите подходящий способ деплоя и начните!**

*Для быстрого старта → [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)*

*Для полной информации → [RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)*

---

*Последнее обновление: Октябрь 2025*

