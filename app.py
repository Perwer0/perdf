from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
from PIL import Image
import fitz  # PyMuPDF
import os
import io
import uuid
from zipfile import ZipFile

# Uygulama başlat
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Klasörler yoksa oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/image_to_pdf', methods=['GET', 'POST'])
def image_to_pdf():
    if request.method == 'POST':
        images = request.files.getlist('images')
        if not images or len(images) == 0:
            return 'No images uploaded.', 400

        pdf = FPDF()
        for img in images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(img.filename))
            img.save(img_path)

            image = Image.open(img_path)
            width, height = image.size
            width_mm = width * 0.264583
            height_mm = height * 0.264583

            pdf.add_page()
            pdf.image(img_path, 0, 0, width_mm, height_mm)

        output_filename = f"{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        pdf.output(output_path)
        return send_file(output_path, as_attachment=True)

    return render_template('image_to_pdf.html')

@app.route('/pdf_to_image', methods=['GET', 'POST'])
def pdf_to_image():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf')
        if not pdf_file:
            return 'No PDF uploaded.', 400

        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf_file.filename))
        pdf_file.save(pdf_path)

        doc = fitz.open(pdf_path)
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, 'a') as zipf:
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                zipf.writestr(f'page_{i + 1}.png', img_data)

        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='images.zip')

    return render_template('pdf_to_image.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render için gereklidir
    app.run(host='0.0.0.0', port=port)
