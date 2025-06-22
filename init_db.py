from app import app, db
from models import User, Tariff

def init_db():
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Проверяем, есть ли уже пользователи в базе
        if User.query.first() is None:
            # Создаем тестового администратора
            admin = User(
                name='Администратор',
                email='admin@example.com',
                phone='+7 (999) 999-99-99',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Создан тестовый администратор:")
            print("Email: admin@example.com")
            print("Пароль: admin123")
        
        print("База данных успешно инициализирована!")

        # Добавляем тарифы, если их нет
        if Tariff.query.count() == 0:
            tariffs = [
                Tariff(name='3 месяца', price=2990, duration_days=90, module_limit=5, description='До 5 модулей. Базовый функционал. Email поддержка.'),
                Tariff(name='6 месяцев', price=4990, duration_days=180, module_limit=10, description='До 10 модулей. Расширенный функционал. Приоритетная поддержка.'),
                Tariff(name='12 месяцев', price=8990, duration_days=365, module_limit=None, description='Неограниченное количество. Все функции. 24/7 поддержка.')
            ]
            db.session.add_all(tariffs)
            db.session.commit()
            print("Тарифы успешно добавлены!")

if __name__ == '__main__':
    init_db() 