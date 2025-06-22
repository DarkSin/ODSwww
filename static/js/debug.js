// Файл для отладки JavaScript
console.log('Debug.js загружен');

// Проверка наличия библиотеки JustValidate
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен');
    
    if (typeof JustValidate === 'undefined') {
        console.error('Библиотека JustValidate не загружена!');
    } else {
        console.log('Библиотека JustValidate загружена успешно');
    }
    
    // Проверка форм
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        console.log('Форма входа найдена');
        loginForm.addEventListener('submit', function(event) {
            console.log('Попытка отправки формы входа');
        });
    } else {
        console.error('Форма входа не найдена');
    }
    
    if (registerForm) {
        console.log('Форма регистрации найдена');
        registerForm.addEventListener('submit', function(event) {
            console.log('Попытка отправки формы регистрации');
        });
    } else {
        console.error('Форма регистрации не найдена');
    }
}); 