from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from rank_bm25 import BM25Okapi
from werkzeug.utils import secure_filename
from io import BytesIO
from pathlib import Path
import re
import webbrowser

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB upload limit

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PDF = BASE_DIR / "sample.pdf"
ALLOWED_EXTENSIONS = {"pdf"}

# The current document and BM25 index are kept in memory.
documents = []
bm25 = None
current_pdf_name = None
current_page_count = 0


def tokenize(text):
    """Simple tokenizer that does not require downloading NLTK data."""
    return re.findall(r"\b[\w]+\b", text.lower(), flags=re.UNICODE)


def split_into_sentences(text):
    """Split extracted PDF text into searchable sentence-like passages."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    # Keep useful non-empty passages, including text without punctuation.
    return [part.strip() for part in parts if part.strip()]


def build_index(pdf_stream, filename):
    """Extract text page by page and build a new BM25 index."""
    global documents, bm25, current_pdf_name, current_page_count

    reader = PdfReader(pdf_stream)
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("This PDF is password-protected and could not be opened.") from exc

    new_documents = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for passage in split_into_sentences(page_text):
            # Avoid indexing tiny fragments such as isolated page numbers.
            if len(passage) >= 3:
                new_documents.append({"text": passage, "page": page_number})

    if not new_documents:
        raise ValueError(
            "No readable text was found in this PDF. If it is a scanned document, OCR is needed first."
        )

    tokenized_docs = [tokenize(item["text"]) for item in new_documents]
    tokenized_docs = [tokens if tokens else ["_empty_"] for tokens in tokenized_docs]
    new_bm25 = BM25Okapi(tokenized_docs)

    documents = new_documents
    bm25 = new_bm25
    current_pdf_name = filename
    current_page_count = len(reader.pages)


# Load sample.pdf automatically when it exists, so the app works on first launch.
if DEFAULT_PDF.exists():
    try:
        with DEFAULT_PDF.open("rb") as pdf_file:
            build_index(BytesIO(pdf_file.read()), DEFAULT_PDF.name)
    except Exception as error:
        print(f"Could not load sample.pdf: {error}")


@app.route("/")
def home():
    return render_template(
        "index.html",
        current_pdf_name=current_pdf_name,
        current_page_count=current_page_count,
    )


@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "Please choose a PDF file first."}), 400

    file = request.files["pdf"]
    if not file or not file.filename:
        return jsonify({"error": "Please choose a PDF file first."}), 400

    safe_name = secure_filename(file.filename)
    if not safe_name or "." not in safe_name or safe_name.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Only PDF files are allowed."}), 400

    try:
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({"error": "The selected file is empty."}), 400
        build_index(BytesIO(file_bytes), safe_name)
        return jsonify({
            "message": "PDF uploaded and indexed successfully.",
            "filename": current_pdf_name,
            "pages": current_page_count,
            "passages": len(documents),
        })
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        app.logger.exception("PDF upload failed")
        return jsonify({"error": "Could not read this PDF. Please check that it is a valid, non-corrupted PDF."}), 400


@app.route("/search", methods=["POST"])
def search():
    global documents, bm25
    if bm25 is None or not documents:
        return jsonify({"error": "Upload a text-based PDF before searching."}), 400

    data = request.get_json(silent=True) or {}
    query = str(data.get("query", "")).strip()
    if not query:
        return jsonify({"error": "Please enter a keyword or phrase to search."}), 400

    tokenized_query = tokenize(query)
    if not tokenized_query:
        return jsonify([])

    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:10]
    results = [
        {
            "text": documents[index]["text"],
            "page": documents[index]["page"],
            "score": round(float(scores[index]), 4),
        }
        for index in top_indices
        if scores[index] > 0
    ]
    return jsonify(results)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "The PDF is too large. The maximum upload size is 25 MB."}), 413


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)
