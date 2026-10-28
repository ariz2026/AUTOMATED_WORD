PDF KEYWORD SEARCH (BM25) - VS CODE CMD SETUP

1. Extract this ZIP file.
2. Open the extracted bm25_pdf_search folder in VS Code.
3. Open Terminal > New Terminal and choose Command Prompt (CMD).
4. Run these commands one at a time:

   python -m venv .venv
   .venv\Scripts\activate.bat
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python app.py

5. Open http://127.0.0.1:5000 in your browser if it does not open automatically.
6. Use "Choose a PDF document" > "Upload and Index PDF".
7. After the upload succeeds, enter a keyword or phrase and click Search.

NOTES
- sample.pdf is loaded automatically on startup if it exists. You can upload a different PDF from the webpage at any time.
- Upload limit: 25 MB. Only PDF files are accepted.
- The app searches extractable text. Scanned/image-only PDFs need OCR before they can be searched.
- The selected PDF and BM25 index are held in memory. Upload again after restarting the app.
- Search results show the PDF page number and BM25 relevance score.
