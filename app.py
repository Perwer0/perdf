from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_pdf():
    files = request.files.getlist('pdfs')
    merger = PdfMerger()
    
    for file in files:
        merger.append(file)

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.pdf')
    merger.write(output_path)
    merger.close()

    return send_file(output_path, as_attachment=True)

@app.route('/split', methods=['POST'])
def split_pdf():
    file = request.files['pdf']
    reader = PdfReader(file)
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add
