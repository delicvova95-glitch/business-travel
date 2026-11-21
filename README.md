# Business Travel

Сайт туристического агентства Business Travel (Томск): корпоративные мероприятия,
деловые поездки и индивидуальные путешествия.

## Технологии

- **Backend:** Flask (Python), SQLite
- **Frontend:** HTML/CSS, vanilla JavaScript, Three.js (3D-сцена первого экрана: Земля и самолёт)
- Без React/Vite/GSAP/Node.js

## Запуск

```bash
pip install -r requirements.txt
SECRET_KEY="dev-secret" ADMIN_PASSWORD="admin-password" python app.py
```

Сайт будет доступен на http://127.0.0.1:5000. Админ-панель — на `/admin`
(логин `admin`, пароль — из переменной `ADMIN_PASSWORD`).

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `SECRET_KEY` | Секретный ключ сессий Flask |
| `ADMIN_PASSWORD` | Пароль входа в админ-панель |
| `TELEGRAM_BOT_TOKEN` | Токен бота для уведомлений о заявках (опционально) |
| `TELEGRAM_CHAT_ID` | Chat ID для уведомлений (опционально) |
| `TEMPLATES_AUTO_RELOAD` | `1` — перечитывать шаблоны без перезапуска (разработка) |

## Структура

- `app.py` — маршруты публичной части и API заявок
- `admin.py` — админ-панель (заявки, настройки)
- `db.py`, `data/app.db` — слой данных SQLite (БД не хранится в репозитории)
- `security.py` — CSRF, лимитеры
- `telegram_notify.py` — уведомления о заявках в Telegram
- `templates/`, `static/` — шаблоны, стили, скрипты, изображения и 3D-модели
- `static/js/globe.js` — 3D-сцена первого экрана (Three.js, загружается только на десктопе)

## Мобильная версия

На смартфонах (≤720px) 3D-сцена не загружается — вместо неё показывается
статичный кадр (`static/img/hero-static.jpg`). Расширенные описания услуг
на главной скрыты, навигация дублируется нижней панелью.
