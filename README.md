
# PerDF Release (Flask)

## Kurulum
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Tarayıcı: http://localhost:10000

- Şablonlar: `templates/`
- Statikler: `static/` (JS: `static/js/app.js`, yüklenen dosyalar: `static/uploads/`)
- Cache kırma: `?v={{ build_ts }}` parametresi ile otomatik.

## Özellikler
- PDF Birleştir / Böl
- PDF→Görsel (PNG) / Görsel→PDF
- PDF Q&A (sayfa numarası ile basit arama)

## OpenAI Özetleme (Opsiyonel)
- `.env` dosyası oluşturun ve anahtarı ekleyin:
```
OPENAI_API_KEY=sk-...
PERDF_LLM_MODEL=gpt-4o-mini
```
- `pip install -r requirements.txt` ile `openai` ve `python-dotenv` kurulur.
- Anahtar yoksa sistem otomatik **extractive** özete düşer.
