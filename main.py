import os
import json
import asyncio
import re
from typing import Any, Dict
from dotenv import load_dotenv
from json import JSONDecodeError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from bot import start_polling, add_order_from_web
import logging

app = FastAPI()
load_dotenv()

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
static_dir = os.path.join(os.path.dirname(__file__), 'static')

templates = Jinja2Templates(directory=templates_dir)

app.mount('/assets', StaticFiles(directory=static_dir), name='assets')

@app.get('/static/{filename:path}', name='static')
async def static_compat(filename: str):
    return RedirectResponse(url=f"/assets/{filename}")

# keys.json ранее использовался для CHAT_ID, сейчас не требуется здесь

# Каталог услуг для детальных страниц
SERVICES_CATALOG: Dict[str, Dict[str, Any]] = {
    "water": {
        "slug": "water",
        "title": "Водоснабжение, Отопление, Водоотведение",
        "lead": "Проектирование и монтаж систем водоснабжения и канализации",
        "description": "Мы разрабатываем и устанавливаем надёжные системы водоснабжения для частных домов и промышленности: от подбора насосного оборудования до разводки и автоматики.",
        "features": [
            "Проект и сметы под ваш объект",
            "Монтаж с соблюдением СНиП и ГОСТ",
            "Материалы с сертификатами качества",
            "Пусконаладка и гарантия",
        ],
        "albums": [
            {
                "title": "тема",
                "items": [
                    {"src": "/assets/img/water/1.jpg", "caption": "текст"},
                    {"src": "/assets/img/water/2.jpg", "caption": "текст"},
                    {"src": "/assets/img/water/3.jpg", "caption": "текст"},
                ],
            }
        ],
    },
    "electric": {
        "slug": "electric",
        "title": "Электрика",
        "lead": "Щиты, разводка, освещение и автоматика",
        "description": "Комплексные решения по электрике: силовые и слаботочные сети, освещение, сборка и настройка щитов, автоматизация и безопасность.",
        "features": [
            "Проектирование по ПУЭ",
            "Сборка щитов и прокладка кабеля",
            "Освещение и управление",
            "Актирование и документация",
        ],
        "albums": [
            {
                "title": "тема",
                "items": [
                    {"src": "/assets/img/electric/1.jpg", "caption": "текст"},
                    {"src": "/assets/img/electric/2.jpg", "caption": "текст"},
                    {"src": "/assets/img/electric/3.jpg", "caption": "текст"},
                ],
            },
            {
                "title": "тема",
                "items": [
                    {"src": "/assets/img/electric/4.jpg", "caption": "текст"},
                    {"src": "/assets/img/electric/5.jpg", "caption": "текст"},
                ],
            }
        ],
    },
    "vent": {
        "slug": "vent",
        "title": "Вентиляция",
        "lead": "Приточно-вытяжные системы и фильтрация",
        "description": "Проектируем и монтируем эффективные вентиляционные системы: комфортный микроклимат, фильтрация и экономичность.",
        "features": [
            "Расчёт производительности",
            "Подбор и монтаж оборудования",
            "Балансировка и шумопонижение",
            "Паспортизация и сервис",
        ],
        "albums": [
            {
                "title": "тема",
                "items": [
                    {"src": "/assets/img/vent/1.jpg", "caption": "текст"},
                    {"src": "/assets/img/vent/2.jpg", "caption": "текст"},
                    {"src": "/assets/img/vent/3.jpg", "caption": "текст"},
                ],
            }
        ],
    },
}

@app.get('/', response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse('main.html', {'request': request})

@app.get('/Price', response_class=HTMLResponse)
async def price(request: Request):
    return templates.TemplateResponse('Price.html', {'request': request})

@app.get('/price', response_class=HTMLResponse)
async def price(request: Request):
    return templates.TemplateResponse('Price.html', {'request': request})

@app.get('/price1', response_class=HTMLResponse)
async def price1(request: Request):
    return templates.TemplateResponse('price1.html', {'request': request})

@app.get('/price2', response_class=HTMLResponse)
async def price2(request: Request):
    return templates.TemplateResponse('price2.html', {'request': request})

@app.get('/price3', response_class=HTMLResponse)
async def price3(request: Request):
    return templates.TemplateResponse('price3.html', {'request': request})

@app.get('/obrsvaz', response_class=HTMLResponse)
async def obrsvaz(request: Request):
    return templates.TemplateResponse('obrsvaz.html', {'request': request})

@app.get('/services/{slug}', response_class=HTMLResponse, name='service_detail')
async def service_detail(request: Request, slug: str):
    service = SERVICES_CATALOG.get(slug)
    if not service:
        return templates.TemplateResponse('service_detail.html', {'request': request, 'service': None}, status_code=404)
    return templates.TemplateResponse('service_detail.html', {'request': request, 'service': service})

@app.post('/feedback')
async def handle_feedback(request: Request):
    try:
        data: Dict[str, Any] = await request.json()
    except JSONDecodeError:
        return JSONResponse({'status': 'error', 'message': 'Некорректный JSON в запросе'}, status_code=400)
    except Exception as e:
        print(f"Ошибка чтения JSON: {e}")
        return JSONResponse({'status': 'error', 'message': 'Не удалось прочитать данные формы'}, status_code=400)

    try:
        phone = data.get('telephone', '') or ''
        phone = re.sub(r'[^\d+]', '', phone)
        if not re.match(r'^(\+7|8)\d{10}$', phone):
            return JSONResponse({'status': 'error', 'message': 'Неверный формат телефона. Используйте +7 или 8 и 10 цифр'}, status_code=400)
        data['telephone'] = phone

        order_id = await add_order_from_web(data)
        print(f"Заказ сохранён (ID: {order_id}) и уведомление отправлено")
        return JSONResponse({'status': 'success'})
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)



@app.on_event('startup')
async def on_startup():
    asyncio.create_task(start_polling())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    uvicorn.run('main:app', host='0.0.0.0', port=5000, reload=False)
