// Инициализация AOS
AOS.init({
    duration: 800,
    easing: 'ease-in-out',
    once: true,
    mirror: false
});

// Обработка прокрутки для навигации
document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
    
    // Плавная прокрутка к секциям
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Валидация форм с Just Validate
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    const validation = new JustValidate(form);
    
    validation
        .addField('#email', [
            {
                rule: 'required',
                errorMessage: 'Email обязателен',
            },
            {
                rule: 'email',
                errorMessage: 'Введите корректный email',
            }
        ])
        .addField('#phone', [
            {
                rule: 'required',
                errorMessage: 'Телефон обязателен',
            },
            {
                rule: 'customRegexp',
                value: /^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$/,
                errorMessage: 'Введите корректный номер телефона',
            }
        ])
        .onSuccess((event) => {
            // Здесь будет логика отправки формы
            console.log('Форма валидна');
        });
});

// Обработка модальных окон
const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', function() {
        const targetModal = document.querySelector(this.getAttribute('data-bs-target'));
        if (targetModal) {
            const modal = new bootstrap.Modal(targetModal);
            modal.show();
        }
    });
});

// Анимация для карточек тарифов
const pricingCards = document.querySelectorAll('.card.popular');
pricingCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.05) translateY(-10px)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1.05)';
    });
});

// Функция для отображения уведомлений
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.appendChild(toast);
    document.body.appendChild(container);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

// Пример использования уведомлений
document.querySelectorAll('.btn-primary').forEach(button => {
    button.addEventListener('click', function() {
        showNotification('Операция успешно выполнена!', 'success');
    });
});
