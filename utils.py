import fitz  # PyMuPDF
from openai import OpenAI
import os

# API anahtarını ortam değişkeninden al (güvenlik için)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY ortam değişkeni tanımlı değil.")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_relevant_answer(pdf_path, question):
    doc = fitz.open(pdf_path)
    page_texts = []

    for page_number, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            page_texts.append((page_number + 1, text))

    candidates = []
    for page_num, content in page_texts:
        prompt = (
            f"PDF belgesinin {page_num}. sayfasındaki içerik:\n\n"
            f"{content}\n\n"
            f"Yukarıdaki bilgiye dayanarak şu soruya cevap ver: {question}\n"
            f"Eğer cevap yoksa sadece 'Yok' yaz."
        )

        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            response = completion.choices[0].message.content.strip()

            if response.lower() != "yok":
                candidates.append((page_num, response))

        except Exception as e:
            print(f"OpenAI API hatası: {e}")
            continue

    if not candidates:
        return "Bu soruya yanıt PDF içinde bulunamadı."

    page_num, answer = candidates[0]
    return f"Sayfa {page_num}:\n{answer}"
