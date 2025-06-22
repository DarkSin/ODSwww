from flask import Flask, render_template, redirect, url_for, flash, request, abort, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, PasswordReset, Module, RelayRequest, Tariff, UserSubscription
from auth import auth_bp
import os
from datetime import datetime, timedelta
import secrets
import api_client
import requests
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Регистрация blueprints
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        relay_id = request.form.get('relay_id')
        action = request.form.get('action')
        print(f"Received relay_id: {relay_id}, action: {action}")  # Отладочная информация
        
        if relay_id:  # Проверяем, что relay_id не пустой
            try:
                relay_id = int(relay_id)
                # Получаем все реле пользователя из БД
                relays = Module.query.filter_by(email=current_user.email).all()
                # Получаем список существующих реле из API
                try:
                    api_relays = api_client.get_relays()
                    api_ids = {str(r.get('relay_id')) for r in api_relays}
                    print(f"Available API relay IDs: {api_ids}")  # Отладочная информация
                except Exception as e:
                    print(f"API error: {e}")  # Отладочная информация
                    api_ids = set()
                
                if str(relay_id) not in api_ids:
                    flash(f'Реле с ID {relay_id} не найдено в системе', 'error')
                    return redirect(url_for('dashboard'))
                
                state = True if action == 'on' else False
                api_client.control_relay(relay_id, state)
                flash(f'Команда {"включить" if state else "выключить"} отправлена для реле {relay_id}', 'success')
                return redirect(url_for('dashboard'))
            except ValueError:
                flash('Неверный ID реле', 'error')
                return redirect(url_for('dashboard'))
        else:
            flash('ID реле не указан', 'error')
            return redirect(url_for('dashboard'))
    
    # Получаем все реле пользователя из БД
    relays = Module.query.filter_by(email=current_user.email).all()
    api_error = False
    # Получаем список существующих реле из API
    try:
        api_relays = api_client.get_relays()
        api_relays_dict = {str(r.get('relay_id')): r for r in api_relays}
        print(f"Available API relay IDs: {list(api_relays_dict.keys())}")  # Отладочная информация
    except Exception as e:
        print(f"API error: {e}")  # Отладочная информация
        api_relays_dict = {}
        api_error = True
    # Обновляем статусы реле и удаляем несуществующие только если API работает
    if not api_error:
        for relay in relays[:]:
            relay_id = relay.serial_number.replace('RELAY-', '')
            if relay_id in api_relays_dict:
                # Обновляем статус реле из API
                api_relay = api_relays_dict[relay_id]
                relay.status = 'on' if api_relay.get('state', False) else 'off'
            else:
                # Удаляем реле, которого нет в API
                db.session.delete(relay)
                relays.remove(relay)
        db.session.commit()
    try:
        logs = api_client.get_logs(limit=10) if not api_error else []
    except Exception:
        logs = []
        api_error = True
    my_requests = RelayRequest.query.filter_by(user_id=current_user.id).order_by(RelayRequest.created_at.desc()).all()
    # Подписка пользователя
    user_subscription = UserSubscription.query.filter_by(user_id=current_user.id, is_active=True).order_by(UserSubscription.end_date.desc()).first()
    tariffs = Tariff.query.all()
    now = datetime.utcnow()
    return render_template('dashboard.html', relays=relays, logs=logs, my_requests=my_requests, api_error=api_error, user_subscription=user_subscription, tariffs=tariffs, now=now)

