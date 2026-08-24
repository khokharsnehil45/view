# VIEW ⚡

> **The All-in-One Extensible CLI OCR Suite**

**VIEW** is a terminal CLI and interactive TUI suite styled with high-contrast cyber/neon themes, designed to extract text from single or batch images/screenshots, analyze content with local Ollama LLMs, and compile results into clean, structured PDF documents or plain text files.

---

## ✨ Features

- 📂 **Visual Terminal File Navigator**: Browse through directories and select images using arrow keys and checkboxes—no manual path typing needed.
- ⚡ **Batch Folder OCR**: Batch scan entire directories or multiple selected images at once.
- 🧠 **Local AI Document Analyst (Ollama)**:
  - Detects installed local models (e.g. `llama3.2:3b`) or downloads new models automatically (`ollama pull`).
  - Summarize documents, extract key takeaways & action items, reconstruct tables into Markdown, fix raw OCR typos, or run freeform Q&A on extracted text.
- 📄 **Structured PDF Engine**: Compiles OCR text into styled documents with running headers, footers, dynamic page numbering (`Page X of Y`), and source previews.
- 📝 **Multi-Format Export**: Export to Structured PDF, Plain Text / Markdown (`.txt`), or live terminal preview.
- 🎨 **HANDY-Style Cyber Terminal Theme**: Beautiful Rich ASCII banners, rectangular cyber panels, and live progress bars.

---

## 🚀 Quick Start

### 1. Launch Interactive Navigator & TUI Mode
Simply run without arguments or with `--interactive`:
```bash
./view.py
# or
view
```

### 2. Local AI Document Analysis (Ollama)
Select **`🧠 Local AI Document Analyst`** from the interactive menu, or run with `--analyze`:
```bash
# OCR an image and immediately open the AI analyst session:
view -i "./invoice.png" --analyze
```

### 3. Direct CLI Batch Commands

**Batch process an entire folder into a structured PDF:**
```bash
view -i "./scans/*.png" -o summary.pdf -t "Scanned Notes"
```

**Batch process multiple directories/files into TXT:**
```bash
view -i "~/Pictures/Screenshots/" --txt extracted_notes.txt
```

---

## 🛠️ Project Structure

- [`view.py`](file:///home/kevin/view/view.py): Main CLI entry point and Interactive TUI launcher.
- [`ai_analyst.py`](file:///home/kevin/view/ai_analyst.py): Local AI Document Analyst engine interfacing with Ollama.
- [`navigator.py`](file:///home/kevin/view/navigator.py): Interactive terminal visual file browser & multi-select checkbox engine.
- [`ocr_engine.py`](file:///home/kevin/view/ocr_engine.py): Multi-engine OCR extraction with spatial sorting and block grouping.
- [`pdf_builder.py`](file:///home/kevin/view/pdf_builder.py): ReportLab PDF document builder with numbered canvas, styles, and headers.
- [`setup.sh`](file:///home/kevin/view/setup.sh): Helper script to symlink/wrap `view` command in `~/.local/bin`.

### 4. Self-Updating
Keep VIEW updated to the latest GitHub release:
```bash
view update
```
Or select **`🔄 Check for Updates (Auto-Updater)`** from the interactive menu.

### 5. Continuous Multi-Turn AI Document Chat
Start an interactive conversation with any document using local Ollama models:
```bash
view chat "/path/to/invoice.png"
# or
view -i "./notes.png" --chat
```
In-chat commands:
- `/save`: Export the entire chat transcript to Markdown (`.md`).
- `/clear`: Reset conversation context.
- `/exit`: End the chat session.

### 6. Interactive Table & Receipt Parser (Export to CSV / JSON)
Automatically extract financial data, invoices, matrices, and tables from images and export to `.csv` or `.json`:
```bash
# Launch table/receipt parser on an image:
view parse "/path/to/receipt.png"
# or
view -i "./invoice.png" --parse-table
```
