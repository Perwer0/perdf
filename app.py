from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import os
import io
import fitz  # PyMuPDF
import uuid
from zipfile import ZipFile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/merge', methods=['GET', 'POST'])
def merge_pdfs():
    if request.method == 'POST':
        files = request.files.getlist('pdfs')
        merger = PdfMerger()

        for file in files:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(filepath)
            merger.append(filepath)

        output_filename = f"merged_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        merger.write(output_path)
        merger.close()

        return send_file(output_path, as_attachment=True)

    return render_template('merge.html')

@app.route('/split', methods=['GET', 'POST'])
def split_pdf():
    if request.method == 'POST':
        file = request.files['pdf_file']
        start = int(request.form['start_page'])
        end = int(request.form['end_page'])

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        reader = PdfReader(filepath)
        writer = PdfWriter()

        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])

        output_filename = f"split_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        with open(output_path, 'wb') as out:
            writer.write(out)

        return send_file(output_path, as_attachment=True)

    return render_template('split.html')

@app.route('/image-to-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    if request.method == 'POST':
        images = request.files.getlist('images')
        pdf = fitz.open()

        for img in images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(img.filename))
            img.save(img_path)
            img_doc = fitz.open(img_path)
            rect = img_doc[0].rect
            pdfbytes = img_doc.convert_to_pdf()
            img_pdf = fitz.open("pdf", pdfbytes)
            pdf.insert_pdf(img_pdf)

        output_filename = f"image2pdf_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        pdf.save(output_path)
        pdf.close()

        return send_file(output_path, as_attachment=True)

    return render_template('image_to_pdf.html')

@app.route('/pdf-to-image', methods=['GET', 'POST'])
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
