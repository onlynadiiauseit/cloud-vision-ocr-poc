# Cloud OCR · Google Cloud Vision API

**Семінар-презентація. Надія Черниченко, ТТП-42.**

PoC вебзастосунку, який надсилає PNG/JPEG у Google Cloud Vision REST API, показує розпізнаний текст і дозволяє завантажити його у UTF-8 TXT. Модель виконується в Google Cloud, локально працює інтерфейс і Python-сервер.

## Стан роботи

- Реалізовано REST-інтеграцію, два режими OCR, обробку помилок та інтерфейс.
- 18 автоматичних тестів пройдено на Python 3.12.
- Демонстраційна відповідь є синтетичною fixture, не результатом виклику Google.
- **Реальний виклик Google ще потрібно виконати з власним API key.** Тести підміняють зовнішній HTTP-запит і не доводять доступність або точність хмарної моделі.

## Запуск на Windows

Потрібен Python 3.10 або новіший. Додаткові Python-пакети не потрібні. Відкрийте папку проєкту у VS Code, а потім термінал PowerShell:

```powershell
py --version
py app.py
```

Відкрийте <http://127.0.0.1:8000>. Кнопка «Показати демоприклад без API» показує `samples/sample.png` та заздалегідь підготовлену відповідь. Вона **не розпізнає довільний файл**. Зупинка сервера: Ctrl+C.

Linux/macOS: `python3 app.py`. Інший порт: `python3 app.py --port 8001`.

## Підключення Google Cloud

1. Відкрийте <https://console.cloud.google.com/> та оберіть власний Google Cloud project. Project ID у посиланні із завдання не слід вважати вашим.
2. Перевірте, що для проєкту увімкнено billing. Безкоштовний обсяг API не скасовує вимогу налаштувати billing.
3. У **APIs & Services → Library** знайдіть **Cloud Vision API** і натисніть **Enable**.
4. У **APIs & Services → Credentials** створіть API key. Обмежте його використання **Cloud Vision API**. Для сервера зі сталою зовнішньою IP-адресою додайте IP restriction. HTTP referrer restriction для цього Python-клієнта не підходить.
5. Встановіть ключ у змінну середовища та запустіть сервер у тому самому терміналі. Не вставляйте реальний ключ у код, README, GitHub або скриншоти.

PowerShell:

```powershell
$env:GOOGLE_VISION_API_KEY = Read-Host "Google Vision API key" -MaskInput
py app.py
```

`-MaskInput` потребує PowerShell 7.1+. Для Windows PowerShell 5.1 використайте:

```powershell
$secureKey = Read-Host "Google Vision API key" -AsSecureString
$env:GOOGLE_VISION_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
py app.py
```

Linux/macOS (bash):

```bash
read -s -p 'Google Vision API key: ' GOOGLE_VISION_API_KEY
export GOOGLE_VISION_API_KEY
python3 app.py
```

Файл `.env.example` пояснює назву змінної. Застосунок **не завантажує `.env` автоматично**.

6. Завантажте `samples/sample.png`, натисніть «Розпізнати через Google» та перевірте індикатор **«Реальний API»**.
7. Порівняйте результат із `samples/expected.txt`. Перевірте точність `2026` та `125.50 UAH`. Збережіть TXT і скриншот результату без ключа для захисту.

## Протокол API

```http
POST https://vision.googleapis.com/v1/images:annotate?key=API_KEY
Content-Type: application/json
```

```json
{
  "requests": [{
    "image": {"content": "BASE64_IMAGE_BYTES"},
    "features": [{"type": "TEXT_DETECTION"}]
  }]
}
```

Заміна `TEXT_DETECTION` на `DOCUMENT_TEXT_DETECTION` обирає режим для щільного тексту. Base64 є кодуванням двійкових даних, а не шифруванням. Передавання захищає HTTPS.

Клієнт читає `responses[0].fullTextAnnotation.text`, а за його відсутності — `responses[0].textAnnotations[0].description`. Перевіряє також `responses[0].error`, навіть за HTTP 200. Відсутність тексту є коректним результатом.

## Архітектура та файли

| Компонент | Відповідальність |
|---|---|
| `static/index.html`, `style.css`, `app.js` | Завантаження зображення, перегляд, вибір OCR, результат та експорт TXT |
| `app.py` | Локальний HTTP-сервер, маршрути, обмеження розміру, передавання запиту клієнту |
| `vision_client.py` | Перевірка формату, Base64, HTTPS POST, розбір JSON, обробка помилок |
| `tests/` | Контракт API з підміною HTTP та інтеграційні перевірки локального сервера |
| `samples/` | Навчальне зображення, еталонний текст та явно позначена імітація відповіді |
| `docs/DEFENSE.md` | Доповідь за слайдами й відповіді на запитання |
| `docs/API.md` | API, обмеження та джерела |

Браузер надсилає байти на локальний `/api/ocr`. Python перетворює їх у Base64 та викликає Google. Браузер отримує лише текст і час запиту. Ключ залишається в процесі сервера.

## Тести

```powershell
py -m unittest discover -s tests -v
```

Тести не потребують ключа, не звертаються до Google та не створюють витрат. У CI запускається той самий набір. Перевірка сигнатури PNG/JPEG є початковою перевіркою формату, повне декодування виконує Google.

## Межі PoC

Підтримуються PNG/JPEG до **4 MiB** — це власний ліміт програми. Немає PDF, пакетної обробки, БД, авторизації користувачів і автоматичних повторів. Таймаут зовнішнього запиту 30 секунд. Показаний час включає мережу й розбір відповіді, він не є чистим часом роботи моделі. Стандартний `http.server` призначений для локальної демонстрації, не для публічного production-сервера.

Google тарифікує окремі функції обробки зображення. На перевіреній сторінці тарифів перші 1000 одиниць на місяць безкоштовні, далі Text Detection / Document Text Detection коштують $1.50 за 1000 одиниць до 5 млн. Перед використанням перевірте актуальні тарифи та квоти у своєму проєкті. Budget alerts не є жорстким лімітом витрат.

## GitHub

Репозиторій: <https://github.com/onlynadiiauseit/cloud-vision-ocr-poc>

```powershell
git clone https://github.com/onlynadiiauseit/cloud-vision-ocr-poc.git
cd cloud-vision-ocr-poc
py app.py
```

Презентація: <https://chatgpt.com/space/page_f869a08a9e8881918258fe372b58cb81> (доступ залежить від налаштувань власника). Її можна експортувати у PPTX.

## Джерела

- [Опис Vision API](https://docs.cloud.google.com/vision/docs)
- [OCR](https://docs.cloud.google.com/vision/docs/ocr)
- [Формат REST-запиту](https://docs.cloud.google.com/vision/docs/request)
- [Налаштування](https://docs.cloud.google.com/vision/docs/setup)
- [API key](https://docs.cloud.google.com/vision/product-search/docs/auth)
- [Тарифи](https://cloud.google.com/vision/pricing)
- [Квоти](https://docs.cloud.google.com/vision/quotas)

Джерела перевірено 05.11.2026. PARCS не використовується: наведене завдання 2 вимагає інтеграції API, але не зобов’язує застосовувати PARCS.
