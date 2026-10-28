const uploadForm = document.getElementById("upload-form");
const pdfInput = document.getElementById("pdf-file");
const uploadButton = document.getElementById("upload-button");
const uploadStatus = document.getElementById("upload-status");
const currentDocument = document.getElementById("current-document");
const pageCount = document.getElementById("page-count");
const searchForm = document.getElementById("search-form");
const searchButton = document.getElementById("search-button");
const searchStatus = document.getElementById("search-status");
const resultsDiv = document.getElementById("results");

function showStatus(element, message, type = "") {
    element.textContent = message;
    element.className = `status ${type}`;
}

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = pdfInput.files[0];
    if (!file) {
        showStatus(uploadStatus, "Please choose a PDF file first.", "error");
        return;
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        showStatus(uploadStatus, "Only PDF files are allowed.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("pdf", file);
    uploadButton.disabled = true;
    showStatus(uploadStatus, "Uploading PDF and building the BM25 index…");

    try {
        const response = await fetch("/upload", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Upload failed.");

        currentDocument.textContent = data.filename;
        pageCount.textContent = `(${data.pages} pages; ${data.passages} searchable passages)`;
        showStatus(uploadStatus, data.message, "success");
        showStatus(searchStatus, "Your PDF is ready to search.", "success");
        resultsDiv.replaceChildren();
    } catch (error) {
        showStatus(uploadStatus, error.message || "Could not upload the PDF.", "error");
    } finally {
        uploadButton.disabled = false;
    }
});

searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = document.getElementById("query").value.trim();
    if (!query) {
        showStatus(searchStatus, "Please enter a keyword or phrase.", "error");
        return;
    }

    searchButton.disabled = true;
    showStatus(searchStatus, "Searching…");
    resultsDiv.replaceChildren();

    try {
        const response = await fetch("/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Search failed.");

        if (data.length === 0) {
            showStatus(searchStatus, "No matching passages found. Try another keyword.");
            return;
        }

        showStatus(searchStatus, `${data.length} matching passage(s), ranked by BM25 score.`, "success");
        data.forEach((item, index) => {
            const card = document.createElement("article");
            card.className = "result";

            const heading = document.createElement("div");
            heading.className = "result-meta";
            heading.textContent = `Result ${index + 1} · Page ${item.page} · BM25 score: ${item.score}`;

            const passage = document.createElement("p");
            passage.textContent = item.text;

            card.append(heading, passage);
            resultsDiv.appendChild(card);
        });
    } catch (error) {
        showStatus(searchStatus, error.message || "Search failed.", "error");
    } finally {
        searchButton.disabled = false;
    }
});
