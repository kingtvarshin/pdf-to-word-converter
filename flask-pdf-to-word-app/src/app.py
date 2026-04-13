import io
import os
import threading
import time
import uuid
import zipfile

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pytesseract
from flask import Flask, jsonify, render_template, request, send_file, session
from werkzeug.utils import secure_filename

from pdf_to_word_converter import pdf_to_word

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', 'outputs')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_MB', '50')) * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

PDF_MAGIC = b'%PDF'

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
}

# Job registry: file_id → {status, output_path, download_name, created_at, completed_at}
jobs: dict = {}
jobs_lock = threading.Lock()


class _JobStatusProxy:
    """Lets pdf_to_word write `progress[file_id] = msg` directly into the jobs dict."""

    def __setitem__(self, file_id: str, status: str) -> None:
        with jobs_lock:
            if file_id in jobs:
                jobs[file_id]['status'] = status

    def __getitem__(self, file_id: str) -> str:
        with jobs_lock:
            return jobs[file_id]['status']

    def get(self, file_id: str, default=None):
        with jobs_lock:
            job = jobs.get(file_id)
            return job['status'] if job else default

    def pop(self, file_id, *args):
        pass  # job lifecycle is managed separately


_progress_proxy = _JobStatusProxy()


def _cleanup_loop() -> None:
    """Background thread: purge completed jobs and output files older than 1 hour."""
    while True:
        time.sleep(300)
        cutoff = time.time() - 3600
        with jobs_lock:
            expired = [
                fid for fid, job in jobs.items()
                if job['completed_at'] and job['completed_at'] < cutoff
            ]
        for fid in expired:
            with jobs_lock:
                job = jobs.pop(fid, None)
            if job:
                try:
                    os.remove(job['output_path'])
                except OSError:
                    pass


threading.Thread(target=_cleanup_loop, daemon=True).start()


def is_valid_pdf(file_storage) -> bool:
    header = file_storage.read(4)
    file_storage.seek(0)
    return header == PDF_MAGIC


def _do_conversion(file_id: str, pdf_path: str, word_path: str,
                   lang: str, page_from, page_to) -> None:
    try:
        pdf_to_word(pdf_path, word_path, lang, file_id, _progress_proxy,
                    page_from=page_from, page_to=page_to)
        with jobs_lock:
            jobs[file_id]['status'] = 'Done!'
            jobs[file_id]['completed_at'] = time.time()
    except Exception as exc:
        with jobs_lock:
            jobs[file_id]['status'] = f'Error: {exc}'
            jobs[file_id]['completed_at'] = time.time()
    finally:
        try:
            os.remove(pdf_path)
        except OSError:
            pass


@app.route('/health')
def health():
    return jsonify(status='ok'), 200


@app.route('/')
def index():
    langs = pytesseract.get_languages(config='')
    lang_display = [(LANG_MAP.get(code, code), code) for code in langs]
    history = []
    for jid in session.get('job_ids', []):
        with jobs_lock:
            job = jobs.get(jid)
        if job:
            history.append({
                'id': jid,
                'download_name': job['download_name'],
                'status': job['status'],
            })
    return render_template('index.html', langs=lang_display, history=history)


@app.route('/upload', methods=['POST'])
def upload_file():
    lang = request.form.get('lang', 'eng')
    page_from_raw = request.form.get('page_from', '').strip()
    page_to_raw = request.form.get('page_to', '').strip()
    page_from = int(page_from_raw) if page_from_raw.isdigit() else None
    page_to = int(page_to_raw) if page_to_raw.isdigit() else None

    files = request.files.getlist('pdfFile')
    if not files or all(f.filename == '' for f in files):
        return jsonify(error='No file provided.'), 400

    job_ids = []
    for file in files:
        if not file or file.filename == '':
            continue
        if not file.filename.lower().endswith('.pdf') or not is_valid_pdf(file):
            return jsonify(error=f'"{file.filename}" is not a valid PDF.'), 400

        safe_name = secure_filename(file.filename)
        prefix = uuid.uuid4().hex
        pdf_filename = f'{prefix}_{safe_name}'
        docx_filename = pdf_filename[:-4] + '.docx'

        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        word_path = os.path.join(app.config['OUTPUT_FOLDER'], docx_filename)
        file.save(pdf_path)

        file_id = uuid.uuid4().hex
        with jobs_lock:
            jobs[file_id] = {
                'status': 'Queued',
                'output_path': word_path,
                'download_name': safe_name[:-4] + '.docx',
                'created_at': time.time(),
                'completed_at': None,
            }

        threading.Thread(
            target=_do_conversion,
            args=(file_id, pdf_path, word_path, lang, page_from, page_to),
            daemon=True,
        ).start()

        job_ids.append(file_id)

    session['job_ids'] = (session.get('job_ids', []) + job_ids)[-20:]
    session.modified = True

    return jsonify(job_ids=job_ids), 202


@app.route('/progress/<file_id>')
def get_progress(file_id):
    with jobs_lock:
        job = jobs.get(file_id)
    if not job:
        return jsonify(status='Not found'), 404
    return jsonify(status=job['status'])


@app.route('/download/<file_id>')
def download_file(file_id):
    with jobs_lock:
        job = jobs.get(file_id)
    if not job:
        return jsonify(error='Job not found.'), 404
    status = job['status']
    if status.startswith('Error:'):
        return jsonify(error=status), 400
    if status != 'Done!':
        return jsonify(error='Conversion not complete yet.'), 202
    output_path = job['output_path']
    if not os.path.exists(output_path):
        return jsonify(error='Output file has been cleaned up. Please re-upload.'), 404
    return send_file(output_path, as_attachment=True, download_name=job['download_name'])


@app.route('/batch-download', methods=['POST'])
def batch_download():
    data = request.get_json(silent=True) or {}
    file_ids = data.get('file_ids', [])
    if not file_ids:
        return jsonify(error='No file IDs provided.'), 400
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fid in file_ids:
            with jobs_lock:
                job = jobs.get(fid)
            if job and os.path.exists(job['output_path']):
                zf.write(job['output_path'], job['download_name'])
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name='converted_documents.zip',
                     mimetype='application/zip')


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', '5123'))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)