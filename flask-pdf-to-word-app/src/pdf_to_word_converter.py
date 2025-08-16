import os
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
from docx import Document

def pdf_to_word(pdf_path, word_path, lang='eng', file_id=None, progress=None):
    if progress is not None and file_id is not None:
        progress[file_id] = "Opening document..."
    try:
        cv = Converter(pdf_path)
        if progress is not None and file_id is not None:
            progress[file_id] = "Analyzing document..."
        cv.convert(word_path)
        cv.close()
        if os.path.getsize(word_path) > 0:
            if progress is not None and file_id is not None:
                progress[file_id] = "Conversion complete!"
            return
    except Exception as e:
        if progress is not None and file_id is not None:
            progress[file_id] = f"Direct conversion failed: {e}"

    if progress is not None and file_id is not None:
        progress[file_id] = "Running OCR..."
    images = convert_from_path(pdf_path)  # No poppler_path needed in Docker
    doc = Document()
    for i, image in enumerate(images):
        if progress is not None and file_id is not None:
            progress[file_id] = f"OCR page {i+1}/{len(images)}"
        text = pytesseract.image_to_string(image, lang=lang)
        doc.add_paragraph(text)
    doc.save(word_path)
    if progress is not None and file_id is not None:
        progress[file_id] = "OCR complete!"