document.addEventListener('DOMContentLoaded', function() {
    // Тема: светлая/тёмная с localStorage и prefers-color-scheme
    const root = document.documentElement;
    const THEME_KEY = 'theme';
    const getStoredTheme = () => {
        const theme = localStorage.getItem(THEME_KEY);
        return theme === 'light' || theme === 'dark' ? theme : null;
    };
    const getPreferredTheme = () => (
        window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    );
    const applyTheme = (theme) => {
        const t = theme || getStoredTheme() || getPreferredTheme() || 'light';
        root.classList.toggle('theme-light', t === 'light');
        localStorage.setItem(THEME_KEY, t);
        const btn = document.querySelector('.theme-toggle .theme-icon');
        if (btn) btn.textContent = t === 'light' ? '☀️' : '🌙';
    };
    applyTheme();
    const toggleBtn = document.querySelector('.theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const current = root.classList.contains('theme-light') ? 'light' : 'dark';
            applyTheme(current === 'light' ? 'dark' : 'light');
        });
    }

    // Меню для мобильных устройств
    const menuBtn = document.querySelector('.menu-btn');
    const navLinks = document.querySelector('.nav-links');

    const setMenuState = (open) => {
        if (!menuBtn || !navLinks) return;
        menuBtn.classList.toggle('active', open);
        navLinks.classList.toggle('active', open);
        menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        document.body.classList.toggle('menu-open', open);
    };

    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', function() {
            const willOpen = !menuBtn.classList.contains('active');
            setMenuState(willOpen);
        });

        // Закрытие меню при клике на ссылку
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', function() {
                setMenuState(false);
            });
        });

        // Закрытие по клику вне меню
        document.addEventListener('click', (e) => {
            if (!navLinks.classList.contains('active')) return;
            const withinMenu = e.target.closest('.nav-links') || e.target.closest('.menu-btn');
            if (!withinMenu) setMenuState(false);
        });

        // Закрытие по Esc
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') setMenuState(false);
        });

        // Автозакрытие при ресайзе на десктоп
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) setMenuState(false);
        });
    }

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

    // Анимация элементов при скролле (reveal)
    const animateElements = document.querySelectorAll(
        '.hero h1, .hero p, .contact-info p, .service-card, .benefit-item, .section-title, .section-subtitle'
    );

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.12 });

    animateElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'all 0.6s ease-out';
        observer.observe(element);
    });

    // Плавное появление страницы
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';

    window.onload = function() {
        document.body.style.opacity = '1';
    };

    // Параллакс для фона хедера/hero
    const hero = document.querySelector('.hero');
    const heroBg = document.querySelector('.hero-bg');
    const heroGrid = document.querySelector('.hero-grid');

    const parallax = (x = 0, y = 0) => {
        if (!heroBg || !heroGrid) return;
        const dx = (x - window.innerWidth / 2) / window.innerWidth;
        const dy = (y - window.innerHeight / 2) / window.innerHeight;
        heroBg.style.transform = `translate3d(${dx * 20}px, ${dy * 20}px, 0)`;
        heroGrid.style.transform = `translate3d(${dx * -10}px, ${dy * -8}px, 0)`;
    };

    if (hero) {
        hero.addEventListener('mousemove', (e) => parallax(e.clientX, e.clientY));
        window.addEventListener('scroll', () => {
            const sc = Math.min(window.scrollY, 200);
            if (heroBg) heroBg.style.transform = `translateY(${sc * 0.08}px)`;
            if (heroGrid) heroGrid.style.transform = `translateY(${sc * -0.04}px)`;
        }, { passive: true });
    }

    // Лайтбокс для галереи на странице услуги
    const allGalleryLinks = () => Array.from(document.querySelectorAll('.gallery-grid .gallery-item'));
    if (allGalleryLinks().length) {
        let currentIndex = 0;
        let currentList = allGalleryLinks();
        // Создаем оверлей один раз
        let overlay = document.querySelector('.lightbox-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'lightbox-overlay';
            overlay.innerHTML = `
                <div class="lightbox-content">
                    <img class="lightbox-img" alt="preview" />
                    <div class="lightbox-caption" aria-live="polite"></div>
                    <button class="lightbox-close" aria-label="Закрыть">✕</button>
                    <button class="lightbox-prev" aria-label="Предыдущее">‹</button>
                    <button class="lightbox-next" aria-label="Следующее">›</button>
                </div>`;
            document.body.appendChild(overlay);
        }
        const imgEl = overlay.querySelector('.lightbox-img');
        const captionEl = overlay.querySelector('.lightbox-caption');
        const btnClose = overlay.querySelector('.lightbox-close');
        const btnPrev = overlay.querySelector('.lightbox-prev');
        const btnNext = overlay.querySelector('.lightbox-next');

        let scale = 1;
        let tx = 0, ty = 0;
        const minScale = 1, maxScale = 5, zoomStep = 0.2;
        const applyTransform = () => {
            imgEl.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
        };
        const resetTransform = () => { scale = 1; tx = 0; ty = 0; applyTransform(); };

        const rebuildCurrentList = () => {
            const visible = Array.from(document.querySelectorAll('.gallery-grid:not(.hidden) .gallery-item'));
            currentList = visible.length ? visible : allGalleryLinks();
        };

        const open = (idx) => {
            rebuildCurrentList();
            currentIndex = ((idx % currentList.length) + currentList.length) % currentList.length;
            const href = currentList[currentIndex].getAttribute('href');
            const cap = currentList[currentIndex].getAttribute('data-caption') || '';
            imgEl.src = href;
            if (captionEl) captionEl.textContent = cap;
            resetTransform();
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        };
        const close = () => {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        };
        const prev = () => open(currentIndex - 1);
        const next = () => open(currentIndex + 1);

        // Переопределим клики аккуратно, учитывая видимый альбом
        document.addEventListener('click', (e) => {
            const a = e.target.closest('.gallery-item');
            if (!a) return;
            if (!a.closest('.gallery-grid')) return;
            e.preventDefault();
            const visibleList = Array.from(document.querySelectorAll('.gallery-grid:not(.hidden) .gallery-item'));
            currentList = visibleList.length ? visibleList : allGalleryLinks();
            currentIndex = currentList.indexOf(a);
            open(currentIndex);
        }, true);

        btnClose.addEventListener('click', close);
        btnPrev.addEventListener('click', prev);
        btnNext.addEventListener('click', next);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
        window.addEventListener('keydown', (e) => {
            if (!overlay.classList.contains('active')) return;
            if (e.key === 'Escape') close();
            if (e.key === 'ArrowLeft') prev();
            if (e.key === 'ArrowRight') next();
        });

        const setScaleAtPoint = (nextScale, cx = imgEl.clientWidth / 2, cy = imgEl.clientHeight / 2) => {
            const prevScale = scale;
            scale = Math.min(maxScale, Math.max(minScale, nextScale));
            if (scale !== prevScale) {
                const rect = imgEl.getBoundingClientRect();
                const dx = cx - (rect.left + rect.width / 2);
                const dy = cy - (rect.top + rect.height / 2);
                const delta = scale - prevScale;
                tx -= (dx / prevScale) * delta;
                ty -= (dy / prevScale) * delta;
                applyTransform();
            }
        };
        const doZoom = (delta, cx = imgEl.clientWidth / 2, cy = imgEl.clientHeight / 2) => {
            setScaleAtPoint(scale + delta, cx, cy);
        };

        let dragging = false, sx = 0, sy = 0;
        const supportsFinePointer = window.matchMedia('(pointer: fine)').matches;
        if (supportsFinePointer) {
            // Wheel zoom (desktop/laptop pointers)
            imgEl.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = (e.deltaY < 0 ? zoomStep : -zoomStep);
                doZoom(delta, e.clientX, e.clientY);
            }, { passive: false });
            // Drag to pan (desktop/laptop pointers)
            imgEl.addEventListener('mousedown', (e) => {
                if (scale <= 1) return;
                dragging = true; sx = e.clientX; sy = e.clientY; imgEl.classList.add('dragging');
            });
            window.addEventListener('mousemove', (e) => {
                if (!dragging) return;
                const dx = e.clientX - sx; const dy = e.clientY - sy;
                sx = e.clientX; sy = e.clientY;
                tx += dx; ty += dy; applyTransform();
            });
            window.addEventListener('mouseup', () => { dragging = false; imgEl.classList.remove('dragging'); });
        }

        // Touch pinch-to-zoom and single-finger pan when zoomed
        const touchDistance = (t1, t2) => Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
        const touchMidpoint = (t1, t2) => ({
            x: (t1.clientX + t2.clientX) / 2,
            y: (t1.clientY + t2.clientY) / 2
        });
        let pinching = false;
        let touchPanning = false;
        let lastPinchDistance = 0;
        let lastTouchX = 0;
        let lastTouchY = 0;

        imgEl.addEventListener('touchstart', (e) => {
            if (e.touches.length === 2) {
                pinching = true;
                touchPanning = false;
                lastPinchDistance = touchDistance(e.touches[0], e.touches[1]);
            } else if (e.touches.length === 1 && scale > 1) {
                touchPanning = true;
                lastTouchX = e.touches[0].clientX;
                lastTouchY = e.touches[0].clientY;
            }
        }, { passive: true });

        imgEl.addEventListener('touchmove', (e) => {
            if (e.touches.length === 2) {
                e.preventDefault();
                const dist = touchDistance(e.touches[0], e.touches[1]);
                if (!lastPinchDistance) {
                    lastPinchDistance = dist;
                    return;
                }
                const ratio = dist / lastPinchDistance;
                const midpoint = touchMidpoint(e.touches[0], e.touches[1]);
                setScaleAtPoint(scale * ratio, midpoint.x, midpoint.y);
                lastPinchDistance = dist;
                pinching = true;
                touchPanning = false;
                return;
            }

            if (e.touches.length === 1 && scale > 1 && !pinching && touchPanning) {
                e.preventDefault();
                const x = e.touches[0].clientX;
                const y = e.touches[0].clientY;
                tx += x - lastTouchX;
                ty += y - lastTouchY;
                lastTouchX = x;
                lastTouchY = y;
                applyTransform();
            }
        }, { passive: false });

        imgEl.addEventListener('touchend', (e) => {
            if (e.touches.length < 2) {
                pinching = false;
                lastPinchDistance = 0;
            }
            if (e.touches.length === 0) touchPanning = false;
        }, { passive: true });
    }

    // Переключение альбомов на странице услуги
    const albumTabs = Array.from(document.querySelectorAll('.album-tabs .album-tab'));
    if (albumTabs.length) {
        const grids = Array.from(document.querySelectorAll('.gallery-grid[data-album]'));
        albumTabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const idx = tab.getAttribute('data-album-index');
                albumTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                grids.forEach(g => {
                    g.classList.toggle('hidden', g.getAttribute('data-album') !== idx);
                });
            });
        });
    }

    // Отправка формы заявки на странице услуги
    const feedbackForm = document.getElementById('feedback-form');
    if (feedbackForm) {
        const status = document.getElementById('feedback-status');
        feedbackForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            status.textContent = '';

            const formData = new FormData(feedbackForm);
            const payload = Object.fromEntries(formData.entries());

            // Простая проверка телефона: +7 или 8 и 10 цифр
            const tel = (payload.telephone || '').replace(/\s+/g, '');
            if (!/^(\+7|8)\d{10}$/.test(tel)) {
                status.textContent = 'Неверный телефон. Формат: +7XXXXXXXXXX или 8XXXXXXXXXX';
                status.style.color = '#b91c1c';
                return;
            }
            payload.telephone = tel;

            try {
                const res = await fetch('/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    status.textContent = 'Заявка отправлена. Мы свяжемся с вами.';
                    status.style.color = '#065f46';
                    feedbackForm.reset();
                } else {
                    status.textContent = data.message || 'Ошибка отправки. Попробуйте позже.';
                    status.style.color = '#b91c1c';
                }
            } catch (err) {
                status.textContent = 'Сбой сети. Попробуйте позже.';
                status.style.color = '#b91c1c';
            }
        });
    }

    // Fallback для отсутствующих изображений (плейсхолдер тёплой палитры)
    const placeholderSvg = encodeURIComponent(
      `<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>`+
      `<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>`+
      `<stop offset='0%' stop-color='#FAF7F2'/><stop offset='100%' stop-color='#E8DCCB'/></linearGradient></defs>`+
      `<rect width='100%' height='100%' fill='url(#g)'/>`+
      `<g fill='#C07A3A' font-family='Arial, sans-serif' text-anchor='middle'>`+
      `<text x='50%' y='50%' font-size='28' font-weight='700'>Фото будет позже</text>`+
      `</g></svg>`
    );
    const ph = `data:image/svg+xml;charset=utf-8,${placeholderSvg}`;
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', () => {
            if (img.dataset.fallbackApplied) return;
            img.dataset.fallbackApplied = '1';
            img.src = ph;
        });
    });
});



