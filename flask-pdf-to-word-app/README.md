# Flask PDF to Word Converter

A Flask web application that converts PDF files into Word documents. It supports direct conversion for digital PDFs and falls back to Optical Character Recognition (OCR) for scanned documents, with support for all Tesseract-supported languages.

## Features

- Upload and convert PDF files to Word (`.docx`) format
- Automatic fallback to OCR for scanned/image-based PDFs
- Language selection for OCR (all Tesseract-supported languages)
- Real-time conversion progress indicator
- Download converted Word documents instantly
- Dockerized for easy deployment

## Planned Improvements

### Security Fixes
- [ ] Sanitize uploaded filenames to prevent path traversal attacks (`secure_filename`)
- [ ] Add server-side MIME type / magic-byte validation (not just HTML `accept=".pdf"`)
- [ ] Enforce a maximum file upload size (`MAX_CONTENT_LENGTH`)
- [ ] Disable `debug=True` in production; use environment-based config

### Bug Fixes
- [ ] Use UUID-based filenames to prevent collisions when multiple users upload files with the same name
- [ ] Clean up `progress` dict entries after download to prevent memory leaks
- [ ] Stop the frontend progress-polling loop when status is `"Done!"` or an error occurs
- [ ] Add route-level error handling to return user-friendly error messages instead of raw 500s
- [ ] Fix stale page title in `index.html` (currently shows "Hindi" leftover)
- [ ] Fix port inconsistency (`app.py` uses `5123`; Docker and README reference `5000`)

### New Features
- [ ] Drag-and-drop upload zone for improved UX
- [ ] Page range selection (convert only selected pages)
- [ ] Improved OCR output formatting using bounding-box data (detect headings, columns, paragraphs)
- [ ] Preserve embedded images in OCR-converted documents
- [ ] Multi-file (batch) upload with zipped output
- [ ] Async conversion using a background thread/task queue to avoid HTTP timeouts on large files
- [ ] Auto-cleanup of temporary upload/output files after download
- [ ] Session-based conversion history (re-download without reconverting)
- [ ] Health-check endpoint (`/health`) for Docker/Kubernetes liveness probes
- [ ] Environment-based configuration via `.env` file

### Documentation
- [x] Update README with full feature list and improvement roadmap

## Project Structure

```
pdf-to-word-converter/
├── flask-pdf-to-word-app/
│   ├── src/
│   │   ├── app.py                  # Flask application entry point
│   │   ├── pdf_to_word_converter.py  # PDF to Word conversion logic
│   │   └── templates/
│   │       └── index.html          # Main page HTML template
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Project documentation
└── Dockerfile                      # Docker configuration
```

## Requirements

- Python 3.8+
- Tesseract OCR
- Poppler (for `pdf2image`)

**Python packages:**

- Flask
- pdf2image
- pytesseract
- python-docx
- Werkzeug
- Pillow
- pdf2docx

Install all Python dependencies:

```bash
pip install -r requirements.txt
```

## Setup Instructions (Local)

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd flask-pdf-to-word-app
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install system dependencies:
   - **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
   - **Poppler**: https://poppler.freedesktop.org/ (Windows users: https://github.com/oschwartz10612/poppler-windows)

4. Run the Flask application:

   ```bash
   python src/app.py
   ```

5. Open your browser at `http://127.0.0.1:5000`.

## Docker Setup

1. Build the Docker image:

   ```bash
   docker build -t flask-pdf-to-word-app .
   ```

2. Run the container:

   ```bash
   docker run -p 5000:5000 flask-pdf-to-word-app
   ```

   Tesseract language packs and Poppler are installed automatically inside the container.

3. Access the app at [http://localhost:5000](http://localhost:5000).

## Usage

1. Open the app in your browser.
2. Upload a PDF file using the file picker (or drag-and-drop, once implemented).
3. Select the document language for OCR from the dropdown.
4. Click **Convert & Download** and wait for the progress indicator to complete.
5. The converted `.docx` file will download automatically.

## License

This project is licensed under the MIT License.