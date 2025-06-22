from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, PasswordReset
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__)

def validate_phone(phone):
    pattern = r'^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$'
    return bool(re.match(pattern, phone))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Пожалуйста, проверьте ваш email и пароль и попробуйте снова.', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.is_active:
            flash('Ваш аккаунт заблокирован. Пожалуйста, свяжитесь с администратором.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not all([name, email, phone, password, password_confirm]):
            flash('Все поля обязательны для заполнения.', 'danger')
            return redirect(url_for('auth.register'))
            
        if not validate_phone(phone):
            flash('Неверный формат номера телефона. Используйте формат: +7 (XXX) XXX-XX-XX', 'danger')
            return redirect(url_for('auth.register'))
            
        if password != password_confirm:
            flash('Пароли не совпадают.', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован.', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(phone=phone).first():
            flash('Номер телефона уже зарегистрирован.', 'danger')
            return redirect(url_for('auth.register'))
            
        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            reset = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset)
            db.session.commit()
            
            # TODO: Отправить email с ссылкой для сброса пароля
            flash('Инструкции по восстановлению пароля отправлены на ваш email.', 'success')
            
        else:
            flash('Если указанный email зарегистрирован, инструкции по восстановлению пароля будут отправлены.', 'info')
            
        return redirect(url_for('auth.login'))
        
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    reset = PasswordReset.query.filter_by(token=token, is_used=False).first()
    
    if not reset or reset.expires_at < datetime.utcnow():
        flash('Ссылка для восстановления пароля недействительна или устарела.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Пароли не совпадают.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
            
        reset.user.set_password(password)
        reset.is_used = True
        db.session.commit()
        
        flash('Пароль успешно изменен. Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_password.html') 