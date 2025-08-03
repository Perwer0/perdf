from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import fitz  # PyMuPDF
import os
import io
import uuid
from zipfile import ZipFile
from utils import get_relevant_answer  # Yapay zekâya soru-cevap için

app = Flask(__name__, static_url_path='/static', static_folder='uploads')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# PDF BİRLEŞTİR
@app.route('/merge', methods=['GET', 'POST'])
def merge():
    if request.method == 'POST':
        files = request.files.getlist('pdfs')
        if not files:
            return 'Dosya seçilmedi', 400
        merger = PdfMerger()
        for f in files:
            path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
            f.save(path)
            merger.append(path)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"merged_{uuid.uuid4().hex}.pdf")
        merger.write(output_path)
        merger.close()
        return send_file(output_path, as_attachment=True)
    return render_template('merge.html')

# PDF BÖL
@app.route('/split', methods=['GET', 'POST'])
def split():
    if request.method == 'POST':
        file = request.files.get('pdf')
        start = int(request.form.get('start', 1))
        end = int(request.form.get('end', 1))
        if not file:
            return 'Dosya seçilmedi', 400
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(input_path)
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"split_{uuid.uuid4().hex}.pdf")
        with open(output_path, 'wb') as f:
            writer.write(f)
        return send_file(output_path, as_attachment=True)
    return render_template('split.html')

# PDF TO IMAGE
@app.route('/pdf_to_image', methods=['GET', 'POST'])
def pdf_to_image():
    if request.method == 'POST':
        file = request.files.get('pdf')
        if not file:
            return 'PDF seçilmedi', 400
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(input_path)
        doc = fitz.open(input_path)
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, 'w') as zipf:
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                zipf.writestr(f'page_{i+1}.png', img_bytes)
        zip_buffer.seek(0)
        return send_file(zip_buffer, download_name='images.zip', as_attachment=True)
    return render_template('pdf_to_image.html')

# IMAGE TO PDF
@app.route('/image_to_pdf', methods=['GET', 'POST'])
def image_to_pdf():
    if request.method == 'POST':
        images = request.files.getlist('images')
        if not images:
            return 'Görsel dosya yüklenmedi.', 400
        pdf = Image.open(images[0].stream).convert("RGB")
        image_list = [Image.open(img.stream).convert("RGB") for img in images[1:]]
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"converted_{uuid.uuid4().hex}.pdf")
        pdf.save(output_path, save_all=True, append_images=image_list)
        return send_file(output_path, as_attachment=True)
    return render_template('image_to_pdf.html')

# ✅ PDF SORU-CEVAP (AI)
@app.route('/pdf_chat', methods=['GET'])
def pdf_chat():
    return render_template('pdf_chat.html', pdf_uploaded=False)

@app.route('/upload_pdf_chat', methods=['POST'])
def upload_pdf_chat():
    file = request.files['pdf_file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return render_template('pdf_chat.html', pdf_uploaded=True, filename=filename)
    return redirect(url_for('pdf_chat'))

@app.route('/ask_pdf_question', methods=['POST'])
def ask_pdf_question():
    filename = request.form['filename']
    question = request.form['question']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    answer = get_relevant_answer(filepath, question)
    return render_template('pdf_chat.html', pdf_uploaded=True, filename=filename, answer=answer)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
