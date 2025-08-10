
import os, re, io
import fitz  # PyMuPDF

# --- Optional: load .env if present ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def _try_embed(texts):
    """Optional embeddings via sentence-transformers; safe fallback if unavailable."""
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("PERDF_EMBED_MODEL", "intfloat/multilingual-e5-small")
        model = SentenceTransformer(model_name)
        import numpy as np
        return model.encode(texts, normalize_embeddings=True)
    except Exception:
        return None

def _chunk_text(text: str, size: int = 900, overlap: int = 150):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return chunks

def _load_pdf_chunks(pdf_path: str):
    doc = fitz.open(pdf_path)
    chunks, pages = [], []
    for pnum, page in enumerate(doc, start=1):
        txt = page.get_text("text") or ""
        if not txt.strip():
            continue
        for ch in _chunk_text(txt):
            chunks.append(ch)
            pages.append(pnum)
    return chunks, pages

def _rank_keyword(chunks, query):
    q = query.lower()
    scores = []
    for i, ch in enumerate(chunks):
        t = ch.lower()
        score = t.count(q) * 3
        for tok in q.split():
            score += t.count(tok)
        scores.append((i, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [i for i, s in scores]

def _rank_embedding(chunks, query):
    vecs = _try_embed(["passage: " + c for c in chunks])
    if vecs is None:
        return None, None
    import numpy as np
    qv = _try_embed(["query: " + query])
    if qv is None:
        return None, None
    qv = qv[0]
    sims = vecs @ qv  # cosine if normalized
    order = list(np.argsort(sims)[::-1])
    return order, sims

def _make_preview(pdf_path: str, page_num: int, dpi: int = 140) -> str:
    doc = fitz.open(pdf_path)
    page = doc[page_num-1]
    pix = page.get_pixmap(dpi=dpi)
    base_dir = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_name = f"{base_name}_p{page_num}_preview.png"
    out_path = os.path.join(base_dir, out_name)
    with open(out_path, "wb") as f:
        f.write(pix.tobytes("png"))
    return out_name

def _sentences(text: str):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]

def _extractive_summary(snippets, question="", max_sentences=3):
    sents = []
    for snip in snippets:
        sents.extend(_sentences(snip)[:2])
    seen = set(); clean = []
    for s in sents:
        t = s.strip()
        if t and t.lower() not in seen:
            clean.append(t)
            seen.add(t.lower())
        if len(clean) >= max_sentences:
            break
    return " ".join(clean) if clean else ""

def _llm_summary(snippets, question: str) -> str:
    """Use OpenAI to summarize if key is available; else return empty to fallback."""
    if not OPENAI_API_KEY:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        text = "\n\n".join(snippets)[:8000]
        prompt = (
            "Aşağıdaki PDF pasajlarına dayanarak, kullanıcı sorusuna çok kısa ve net Türkçe bir özet yaz. "
            "Sadece pasajlarda yer alan bilgilere dayan. Gerekirse belirsizliği belirt. 3-4 cümleyi geçme.\n\n"
            f"Soru: {question}\n\n"
            f"Pasajlar:\n{text}"
        )
        resp = client.chat.completions.create(
            model=os.getenv("PERDF_LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role":"user","content":prompt}],
            max_tokens=180,
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # any failure -> fallback
        return ""

def get_relevant_answer_struct(pdf_path: str, question: str, k: int = 3, make_previews: bool = True):
    """
    Returns:
    {
      'mode': 'Embedding' | 'Anahtar kelime',
      'summary': '...',
      'results': [{'page': int, 'snippet': str, 'preview': 'filename.png' | None}]
    }
    """
    chunks, page_of = _load_pdf_chunks(pdf_path)
    if not chunks:
        return {'mode': 'Anahtar kelime', 'summary': 'PDF metin içerik bulunamadı.', 'results': []}

    order, sims = _rank_embedding(chunks, question)
    mode = "Embedding" if order is not None else "Anahtar kelime"
    if order is None:
        order = _rank_keyword(chunks, question)

    idxs = order[:k]
    results = []
    for i in idxs:
        page = page_of[i]
        snip = chunks[i].strip().replace('\\n', ' ')
        snip = snip[:450] + ("…" if len(snip) > 450 else "")
        preview = None
        if make_previews:
            try:
                preview = _make_preview(pdf_path, page)
            except Exception:
                preview = None
        results.append({'page': page, 'snippet': snip, 'preview': preview})

    # Prefer LLM summary if possible, else extractive
    snippets = [r['snippet'] for r in results]
    summary = _llm_summary(snippets, question).strip()
    if not summary:
        summary = _extractive_summary(snippets, question, max_sentences=3)
        if not summary:
            summary = "İlgili kısa bir özet çıkarılamadı; kaynak pasajlar aşağıda."
    return {'mode': mode, 'summary': summary, 'results': results}
