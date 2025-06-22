# Система управления электрощитами через SMS

Веб-приложение для управления электрощитами через SMS-модули.

## Функциональность

- Регистрация и авторизация пользователей
- Восстановление пароля
- Управление модулями электрощитов
- Мониторинг событий и статусов
- Административная панель

## Технологии

- Flask - веб-фреймворк
- SQLAlchemy - ORM для работы с базой данных
- SQLite - база данных
- Flask-Login - аутентификация пользователей
- Bootstrap 5 - фронтенд фреймворк
- Font Awesome - иконки
- Just Validate - валидация форм

## Установка

1. Клонируйте репозиторий:
```
git clone https://github.com/yourusername/electrical-control.git
cd electrical-control
```

2. Создайте виртуальное окружение и активируйте его:
```
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```
pip install -r requirements.txt
```

4. Инициализируйте базу данных:
```
python init_db.py
```

## Запуск

1. Запустите приложение:
```
python app.py
```

2. Откройте браузер и перейдите по адресу:
```
http://localhost:5000
```

## Структура проекта

```
electrical-control/
├── app.py                 # Основной файл приложения
├── models.py              # Модели базы данных
├── auth.py                # Маршруты аутентификации
├── init_db.py             # Скрипт инициализации БД
├── requirements.txt       # Зависимости проекта
├── README.md              # Документация
├── static/                # Статические файлы
│   ├── css/               # CSS стили
│   ├── js/                # JavaScript файлы
│   └── img/               # Изображения
└── templates/             # HTML шаблоны
    ├── base.html          # Базовый шаблон
    ├── index.html         # Главная страница
    ├── login.html         # Страница входа
    ├── register.html      # Страница регистрации
    ├── forgot_password.html # Страница восстановления пароля
    ├── reset_password.html  # Страница сброса пароля
    └── dashboard.html     # Панель управления
```

## Лицензия

MIT 