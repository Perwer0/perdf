from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from fpdf import FPDF
from PIL import Image
import fitz  # PyMuPDF
import os
import io
import uuid

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
        if not images:
            return 'No images uploaded.', 400

        pdf = FPDF()
        for img in images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(img.filename))
            img.save(img_pat_
