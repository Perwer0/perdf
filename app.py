from flask import Flask, render_template, request, send_file, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Serve uploaded PDFs
@app.route('/static/uploads/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# PDF Soru-Cevap arayüzü
@app.route('/pdf_chat', methods=['GET'])
def pdf_chat():
    return render_template('pdf_chat.html', pdf_uploaded=False)

# PDF yükleme
@app.route('/upload_pdf_chat', methods=['POST'])
def upload_pdf_chat():
    file = request.files['pdf_file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return render_template('pdf_chat.html', pdf_uploaded=True, filename=filename)
    return redirect(url_for('pdf_chat'))

# PDF'ten soru sorma
@app.route('/ask_pdf_question', methods=['POST'])
def ask_pdf_question():
    filename = request.form['filename']
    question = request.form['question']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    answer = get_relevant_answer(filepath, question)
    return render_template('pdf_chat.html', pdf_uploaded=True, filename=filename, answer=answer)

# PDF içerisinden metin arama fonksiyonu

def get_relevant_answer(pdf_path, question):
    reader = PdfReader(pdf_path)
    full_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    if question.lower() in full_text.lower():
        start = full_text.lower().find(question.lower())
        snippet = full_text[start:start+500]
        return snippet.strip()
@app.route('/split')
def split():
    return render_template('split.html')

@app.route('/merge')
def merge():
    return render_template('merge.html')

@app.route('/pdf_to_image')
def pdf_to_image():
    return render_template('pdf_to_image.html')

@app.route('/image_to_pdf')
def image_to_pdf():
    return render_template('image_to_pdf.html')

@app.route('/chat_pdf')
def chat_pdf():
    return render_template('chat_pdf.html')


    return "Bu soruya yanıt PDF içinde bulunamadı."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

