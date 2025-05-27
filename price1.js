document.addEventListener('DOMContentLoaded', function() {
    // Меню для мобильных устройств
    const menuBtn = document.querySelector('.menu-btn');
    const navLinks = document.querySelector('.nav-links');

    menuBtn.addEventListener('click', function() {
        menuBtn.classList.toggle('active');
        navLinks.classList.toggle('active');
    });

    // Закрытие меню при клике на ссылку
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', function() {
            menuBtn.classList.remove('active');
            navLinks.classList.remove('active');
        });
    });

    // Плавная прокрутка к якорям
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            if (this.getAttribute('href') !== '#') {
                e.preventDefault();
                
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    window.scrollTo({
                        top: target.offsetTop,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Анимация элементов при скролле
    const animateElements = document.querySelectorAll('.hero h1, .hero p, .cta-button, .contact-info p');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1
    });

    animateElements.forEach(element => {
        observer.observe(element);
    });

    // Плавное появление страницы
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';

    window.onload = function() {
        document.body.style.opacity = '1';
    };
});
