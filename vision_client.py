"""Small, dependency-free Google Cloud Vision REST client."""
import base64
import json
import os
import socket
import time
from urllib import request, error, parse

ENDPOINT = 'https://vision.googleapis.com/v1/images:annotate'
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # Application limit, not Google's API limit.
FEATURES = {'TEXT_DETECTION', 'DOCUMENT_TEXT_DETECTION'}

class VisionError(Exception):
    pass

def build_payload(image, feature='TEXT_DETECTION'):
    if not image or len(image) > MAX_IMAGE_BYTES:
        raise ValueError('Зображення має бути від 1 байта до 4 MiB.')
    if not (image.startswith(b'\x89PNG\r\n\x1a\n') or image.startswith(b'\xff\xd8\xff')):
        raise ValueError('Підтримуються PNG та JPEG. Перевірте формат файлу.')
    if feature not in FEATURES:
        raise ValueError('Невідомий режим OCR.')
    return {'requests': [{'image': {'content': base64.b64encode(image).decode('ascii')},
                          'features': [{'type': feature}]}]}

def extract_text(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('responses'), list) or not payload['responses']:
        raise VisionError('API повернув некоректну структуру відповіді.')
    item = payload['responses'][0]
    if not isinstance(item, dict):
        raise VisionError('API повернув некоректний результат.')
    if item.get('error'):
        raise VisionError('Google не зміг обробити зображення. Перевірте файл і доступ до API.')
    full = item.get('fullTextAnnotation') or {}
    annotations = item.get('textAnnotations') or []
    text = full.get('text', '') if isinstance(full, dict) else ''
    if not text and annotations and isinstance(annotations[0], dict):
        text = annotations[0].get('description', '')
    if not isinstance(text, str):
        raise VisionError('API повернув некоректний текст.')
    return text

def recognize(image, feature='TEXT_DETECTION', *, api_key=None, opener=None):
    payload = build_payload(image, feature)
    key = api_key if api_key is not None else os.environ.get('GOOGLE_VISION_API_KEY', '')
    if not key.strip():
        raise VisionError('Не задано GOOGLE_VISION_API_KEY. Перезапустіть сервер після налаштування ключа.')
    # Never log this URL or raw upstream exception: it contains the API key.
    req = request.Request(ENDPOINT + '?' + parse.urlencode({'key': key}),
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    start = time.perf_counter()
    try:
        with (opener or request.urlopen)(req, timeout=30) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise VisionError('Відповідь API перевищує ліміт застосунку.')
        result = json.loads(raw)
    except error.HTTPError as exc:
        messages = {400: 'Некоректний запит або ключ API.', 401: 'Помилка автентифікації.',
                    403: 'Доступ заборонено. Перевірте API, ключ, обмеження та billing.',
                    429: 'Перевищено квоту. Спробуйте пізніше.'}
        raise VisionError(messages.get(exc.code, f'Помилка сервісу Google (HTTP {exc.code}).')) from None
    except (error.URLError, TimeoutError, socket.timeout):
        raise VisionError('Не вдалося з’єднатися з Google за 30 секунд або виникла мережева помилка.') from None
    except (ValueError, UnicodeDecodeError):
        raise VisionError('API повернув некоректний JSON.') from None
    return {'text': extract_text(result), 'elapsed_ms': round((time.perf_counter()-start)*1000),
            'mode': 'live', 'feature': feature}
