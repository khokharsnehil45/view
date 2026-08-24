# VIEW ⚡ — Detailed Technical Architecture & Feature Guide

> **The All-in-One Extensible CLI OCR & Local AI Document Suite**  
> *Repository: [https://github.com/khokharsnehil45/view](https://github.com/khokharsnehil45/view)*

---

## 🌟 Overview

**VIEW** is a modular terminal CLI and interactive TUI (Terminal User Interface) crafted with high-contrast cyber/neon themes inspired by developer power tools. It provides an end-to-end pipeline to **visually navigate**, **batch extract OCR text**, **compile structured PDFs/TXT**, and **analyze document content with local LLMs (Ollama)** without ever leaving the terminal.

---

## 🚀 Complete Feature Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   VIEW CLI                                  │
├─────────────────┬────────────────────┬────────────────────┬─────────────────┤
│  📂 NAVIGATOR   │   🔍 OCR ENGINE    │   📄 PDF BUILDER   │  🧠 AI ANALYST  │
│  - Visual Tree  │  - EasyOCR (NN)    │  - ReportLab Flow  │  - Ollama Auto  │
│  - Multi-Select │  - PyTesseract     │  - Numbered Canvas │  - Auto Puller  │
│  - Size Badges  │  - Spatial Sort    │  - Thumbnails      │  - Clean/Q&A    │
└─────────────────┴────────────────────┴────────────────────┴─────────────────┘
```

### 1. 📂 Interactive Visual File Navigator (`navigator.py`)
- **Arrow-Key Navigation**: Seamless filesystem traversal. Enter subdirectories with `Enter` and return to the parent directory with `..`.
- **Zero Manual Path Typing**: Avoid typos or path copying.
- **Smart Directory Previews**: Displays image file counts `(X imgs)` and file sizes next to directory items.
- **Batch Selection Modes**:
  - `⚡ [SELECT ALL X IMAGES IN THIS FOLDER]`: Instantly queue every image in the directory.
  - `☑️ [CHOOSE MULTIPLE IMAGES WITH CHECKBOXES]`: Multi-select specific images using `Space` to toggle and `Enter` to confirm.
- **Robust Path Resolution**: Employs direct object value binding (`questionary.Choice`) with fallback checks (`os.path.isfile`) to handle whitespace and special filenames safely.

---

### 2. 🔍 Multi-Engine Offline OCR (`ocr_engine.py`)
- **Dual Engine Architecture**:
  - **EasyOCR (Default)**: Deep-learning PyTorch neural network model capable of detecting curved, rotated, low-contrast, or stylized text.
  - **PyTesseract (Fallback/Fast)**: Classical Tesseract engine for rapid text scans.
- **Spatial Geometry Sorting**: Sorts detected bounding boxes vertically (top-to-bottom) and horizontally (left-to-right) to reconstruct multi-column layouts into coherent reading order.
- **Line & Block Grouping**: Merges detected character segments into full paragraphs and headings.

---

### 3. 📄 Structured PDF Document Builder (`pdf_builder.py`)
- **Professional Typography**: Formats raw text into headers, subheadings, paragraphs, and formatted bullet points using ReportLab flowables.
- **Dynamic Two-Pass Numbered Canvas**: Renders accurate running headers and footers with `Page X of Y` and source metadata tags.
- **Source Image Thumbnails**: Dynamically resizes and embeds preview snapshots of the source images alongside the extracted text.
- **Multi-Page Batch Support**: Handles multi-image queues cleanly with visual dividers and page breaks.

---

### 4. 🧠 Local AI Document Analyst via Ollama (`ai_analyst.py`)
- **Local Model Auto-Discovery**: Queries local Ollama daemon (`http://127.0.0.1:11434`) via HTTP API to detect downloaded models (e.g., `llama3.2:3b`).
- **Interactive Model Downloader**:
  - Download popular models directly in the app (`llama3.2`, `mistral`, `deepseek-r1`, `qwen2.5`, `phi3`).
  - Enter custom model tags to pull with live progress streaming.
- **Analysis Capabilities**:
  - 📋 **Comprehensive Document Summary**: Executive overview with section breakdowns.
  - 🔑 **Key Takeaways & Action Items**: Extracts action points, insights, and bulleted summaries.
  - 📊 **Structured Data & Markdown Tables**: Converts unstructured receipt/invoice/list data into Markdown tables.
  - 🧹 **Clean Up OCR Typos**: AI-powered proofreading to fix OCR spelling glitches and formatting while preserving original meaning.
  - ❓ **Interactive Document Q&A**: Chat and query specific information from the document.
  - 💾 **Export Analysis**: Save AI generated insights directly to Markdown (`.md`) or text files.

---

### 5. 🎨 Aesthetic & User Experience (`view.py`)
- **HANDY Cyber Theme**:
  - Left-aligned ASCII banner enclosed in a bright cyan rectangular panel.
  - Subtitle badge: `v1.2.0 • All-in-One CLI Suite`.
  - Neon magenta and cyan progress bars.
- **Continuous Loop Lifecycle**: The interactive mode runs in a loop, returning to the main menu after each task with a screen clear (`os.system('clear')`).
- **CLI & TUI Dual Modes**: Run as an interactive menu or via headless terminal flags in scripts and automation pipelines.

---

## 💻 CLI Command Reference

### Interactive Mode
```bash
view
# or
./view.py
```

### Direct CLI Flags
| Flag | Description | Example |
|---|---|---|
| `-i, --input` | Input image file, wildcard, or directory | `view -i "./scans/*.png"` |
| `-o, --output` | Output PDF filename | `view -i receipt.png -o receipt.pdf` |
| `--txt` | Output text / markdown filename | `view -i screenshot.png --txt notes.txt` |
| `-t, --title` | Custom document title header | `view -i scan.png -t "Annual Report"` |
| `--no-thumbnails` | Exclude source image thumbnails in PDF | `view -i scan.png --no-thumbnails` |
| `--engine` | Preferred OCR engine (`easyocr` or `tesseract`) | `view -i scan.png --engine tesseract` |
| `--analyze` | Immediately open local AI Analyst on extracted text | `view -i contract.png --analyze` |
| `-m, --interactive` | Launch interactive TUI menu | `view -m` |

---

## 🏗️ Codebase Structure

```
/home/kevin/view/
├── view.py                 # Core CLI entry point, menu loop & argument parser
├── navigator.py            # Terminal visual directory browser & multi-select
├── ocr_engine.py           # Multi-engine OCR pipeline (EasyOCR / PyTesseract)
├── pdf_builder.py          # ReportLab PDF compilation engine
├── ai_analyst.py           # Ollama Local LLM interface & prompt templates
├── detailed_info_view.md   # Comprehensive technical documentation
├── README.md               # Quickstart guide
├── requirements.txt        # Python library dependencies
├── setup.sh                # Symlink setup wrapper for ~/.local/bin/view
└── .gitignore              # Git ignore rules
```

### 6. 🔄 Auto-Updater (`updater.py`)
- Direct command: `view update`
- Interactively checks GitHub remote for incoming commits (`git fetch` & `git rev-list`).
- Automatically pulls latest updates (`git pull origin main`).
- Upgrades python dependencies if `requirements.txt` was modified.

### 7. 💬 Continuous Multi-Turn AI Document Chat (`ai_analyst.py`)
- Direct command: `view chat <image>` or `view -i <image> --chat`
- Multi-turn conversation engine leveraging Ollama's `/api/chat` endpoint.
- Full context retention: Preserves conversation history between turns.
- In-Chat Commands:
  - `/save`: Export complete conversation to formatted Markdown with model tags.
  - `/clear`: Flush conversation memory and keep document context clean.
  - `/exit`: Clean termination back to the terminal.
