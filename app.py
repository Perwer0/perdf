from flask import Flask, render_template, request, send_file
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
from pdf2image import convert_from_path
import os
import uuid
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('pdfs')
    merger = PdfMerger()
    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        merger.append(path)

    output_path = os.path.join(OUTPUT_FOLDER, 'merged.pdf')
    merger.write(output_path)
    merger.close()

    for f in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, f))

    return send_file(output_path, as_attachment=True)


@app.route('/split', methods=['GET', 'POST'])
def split():
    if request.method == 'POST':
        file = request.files['pdf']
        start = int(request.form['start'])
        end = int(request.form['end'])

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for i in range(start - 1, end):
            if i < len(reader.pages):
                writer.add_page(reader.pages[i])

        output_path = os.path.join(OUTPUT_FOLDER, 'split.pdf')
        with open(output_path, 'wb') as f:
            writer.write(f)

        os.remove(input_path)
        return send_file(output_path, as_attachment=True)

    return render_template('split.html')


@app.route('/image-to-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    if request.method == 'POST':
        files = request.files.getlist('images')
        image_list = []

        for file in files:
            image = Image.open(file.stream).convert('RGB')
            image_list.append(image)

        if image_list:
            output_path = os.path.join(OUTPUT_FOLDER, 'converted.pdf')
            image_list[0].save(output_path, save_all=True, append_images=image_list[1:])
            return send_file(output_path, as_attachment=True)

    return render_template('image_to_pdf.html')


@app.route('/pdf-to-image', methods=['GET', 'POST'])
def pdf_to_image():
    if request.method == 'POST':
        file = request.files['pdf']
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        output_images = convert_from_path(input_path)
        zip_filename = f"pdf_images_{uuid.uuid4().hex[:8]}.zip"
        zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for idx, img in enumerate(output_images):
                img_filename = f"page_{idx + 1}.jpg"
                img_path = os.path.join(OUTPUT_FOLDER, img_filename)
                img.save(img_path, 'JPEG')
                zipf.write(img_path, img_filename)
                os.remove(img_path)

        os.remove(input_path)
        return send_file(zip_path, as_attachment=True)

    return render_template('pdf_to_image.html')


if __name__ == '__main__':
    app.run(debug=True)
