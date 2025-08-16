# Flask PDF to Word Converter

This project is a Flask web application that allows users to upload PDF files and convert them into Word documents. The app supports direct conversion for digital PDFs and uses Optical Character Recognition (OCR) for scanned documents in any Tesseract-supported language.

## Features

- Upload PDF files
- Convert PDF files to Word documents (direct or via OCR)
- Select document language for OCR from all Tesseract-supported languages
- Download the converted Word documents
- Dockerized for easy deployment

## Project Structure

```
flask-pdf-to-word-app
├── src
│   ├── app.py                # Entry point of the Flask application
│   ├── pdf_to_word_converter_hindi.py  # Logic for PDF to Word conversion
│   └── templates
│       └── index.html        # HTML template for the main page
├── requirements.txt          # List of dependencies
└── README.md                 # Project documentation
Dockerfile                    # Docker configuration
```

## Requirements

To run this project locally, you need to have the following dependencies installed:

- Flask
- pdf2image
- pytesseract
- python-docx
- Werkzeug
- Pillow
- pdf2docx

You can install the required packages using pip:

```
pip install -r requirements.txt
```

## Setup Instructions (Local)

1. Clone the repository:

   ```
   git clone <repository-url>
   cd flask-pdf-to-word-app
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Ensure that Tesseract OCR and Poppler are installed on your system. All Tesseract language data should be available for best results.

4. Run the Flask application:

   ```
   python src/app.py
   ```

5. Open your web browser and go to `http://127.0.0.1:5000` to access the application.

## Docker Setup

1. Build the Docker image:

   ```
   docker build -t flask-pdf-to-word-app .
   ```

2. Run the Docker container:

   ```
   docker run -p 5000:5000 flask-pdf-to-word-app
   ```

   This will install all Tesseract language packs and Poppler utilities automatically.

3. Access the app at [http://localhost:5000](http://localhost:5000).

## Usage

1. On the main page, upload a PDF file using the provided form.
2. Select the document language for OCR from the dropdown (all available Tesseract languages are shown).
3. Click the "Convert & Download" button to start the conversion process.
4. Once the conversion is complete, a download link for the converted Word document will be provided.

## License

This project is licensed under the MIT License.