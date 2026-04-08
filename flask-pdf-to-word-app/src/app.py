from flask import Flask, request, send_file, render_template, jsonify
import os
from pdf_to_word_converter import pdf_to_word
import pytesseract
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', 'outputs')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_MB', 50)) * 1024 * 1024  # default 50 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

PDF_MAGIC = b'%PDF'

def is_valid_pdf(file_storage):
    """Check the first 4 bytes for the PDF magic number."""
    header = file_storage.read(4)
    file_storage.seek(0)
    return header == PDF_MAGIC

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
    file = request.files.get('pdfFile')
    file_id = request.form.get('fileId')

    if not file or file.filename == '':
        return jsonify(error='No file provided.'), 400

    if not file.filename.lower().endswith('.pdf') or not is_valid_pdf(file):
        return jsonify(error='Invalid file. Only PDF files are accepted.'), 400

    safe_name = secure_filename(file.filename)
    unique_prefix = uuid.uuid4().hex
    pdf_filename = f'{unique_prefix}_{safe_name}'
    docx_filename = pdf_filename.replace('.pdf', '.docx')

    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    word_path = os.path.join(app.config['OUTPUT_FOLDER'], docx_filename)

    file.save(pdf_path)
    progress[file_id] = 'Starting...'
    try:
        pdf_to_word(pdf_path, word_path, lang, file_id, progress)
        progress[file_id] = 'Done!'
        response = send_file(word_path, as_attachment=True, download_name=safe_name.replace('.pdf', '.docx'))
        return response
    except Exception as e:
        progress[file_id] = f'Error: {e}'
        return jsonify(error='Conversion failed. Please try again with a different file.'), 500
    finally:
        progress.pop(file_id, None)

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', 5123))
    app.run(host='0.0.0.0', port=port, debug=debug)