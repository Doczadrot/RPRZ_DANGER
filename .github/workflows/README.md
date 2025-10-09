# 🤖 GitHub Actions Workflows

## 📋 Доступные Workflows

### 1. 🧪 Tests & Code Quality (`tests.yml`)

**Запускается при:**
- Push в ветки `main`, `develop`
- Pull Request в `main`

**Что делает:**
- ✅ Запускает все тесты проекта
- 📊 Генерирует отчёт о покрытии кода
- 🔍 Проверяет качество кода (flake8, black, isort)
- 🔒 Проверяет безопасность (секреты, уязвимости)
- 🚀 Проверяет готовность к деплою

**Результаты:**
- Зелёная галочка ✅ = все тесты прошли
- Красный крестик ❌ = есть ошибки

---

### 2. 🚂 Railway Deploy (`railway-deploy.yml`)

**Запускается при:**
- Push в ветку `main`
- Ручной запуск (workflow_dispatch)

**Что делает:**
- 🧪 Быстрые smoke-тесты
- 🔍 Проверка готовности к деплою
- 📢 Уведомление о статусе

**Примечание:** Railway автоматически деплоит из GitHub, этот workflow просто проверяет готовность.

---

## 🚀 Как использовать

### Автоматический запуск

Workflows запускаются автоматически при push/PR. Ничего делать не нужно!

### Ручной запуск

1. Перейдите в GitHub → **Actions**
2. Выберите workflow (например, "Railway Deploy")
3. Нажмите **Run workflow**

---

## 📊 Просмотр результатов

1. GitHub → **Actions**
2. Выберите конкретный workflow run
3. Посмотрите детали каждого job

---

## 🔧 Настройка

### Добавление новых тестов

Добавьте тесты в `tests/` - они автоматически подхватятся.

### Изменение Python версии

Отредактируйте в workflow:
```yaml
python-version: ['3.10', '3.11']  # добавьте нужные версии
```

### Добавление секретов

Для использования секретов в Actions:
1. GitHub → Settings → Secrets → Actions
2. New repository secret
3. Используйте в workflow: `${{ secrets.SECRET_NAME }}`

---

## ⚠️ Важные замечания

- **НЕ добавляйте** реальные токены в workflows
- **НЕ отключайте** security checks
- **Всегда проверяйте** результаты перед мержем в main

---

## 🐛 Troubleshooting

### Тесты падают в CI, но работают локально

```bash
# Проверьте переменные окружения
# В CI используются тестовые значения:
BOT_TOKEN=test_token
ADMIN_CHAT_ID=123456789
```

### Workflow не запускается

- Проверьте синтаксис YAML
- Убедитесь, что файл в `.github/workflows/`
- Проверьте права доступа к репозиторию

---

## 📖 Полезные ссылки

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Railway Docs](https://docs.railway.app)

---

*Последнее обновление: Октябрь 2025*

