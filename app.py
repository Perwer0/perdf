from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pdf-to-image', methods=['GET', 'POST'])
def pdf_to_image():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file.filename.endswith('.pdf'):
            file_path = os.path.join(UPLOAD_FOLDER, secure_filename(pdf_file.filename))
            pdf_file.save(file_path)

            images = convert_pdf_to_images(file_path)
            image_paths = []

            for i, image in enumerate(images):
                image_path = os.path.join(UPLOAD_FOLDER, f'page_{i+1}.png')
                image.save(image_path, 'PNG')
                image_paths.append(image_path)

            return render_template('pdf_to_image.html', images=image_paths)
    return render_template('pdf_to_image.html')

@app.route('/image-to-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    if request.method == 'POST':
        images = request.files.getlist('image_files')
        image_list = []

        for image in images:
            img = Image.open(image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image_list.append(img)

        output_path = os.path.join(UPLOAD_FOLDER, 'converted.pdf')
        image_list[0].save(output_path, save_all=True, append_images=image_list[1:])

        return send_file(output_path, as_attachment=True)
    return render_template('image_to_pdf.html')

@app.route('/split-pdf', methods=['GET', 'POST'])
def split_pdf():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        start_page = int(request.form['start_page'])
        end_page = int(request.form['end_page'])

        input_pdf = PdfReader(pdf_file)
        output_pdf = PdfWriter()

        for page_num in range(start_page - 1, end_page):
            output_pdf.add_page(input_pdf.pages[page_num])

        output_path = os.path.join(UPLOAD_FOLDER, 'split.pdf')
        with open(output_path, 'wb') as f:
            output_pdf.write(f)

        return send_file(output_path, as_attachment=True)
    return render_template('split.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
