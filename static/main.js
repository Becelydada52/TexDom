document.addEventListener('DOMContentLoaded', () => {
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
        const resolvedTheme = theme || getStoredTheme() || getPreferredTheme() || 'light';
        root.classList.toggle('theme-light', resolvedTheme === 'light');
        localStorage.setItem(THEME_KEY, resolvedTheme);

        const icon = document.querySelector('.theme-toggle .theme-icon');
        if (icon) {
            icon.textContent = resolvedTheme === 'light' ? '☀️' : '🌙';
        }
    };

    applyTheme();

    const toggleBtn = document.querySelector('.theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const current = root.classList.contains('theme-light') ? 'light' : 'dark';
            applyTheme(current === 'light' ? 'dark' : 'light');
        });
    }

    const menuBtn = document.querySelector('.menu-btn');
    const navLinks = document.querySelector('.nav-links');

    const setMenuState = (open) => {
        if (!menuBtn || !navLinks) {
            return;
        }

        menuBtn.classList.toggle('active', open);
        navLinks.classList.toggle('active', open);
        menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        document.body.classList.toggle('menu-open', open);
    };

    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', () => {
            setMenuState(!menuBtn.classList.contains('active'));
        });

        document.querySelectorAll('.nav-links a').forEach((link) => {
            link.addEventListener('click', () => setMenuState(false));
        });

        document.addEventListener('click', (event) => {
            if (!navLinks.classList.contains('active')) {
                return;
            }

            const withinMenu = event.target.closest('.nav-links') || event.target.closest('.menu-btn');
            if (!withinMenu) {
                setMenuState(false);
            }
        });

        window.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                setMenuState(false);
            }
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                setMenuState(false);
            }
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function(event) {
            const href = this.getAttribute('href');
            if (!href || href === '#') {
                return;
            }

            const target = document.querySelector(href);
            if (!target) {
                return;
            }

            event.preventDefault();
            window.scrollTo({
                top: target.offsetTop,
                behavior: 'smooth',
            });
        });
    });

    const animateElements = document.querySelectorAll(
        '.hero h1, .hero p, .contact-info p, .service-card, .benefit-item, .section-title, .section-subtitle, .trust-item, .market-card, .scope-item, .process-step, .project-card, .faq-item, .contact-card, .cta-banner, .hero-panel-card, .hero-badge'
    );

    if (animateElements.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.12 });

        animateElements.forEach((element) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'all 0.6s ease-out';
            observer.observe(element);
        });
    }

    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';
    window.addEventListener('load', () => {
        document.body.style.opacity = '1';
    });

    const hero = document.querySelector('.hero');
    const heroBg = document.querySelector('.hero-bg');
    const heroGrid = document.querySelector('.hero-grid');

    const parallax = (x = 0, y = 0) => {
        if (!heroBg || !heroGrid) {
            return;
        }

        const dx = (x - window.innerWidth / 2) / window.innerWidth;
        const dy = (y - window.innerHeight / 2) / window.innerHeight;
        heroBg.style.transform = `translate3d(${dx * 20}px, ${dy * 20}px, 0)`;
        heroGrid.style.transform = `translate3d(${dx * -10}px, ${dy * -8}px, 0)`;
    };

    if (hero) {
        hero.addEventListener('mousemove', (event) => parallax(event.clientX, event.clientY));
        window.addEventListener('scroll', () => {
            const scrolled = Math.min(window.scrollY, 200);
            if (heroBg) {
                heroBg.style.transform = `translateY(${scrolled * 0.08}px)`;
            }
            if (heroGrid) {
                heroGrid.style.transform = `translateY(${scrolled * -0.04}px)`;
            }
        }, { passive: true });
    }

    const galleryToggle = document.querySelector('[data-gallery-toggle]');
    const serviceGallery = document.getElementById('service-gallery');
    if (galleryToggle && serviceGallery) {
        galleryToggle.addEventListener('click', () => {
            const willOpen = serviceGallery.hasAttribute('hidden');

            if (willOpen) {
                serviceGallery.removeAttribute('hidden');
            } else {
                serviceGallery.setAttribute('hidden', '');
            }

            galleryToggle.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
            galleryToggle.textContent = willOpen ? 'Скрыть фото' : 'Посмотреть фото';

            if (willOpen) {
                serviceGallery.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    const allGalleryLinks = () => Array.from(document.querySelectorAll('.gallery-grid .gallery-item'));
    if (allGalleryLinks().length) {
        let currentIndex = 0;
        let currentList = allGalleryLinks();

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
        let tx = 0;
        let ty = 0;
        const minScale = 1;
        const maxScale = 5;
        const zoomStep = 0.2;

        const applyTransform = () => {
            imgEl.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
        };

        const resetTransform = () => {
            scale = 1;
            tx = 0;
            ty = 0;
            applyTransform();
        };

        const rebuildCurrentList = () => {
            currentList = allGalleryLinks();
        };

        const open = (index) => {
            rebuildCurrentList();
            currentIndex = ((index % currentList.length) + currentList.length) % currentList.length;
            const href = currentList[currentIndex].getAttribute('href');
            const caption = currentList[currentIndex].getAttribute('data-caption') || '';
            imgEl.src = href;
            captionEl.textContent = caption;
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

        document.addEventListener('click', (event) => {
            const link = event.target.closest('.gallery-item');
            if (!link || !link.closest('.gallery-grid')) {
                return;
            }

            event.preventDefault();
            currentList = allGalleryLinks();
            currentIndex = currentList.indexOf(link);
            open(currentIndex);
        }, true);

        btnClose.addEventListener('click', close);
        btnPrev.addEventListener('click', prev);
        btnNext.addEventListener('click', next);

        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) {
                close();
            }
        });

        window.addEventListener('keydown', (event) => {
            if (!overlay.classList.contains('active')) {
                return;
            }

            if (event.key === 'Escape') {
                close();
            }
            if (event.key === 'ArrowLeft') {
                prev();
            }
            if (event.key === 'ArrowRight') {
                next();
            }
        });

        const setScaleAtPoint = (nextScale, cx = imgEl.clientWidth / 2, cy = imgEl.clientHeight / 2) => {
            const prevScale = scale;
            scale = Math.min(maxScale, Math.max(minScale, nextScale));
            if (scale === prevScale) {
                return;
            }

            const rect = imgEl.getBoundingClientRect();
            const dx = cx - (rect.left + rect.width / 2);
            const dy = cy - (rect.top + rect.height / 2);
            const delta = scale - prevScale;
            tx -= (dx / prevScale) * delta;
            ty -= (dy / prevScale) * delta;
            applyTransform();
        };

        const doZoom = (delta, cx = imgEl.clientWidth / 2, cy = imgEl.clientHeight / 2) => {
            setScaleAtPoint(scale + delta, cx, cy);
        };

        let dragging = false;
        let sx = 0;
        let sy = 0;
        const supportsFinePointer = window.matchMedia('(pointer: fine)').matches;

        if (supportsFinePointer) {
            imgEl.addEventListener('wheel', (event) => {
                event.preventDefault();
                const delta = event.deltaY < 0 ? zoomStep : -zoomStep;
                doZoom(delta, event.clientX, event.clientY);
            }, { passive: false });

            imgEl.addEventListener('mousedown', (event) => {
                if (scale <= 1) {
                    return;
                }

                dragging = true;
                sx = event.clientX;
                sy = event.clientY;
                imgEl.classList.add('dragging');
            });

            window.addEventListener('mousemove', (event) => {
                if (!dragging) {
                    return;
                }

                const dx = event.clientX - sx;
                const dy = event.clientY - sy;
                sx = event.clientX;
                sy = event.clientY;
                tx += dx;
                ty += dy;
                applyTransform();
            });

            window.addEventListener('mouseup', () => {
                dragging = false;
                imgEl.classList.remove('dragging');
            });
        }

        const touchDistance = (touchA, touchB) => Math.hypot(
            touchB.clientX - touchA.clientX,
            touchB.clientY - touchA.clientY,
        );

        const touchMidpoint = (touchA, touchB) => ({
            x: (touchA.clientX + touchB.clientX) / 2,
            y: (touchA.clientY + touchB.clientY) / 2,
        });

        let pinching = false;
        let touchPanning = false;
        let lastPinchDistance = 0;
        let lastTouchX = 0;
        let lastTouchY = 0;

        imgEl.addEventListener('touchstart', (event) => {
            if (event.touches.length === 2) {
                pinching = true;
                touchPanning = false;
                lastPinchDistance = touchDistance(event.touches[0], event.touches[1]);
            } else if (event.touches.length === 1 && scale > 1) {
                touchPanning = true;
                lastTouchX = event.touches[0].clientX;
                lastTouchY = event.touches[0].clientY;
            }
        }, { passive: true });

        imgEl.addEventListener('touchmove', (event) => {
            if (event.touches.length === 2) {
                event.preventDefault();
                const dist = touchDistance(event.touches[0], event.touches[1]);
                if (!lastPinchDistance) {
                    lastPinchDistance = dist;
                    return;
                }

                const ratio = dist / lastPinchDistance;
                const midpoint = touchMidpoint(event.touches[0], event.touches[1]);
                setScaleAtPoint(scale * ratio, midpoint.x, midpoint.y);
                lastPinchDistance = dist;
                pinching = true;
                touchPanning = false;
                return;
            }

            if (event.touches.length === 1 && scale > 1 && !pinching && touchPanning) {
                event.preventDefault();
                const x = event.touches[0].clientX;
                const y = event.touches[0].clientY;
                tx += x - lastTouchX;
                ty += y - lastTouchY;
                lastTouchX = x;
                lastTouchY = y;
                applyTransform();
            }
        }, { passive: false });

        imgEl.addEventListener('touchend', (event) => {
            if (event.touches.length < 2) {
                pinching = false;
                lastPinchDistance = 0;
            }
            if (event.touches.length === 0) {
                touchPanning = false;
            }
        }, { passive: true });
    }

    const feedbackForm = document.getElementById('feedback-form');
    if (feedbackForm) {
        const status = document.getElementById('feedback-status');

        feedbackForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            status.textContent = '';

            const formData = new FormData(feedbackForm);
            const payload = Object.fromEntries(formData.entries());
            const tel = (payload.telephone || '').replace(/\s+/g, '');

            if (!/^(\+7|8)\d{10}$/.test(tel)) {
                status.textContent = 'Неверный телефон. Формат: +7XXXXXXXXXX или 8XXXXXXXXXX';
                status.style.color = '#b91c1c';
                return;
            }

            payload.telephone = tel;

            try {
                const response = await fetch('/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    status.textContent = 'Заявка отправлена. Мы свяжемся с вами.';
                    status.style.color = '#065f46';
                    feedbackForm.reset();
                } else {
                    status.textContent = data.message || 'Ошибка отправки. Попробуйте позже.';
                    status.style.color = '#b91c1c';
                }
            } catch (error) {
                status.textContent = 'Сбой сети. Попробуйте позже.';
                status.style.color = '#b91c1c';
            }
        });
    }

    const placeholderSvg = encodeURIComponent(
        "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>" +
        "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>" +
        "<stop offset='0%' stop-color='#FAF7F2'/><stop offset='100%' stop-color='#E8DCCB'/></linearGradient></defs>" +
        "<rect width='100%' height='100%' fill='url(#g)'/>" +
        "<g fill='#C07A3A' font-family='Arial, sans-serif' text-anchor='middle'>" +
        "<text x='50%' y='50%' font-size='28' font-weight='700'>Фото будет позже</text>" +
        "</g></svg>"
    );

    const placeholderSrc = `data:image/svg+xml;charset=utf-8,${placeholderSvg}`;
    document.querySelectorAll('img').forEach((img) => {
        img.addEventListener('error', () => {
            if (img.dataset.fallbackApplied) {
                return;
            }

            img.dataset.fallbackApplied = '1';
            img.src = placeholderSrc;
        });
    });
});
