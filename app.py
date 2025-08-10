
import os, io, uuid, zipfile
from datetime import datetime
from flask import Flask, render_template, request, send_file, send_from_directory, redirect, url_for, flash
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import fitz  # PyMuPDF
from utils import get_relevant_answer_struct

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = os.getenv("SECRET_KEY", "perdf-dev")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TEMPLATES_AUTO_RELOAD"] = True
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Disable Jinja cache so template changes reflect immediately (useful during dev)
app.jinja_env.cache = {}

# Inject a timestamp for cache-busting static assets
@app.context_processor
def inject_build_ts():
    return {"build_ts": int(datetime.now().timestamp())}

def _unique_name(filename: str) -> str:
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{name}_{uuid.uuid4().hex[:8]}{ext}"

@app.route("/")
def index():
    return render_template("index.html")

# Serve uploaded files (preview)
@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

# ------------- PDF MERGE -------------

@app.route("/merge", methods=["GET", "POST"])
def merge():
    if request.method == "GET":
        return render_template("merge.html")
    files = request.files.getlist("pdfs")
    if not files:
        flash("PDF dosyaları seçilmedi.")
        return redirect(url_for("merge"))

    # Client-side order (indices string like "0,2,1")
    order = (request.form.get("order") or "").strip()
    sort_name = request.form.get("sort_name") == "1"
    if order:
        try:
            idxs = [int(x) for x in order.split(",") if x.strip()!=""]
            files = [files[i] for i in idxs if 0 <= i < len(files)]
            # when manual order present, ignore sort by name
            sort_name = False
        except Exception as e:
            print("merge order parse error:", e)

    if sort_name and files:
        files = sorted(files, key=lambda f: (f.filename or "").lower())

    # Save uploads, compute hash for dedupe
    dedupe = request.form.get("dedupe") == "1"
    seen = set()
    saved_paths = []
    import hashlib
    for f in files:
        if not f or not f.filename.lower().endswith(".pdf"):
            continue
        data = f.read()  # read into memory to hash; typical PDFs are fine for MVP
        f.stream.seek(0)
        if dedupe:
            h = hashlib.sha256(data).hexdigest()
            if h in seen:
                continue
            seen.add(h)
        fname = _unique_name(f.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        f.save(path)
        saved_paths.append(path)

    if not saved_paths:
        flash("Geçerli PDF bulunamadı (kopyalar ayıklandıysa hepsi aynı olabilir).")
        return redirect(url_for("merge"))

    # Merge
    writer = PdfWriter()
    for path in saved_paths:
        try:
            reader = PdfReader(path)
            # Try to keep metadata from the first file
            if len(writer.pages) == 0 and reader.metadata:
                writer.add_metadata(reader.metadata)
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            print("Merge error:", e)

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    return send_file(out_buf, mimetype="application/pdf", as_attachment=True, download_name="perdf_merged.pdf")

# ------------- PDF SPLIT -------------

@app.route("/split", methods=["GET", "POST"])
def split():
    if request.method == "GET":
        return render_template("split.html")

    f = request.files.get("pdf")
    if not f:
        flash("PDF yükleyin.")
        return redirect(url_for("split"))

    # Save upload
    fname = _unique_name(f.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    f.save(path)

    # Options
    ranges_spec = (request.form.get("ranges") or "").strip()
    mode = request.form.get("mode", "zip")
    pattern = (request.form.get("pattern") or "page_{n}.pdf").strip()
    if "{n}" not in pattern:
        pattern = "page_{n}.pdf"

    reader = PdfReader(path)
    total = len(reader.pages)

    # Parse ranges like "1-3,7,10-12"
    def parse_ranges(spec: str, total_pages: int):
        if not spec:
            return list(range(1, total_pages+1))
        nums = set()
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                try:
                    a, b = int(a), int(b)
                except ValueError:
                    continue
                if a > b: a, b = b, a
                for x in range(max(1,a), min(total_pages,b)+1):
                    nums.add(x)
            else:
                try:
                    x = int(part)
                    if 1 <= x <= total_pages:
                        nums.add(x)
                except ValueError:
                    continue
        return sorted(nums)

    pages = parse_ranges(ranges_spec, total)
    if not pages:
        flash("Geçerli sayfa aralığı bulunamadı.")
        return redirect(url_for("split"))

    if mode == "single":
        # one combined PDF
        w = PdfWriter()
        for p in pages:
            w.add_page(reader.pages[p-1])
        out_buf = io.BytesIO()
        w.write(out_buf)
        out_buf.seek(0)
        return send_file(out_buf, mimetype="application/pdf", as_attachment=True, download_name="perdf_selected_pages.pdf")

    # default: separate PDFs zipped
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in pages:
            w = PdfWriter()
            w.add_page(reader.pages[p-1])
            pdf_bytes = io.BytesIO()
            w.write(pdf_bytes)
            out_name = pattern.replace("{n}", str(p))
            if not out_name.lower().endswith(".pdf"):
                out_name += ".pdf"
            zf.writestr(out_name, pdf_bytes.getvalue())
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype="application/zip", as_attachment=True, download_name="perdf_split_pages.zip")

# ------------- PDF -> IMAGE -------------

@app.route("/pdf_to_image", methods=["GET", "POST"])
def pdf_to_image():
    if request.method == "GET":
        return render_template("pdf_to_image.html")
    f = request.files.get("pdf")
    if not f:
        flash("PDF yükleyin.")
        return redirect(url_for("pdf_to_image"))

    fname = _unique_name(f.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    f.save(path)

    ranges_spec = (request.form.get("ranges") or "").strip()
    dpi = int(request.form.get("dpi") or 200)
    fmt = (request.form.get("fmt") or "png").lower()
    if fmt not in ("png","jpg","jpeg"):
        fmt = "png"

    reader = PdfReader(path)
    total = len(reader.pages)

    def parse_ranges(spec: str, total_pages: int):
        if not spec:
            return list(range(1, total_pages+1))
        nums = set()
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                try:
                    a, b = int(a), int(b)
                except ValueError:
                    continue
                if a > b: a, b = b, a
                for x in range(max(1,a), min(total_pages,b)+1):
                    nums.add(x)
            else:
                try:
                    x = int(part)
                    if 1 <= x <= total_pages:
                        nums.add(x)
                except ValueError:
                    continue
        return sorted(nums)

    pages = parse_ranges(ranges_spec, total)
    if not pages:
        flash("Geçerli sayfa aralığı bulunamadı.")
        return redirect(url_for("pdf_to_image"))

    doc = fitz.open(path)
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in pages:
            page = doc[p-1]
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes(fmt)
            zf.writestr(f"page_{p}.{fmt}", img_bytes)
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype="application/zip", as_attachment=True, download_name="perdf_images.zip")

# ------------- IMAGE -> PDF -------------

@app.route("/image_to_pdf", methods=["GET", "POST"])
def image_to_pdf():
    if request.method == "GET":
        return render_template("image_to_pdf.html")
    files = request.files.getlist("images")
    if not files:
        single = request.files.get("image")
        if single: files = [single]
    if not files:
        flash("En az bir görsel yükleyin.")
        return redirect(url_for("image_to_pdf"))

    # Order handling: we get order as "0,1,2"; map to original indices
    order = (request.form.get("order") or "").strip()
    if order:
        try:
            idxs = [int(x) for x in order.split(",") if x.strip()!='']
            files = [files[i] for i in idxs if 0 <= i < len(files)]
        except Exception as e:
            print("Order parse error:", e)

    page_size = (request.form.get("page_size") or "auto")
    orientation = (request.form.get("orientation") or "auto")
    fit_mode = (request.form.get("fit_mode") or "contain")
    try:
        margin_mm = float(request.form.get("margin_mm") or 10.0)
    except Exception:
        margin_mm = 10.0

    # If auto page size and zero margins and fit=contain, we can use PIL simple multi-save
    simple_path = (page_size == "auto" and margin_mm <= 0 and fit_mode == "contain")

    # Load images
    from PIL import Image
    imgs = []
    for f in files:
        try:
            img = Image.open(f.stream).convert("RGB")
            imgs.append(img)
        except Exception as e:
            print("IMG load error:", e)

    if not imgs:
        flash("Görsel okunamadı.")
        return redirect(url_for("image_to_pdf"))

    if simple_path and len(imgs) == 1:
        out_buf = io.BytesIO()
        imgs[0].save(out_buf, format="PDF")
        out_buf.seek(0)
        return send_file(out_buf, mimetype="application/pdf", as_attachment=True, download_name="perdf_from_images.pdf")
    elif simple_path and len(imgs) > 1:
        out_buf = io.BytesIO()
        imgs[0].save(out_buf, format="PDF", save_all=True, append_images=imgs[1:])
        out_buf.seek(0)
        return send_file(out_buf, mimetype="application/pdf", as_attachment=True, download_name="perdf_from_images.pdf")

    # Advanced path with ReportLab for page size/margins/fit modes
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait

    def mm_to_pt(mm): 
        return mm * 72.0 / 25.4

    margin_pt = mm_to_pt(margin_mm)

    def pick_page_size(base, img):
        # auto orientation based on image aspect if requested
        if orientation == "portrait":
            return portrait(base)
        if orientation == "landscape":
            return landscape(base)
        # auto: decide by image aspect ratio (>1: landscape)
        w, h = img.size
        if w >= h:
            return landscape(base)
        return portrait(base)

    def get_base_size():
        if page_size == "A4":
            return A4
        if page_size == "Letter":
            return LETTER
        # auto -> use A4 as base, but will be oriented automatically
        return A4

    base = get_base_size()

    out_buf = io.BytesIO()
    c = canvas.Canvas(out_buf, pagesize=base)  # will be reset per page

    for img in imgs:
        # decide page size for this image
        ps = pick_page_size(base, img)
        c.setPageSize(ps)
        page_w, page_h = ps
        box_w = max(1, page_w - 2*margin_pt)
        box_h = max(1, page_h - 2*margin_pt)

        iw, ih = img.size
        # assume 72 dpi if not provided
        dpi = img.info.get("dpi", (72,72))[0] or 72
        # image size in points at 72dpi scaling
        iw_pt = iw * 72.0 / dpi
        ih_pt = ih * 72.0 / dpi

        if fit_mode == "stretch":
            draw_w, draw_h = box_w, box_h
        else:
            import math
            scale_fit = min(box_w/iw_pt, box_h/ih_pt)
            scale_cover = max(box_w/iw_pt, box_h/ih_pt)
            s = scale_fit if fit_mode == "contain" else scale_cover
            draw_w, draw_h = iw_pt*s, ih_pt*s

        # center in box
        x = (page_w - draw_w) / 2.0
        y = (page_h - draw_h) / 2.0

        # Save PIL image to a temporary in-memory buffer to draw
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        # reportlab needs a filename or a PIL ImageReader
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(buf), x, y, width=draw_w, height=draw_h, preserveAspectRatio=False, mask='auto')
        c.showPage()

    c.save()
    out_buf.seek(0)
    return send_file(out_buf, mimetype="application/pdf", as_attachment=True, download_name="perdf_from_images.pdf")

# ------------- PDF CHAT -------------
@app.route("/pdf_chat", methods=["GET"])
def pdf_chat():
    return render_template("pdf_chat.html", pdf_uploaded=False)

@app.route("/upload_pdf_chat", methods=["POST"])
def upload_pdf_chat():
    f = request.files.get("pdf_file")
    if not f:
        flash("PDF yükleyin.")
        return redirect(url_for("pdf_chat"))
    fname = _unique_name(f.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    f.save(path)
    return render_template("pdf_chat.html", pdf_uploaded=True, filename=fname)


@app.route("/ask_pdf_question", methods=["POST"])
def ask_pdf_question():
    filename = request.form.get("filename")
    q = request.form.get("question", "").strip()
    if not filename or not q:
        flash("Soru veya dosya eksik.")
        return redirect(url_for("pdf_chat"))
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    data = get_relevant_answer_struct(path, q, k=3, make_previews=True)
    return render_template("pdf_chat.html", pdf_uploaded=True, filename=filename, qa=data, query=q)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")), debug=True)
