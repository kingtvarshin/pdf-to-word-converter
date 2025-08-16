from flask import Flask, request, send_file, render_template
import os
from pdf_to_word_converter import pdf_to_word
import pytesseract
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

progress = {}

LANG_MAP = {
    'afr': 'Afrikaans',
    'amh': 'Amharic',
    'ara': 'Arabic',
    'ben': 'Bengali',
    'bod': 'Tibetan',
    'bos': 'Bosnian',
    'bul': 'Bulgarian',
    'cat': 'Catalan',
    'ces': 'Czech',
    'chi_sim': 'Chinese (Simplified)',
    'chi_tra': 'Chinese (Traditional)',
    'dan': 'Danish',
    'deu': 'German',
    'eng': 'English',
    'fra': 'French',
    'guj': 'Gujarati',
    'hin': 'Hindi',
    'ita': 'Italian',
    'jpn': 'Japanese',
    'kan': 'Kannada',
    'kor': 'Korean',
    'mar': 'Marathi',
    'nld': 'Dutch',
    'pol': 'Polish',
    'por': 'Portuguese',
    'rus': 'Russian',
    'spa': 'Spanish',
    'tam': 'Tamil',
    'tel': 'Telugu',
    'tur': 'Turkish',
    'ukr': 'Ukrainian',
    'urd': 'Urdu',
    'vie': 'Vietnamese',
    # ...add more as needed...
}

@app.route('/progress/<file_id>')
def get_progress(file_id):
    return progress.get(file_id, 'Starting...')

@app.route('/')
def index():
    langs = pytesseract.get_languages(config='')
    lang_display = [(LANG_MAP.get(code, code), code) for code in langs]
    return render_template('index.html', langs=lang_display)

@app.route('/upload', methods=['POST'])
def upload_file():
    lang = request.form.get('lang', 'eng')
    file = request.files['pdfFile']
    file_id = request.form.get('fileId')
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    word_path = os.path.join(app.config['OUTPUT_FOLDER'], file.filename.replace('.pdf', '.docx'))
    file.save(pdf_path)
    progress[file_id] = "Starting..."
    pdf_to_word(pdf_path, word_path, lang, file_id, progress)
    progress[file_id] = "Done!"
    return send_file(word_path, as_attachment=True, download_name=file.filename.replace('.pdf', '.docx'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5123, debug=True)