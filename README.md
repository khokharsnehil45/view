# VIEW ⚡

> **The All-in-One Extensible CLI OCR Suite**

**VIEW** is a terminal CLI and interactive TUI suite styled with high-contrast cyber/neon themes, designed to extract text from single or batch images/screenshots and compile them into clean, structured PDF documents or plain text files.

---

## ✨ Features

- 📂 **Visual Terminal File Navigator**: Browse through directories and select images using arrow keys and checkboxes—no manual path typing needed.
- ⚡ **Batch Folder OCR**: Batch scan entire directories or multiple selected images at once.
- 📄 **Structured PDF Engine**: Compiles OCR text into styled documents with running headers, footers, dynamic page numbering (`Page X of Y`), and source previews.
- 📝 **Multi-Format Export**: Export to Structured PDF, Plain Text / Markdown (`.txt`), or live terminal preview.
- 🎨 **HANDY-Style Cyber Terminal Theme**: Beautiful Rich ASCII banners, styled status tables, and live progress bars.

---

## 🚀 Quick Start

### 1. Launch Interactive Navigator & TUI Mode
Simply run without arguments or with `--interactive`:
```bash
./view.py
# or
view
```
This opens the visual navigator where you can:
- Browse folders using arrow keys (`Enter` to enter folders, `..` to go up).
- **Select All Images** in a directory with 1 click.
- **Choose Multiple Images with Checkboxes** (`Space` to toggle, `Enter` to confirm).

### 2. Direct CLI Batch Commands

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
- [`navigator.py`](file:///home/kevin/view/navigator.py): Interactive terminal visual file browser & multi-select checkbox engine.
- [`ocr_engine.py`](file:///home/kevin/view/ocr_engine.py): Multi-engine OCR extraction with spatial sorting and block grouping.
- [`pdf_builder.py`](file:///home/kevin/view/pdf_builder.py): ReportLab PDF document builder with numbered canvas, styles, and headers.
- [`setup.sh`](file:///home/kevin/view/setup.sh): Helper script to symlink/wrap `view` command in `~/.local/bin`.
