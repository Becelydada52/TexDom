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

    // Плавный переход между страницами
    document.querySelectorAll('a[href^="main"], a[href^="price"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });

    // Переходы на страницы с ценами
    document.querySelectorAll('.price-item button').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.id;
            let href = '';
            if (id === '1') {
                href = 'price1.html';
            } else if (id === '2') {
                href = 'price2.html';
            } else if (id === '3') {
                href = 'price3.html';
            }
            if (href) {
                document.body.style.opacity = '0';
                document.body.style.transition = 'opacity 0.3s ease';
                
                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });

    // Плавная прокрутка к контактам с анимацией
    document.querySelectorAll('.nav-links a[href="#contact"], .cta-button[href="#contact"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Затемнение страницы перед прокруткой
            document.body.style.transition = 'opacity 0.1s ease';
            
            setTimeout(() => {
                const contactSection = document.querySelector('#contact');
                if (contactSection) {
                    contactSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
                
                // Возвращаем прозрачность после прокрутки
                setTimeout(() => {
                    document.body.style.opacity = '1';
                }, 500);
            }, 300);
        });
    });

    // Анимация появления элементов при скролле
    const animateElements = document.querySelectorAll('.price-item, .cta-section, .page-navigation, footer');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });

    animateElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'all 0.6s ease-out';
        observer.observe(element);
    });
});