@app.route('/dashboard/request-relay', methods=['POST'])
@login_required
def request_relay():
    relay_name = request.form.get('relay_name')
    phone_number = request.form.get('phone_number')
    description = request.form.get('description')
    if not relay_name or not phone_number:
        flash('Укажите название и номер телефона для нового реле', 'danger')
        return redirect(url_for('dashboard'))
    relay_request = RelayRequest(user_id=current_user.id, relay_name=relay_name, phone_number=phone_number, description=description)
    db.session.add(relay_request)
    db.session.commit()
    flash('Заявка на добавление реле отправлена!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    requests = RelayRequest.query.order_by(RelayRequest.created_at.desc()).all()
    return render_template('admin.html', users=users, requests=requests)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>/modules')
@login_required
def admin_user_modules(user_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    modules = Module.query.filter_by(email=user.email).all()
    # Проверяем наличие реле в API
    try:
        api_relays = api_client.get_relays()
        api_ids = {str(r.get('relay_id')) for r in api_relays}
    except Exception:
        api_ids = set()
    for module in modules[:]:
        relay_id = module.serial_number.replace('RELAY-', '')
        if relay_id not in api_ids:
            db.session.delete(module)
            modules.remove(module)
    db.session.commit()
    return render_template('admin_user_modules.html', user=user, modules=modules)

@app.route('/admin/requests')
@login_required
def admin_requests():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    # Для примера: заявки на добавление реле можно хранить в отдельной таблице, здесь просто заглушка
    requests = []
    return render_template('admin_requests.html', requests=requests)

@app.route('/admin/request-status/<int:request_id>', methods=['POST'])
@login_required
def admin_request_status(request_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    req = RelayRequest.query.get_or_404(request_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'approved', 'rejected']:
        req.status = new_status
        db.session.commit()
        flash('Статус заявки обновлен', 'success')
    else:
        flash('Некорректный статус', 'danger')
    return redirect(url_for('admin_panel'))

@app.route('/dashboard/request-edit/<int:request_id>', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    req = RelayRequest.query.get_or_404(request_id)
    if req.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        req.relay_name = request.form.get('relay_name')
        req.phone_number = request.form.get('phone_number')
        req.description = request.form.get('description')
        db.session.commit()
        flash('Заявка обновлена', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_request.html', req=req)

@app.route('/dashboard/request-delete/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    req = RelayRequest.query.get_or_404(request_id)
    if req.user_id != current_user.id:
        abort(403)
    db.session.delete(req)
    db.session.commit()
    flash('Заявка удалена', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/create-relay/<int:request_id>', methods=['GET', 'POST'])
@login_required
def admin_create_relay(request_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    req = RelayRequest.query.get_or_404(request_id)
    user = req.user
    if request.method == 'POST':
        relay_id = request.form.get('relay_id')
        name = request.form.get('name')
        description = request.form.get('description')
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        MO = request.form.get('MO')
        TP_RP = request.form.get('TP_RP')
        Activity = 'Activity' in request.form
        TimeOn = request.form.get('TimeOn')
        TimeOff = request.form.get('TimeOff')
        Status = request.form.get('Status')
        
        try:
            # Создаем реле через API
            api_client.create_relay({
                'relay_id': int(relay_id),
                'name': name,
                'description': description,
                'phone_number': phone_number,
                'password': password,
                'MO': MO,
                'TP_RP': TP_RP,
                'Activity': Activity,
                'TimeOn': TimeOn,
                'TimeOff': TimeOff,
                'Status': Status
            })
            
            # Создаем запись в БД
            module = Module(
                name=name,
                serial_number=f'RELAY-{relay_id}',
                phone_number=phone_number,
                status=Status,
                user_id=user.id,
                email=user.email
            )
            db.session.add(module)
            req.status = 'approved'
            db.session.commit()
            flash('Реле успешно создано и привязано к пользователю', 'success')
            return redirect(url_for('admin_panel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании реле: {str(e)}', 'danger')
            return render_template('admin_create_relay.html', req=req, user=user)
    
    return render_template('admin_create_relay.html', req=req, user=user)

@app.route('/admin/user/<int:user_id>/module/<int:module_id>/delete', methods=['POST'])
@login_required
def admin_delete_module(user_id, module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    # Удаляем из API
    api_url = f'http://10.8.1.7:9001/relays/{module.serial_number.replace("RELAY-", "")}'
    api_key = 'ac7ab11bb27eec55ddec772b5c8eab42917da842dfb4da80add15288ae58d4bb'
    headers = {'X-API-Key': api_key}
    try:
        requests.delete(api_url, headers=headers, timeout=10)
    except Exception:
        pass
    db.session.delete(module)
    db.session.commit()
    flash('Реле удалено', 'success')
    return redirect(url_for('admin_user_modules', user_id=user_id))

@app.route('/admin/user/<int:user_id>/module/<int:module_id>/control', methods=['POST'])
@login_required
def admin_control_module(user_id, module_id):
    if not current_user.is_admin:
        abort(403)
    module = Module.query.get_or_404(module_id)
    action = request.form.get('action')
    state = True if action == 'on' else False
    try:
        relay_id = int(module.serial_number.replace("RELAY-", ""))
        api_client.control_relay(relay_id, state)
        module.status = 'on' if state else 'off'
        db.session.commit()
        flash(f'Команда {"включить" if state else "выключить"} отправлена', 'success')
    except Exception as e:
        flash(f'Ошибка управления реле: {str(e)}', 'danger')
    return redirect(url_for('admin_user_modules', user_id=user_id))

@app.route('/admin/user/<int:user_id>/module/<int:module_id>/change-password', methods=['POST'])
@login_required
def admin_change_relay_password(user_id, module_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    module = Module.query.get_or_404(module_id)
    new_password = request.form.get('password')
    module.password = new_password
    db.session.commit()
    flash('Пароль реле успешно изменён', 'success')
    return redirect(url_for('admin_manage_user', user_id=user_id))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 'logo.svg', mimetype='image/svg+xml')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/buy-tariff/<int:tariff_id>', methods=['POST'])
@login_required
def buy_tariff(tariff_id):
    tariff = Tariff.query.get_or_404(tariff_id)
    now = datetime.utcnow()
    # Находим текущую активную подписку
    current_sub = UserSubscription.query.filter_by(user_id=current_user.id, is_active=True).order_by(UserSubscription.end_date.desc()).first()
    if current_sub and current_sub.end_date > now:
        if current_sub.tariff_id != tariff.id:
            flash('Продлить можно только текущий активный тариф!', 'danger')
            return redirect(url_for('buy_subscription'))
        # Продление: прибавляем срок к текущей дате окончания
        start_date = current_sub.end_date
        end_date = current_sub.end_date + timedelta(days=tariff.duration_days)
        # Деактивируем старую
        current_sub.is_active = False
    else:
        # Новая подписка
        start_date = now
        end_date = now + timedelta(days=tariff.duration_days)
        # Деактивируем все старые
        UserSubscription.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    new_sub = UserSubscription(user_id=current_user.id, tariff_id=tariff.id, start_date=start_date, end_date=end_date, is_active=True)
    db.session.add(new_sub)
    db.session.commit()
    flash(f'Вы успешно приобрели тариф: {tariff.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/buy-subscription')
@login_required
def buy_subscription():
    tariffs = Tariff.query.all()
    user_subscription = UserSubscription.query.filter_by(user_id=current_user.id, is_active=True).order_by(UserSubscription.end_date.desc()).first()
    now = datetime.utcnow()
    return render_template('buy_subscription.html', tariffs=tariffs, user_subscription=user_subscription, now=now)

@app.route('/admin/user/<int:user_id>/manage', methods=['GET'])
@login_required
def admin_manage_user(user_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    modules = Module.query.filter_by(user_id=user.id).all()
    subscriptions = UserSubscription.query.filter_by(user_id=user.id).order_by(UserSubscription.end_date.desc()).all()
    tariffs = Tariff.query.all()
    requests = RelayRequest.query.filter_by(user_id=user.id).order_by(RelayRequest.created_at.desc()).all()
    return render_template('admin_manage_user.html', user=user, modules=modules, subscriptions=subscriptions, tariffs=tariffs, requests=requests)

@app.route('/admin/user/<int:user_id>/set-password', methods=['POST'])
@login_required
def admin_set_user_password(user_id):
    if not current_user.is_admin:
        return '', 403
    user = User.query.get_or_404(user_id)
    password = request.form.get('password')
    user.set_password(password)
    db.session.commit()
    return '', 204

@app.route('/admin/user/<int:user_id>/module/<int:module_id>/edit', methods=['POST'])
@login_required
def admin_edit_module(user_id, module_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    module = Module.query.get_or_404(module_id)
    module.name = request.form.get('name')
    module.serial_number = request.form.get('serial_number')
    module.phone_number = request.form.get('phone_number')
    module.status = request.form.get('status')
    db.session.commit()
    flash('Реле успешно обновлено', 'success')
    return redirect(url_for('admin_manage_user', user_id=user_id))

@app.route('/admin/user/<int:user_id>/request/<int:request_id>/delete', methods=['POST'])
@login_required
def admin_delete_request(user_id, request_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    req = RelayRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    flash('Заявка удалена', 'success')
    return redirect(url_for('admin_manage_user', user_id=user_id))

@app.route('/admin/user/<int:user_id>/set-subscription', methods=['POST'])
@login_required
def admin_set_user_subscription(user_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    tariff_id = int(request.form.get('tariff_id'))
    end_date_str = request.form.get('end_date')
    tariff = Tariff.query.get_or_404(tariff_id)
    # Деактивируем все старые подписки
    UserSubscription.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
    # Создаём новую
    from datetime import datetime
    start_date = datetime.utcnow()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    new_sub = UserSubscription(user_id=user.id, tariff_id=tariff.id, start_date=start_date, end_date=end_date, is_active=True)
    db.session.add(new_sub)
    db.session.commit()
    flash('Подписка пользователя обновлена', 'success')
    return redirect(url_for('admin_manage_user', user_id=user_id))

if __name__ == '__main__':
    with app.app_context():
        # Автоматическая миграция поля email для Module
        engine = db.engine
        insp = inspect(engine)
        if 'module' in insp.get_table_names():
            columns = [col['name'] for col in insp.get_columns('module')]
            if 'email' not in columns:
                with engine.connect() as conn:
                    conn.execute(text('ALTER TABLE module ADD COLUMN email VARCHAR(120)'))
    app.run(debug=True)