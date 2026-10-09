---
name: ocr-and-documents
description: "Extract text from PDFs, scans, and standalone images (photos/receipts/screenshots) — pymupdf, marker-pdf, tesseract."
version: 2.3.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

## Scanned PDF Pipeline (pymupdf + tesseract)

When marker-pdf is too heavy (~3-5GB) or unavailable, use **pymupdf to render pages → tesseract to OCR**. This works for any scanned/image-based PDF.

### Step 1: Install deps

```bash
pip install pymupdf
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```

### Step 2: Render pages to images

```bash
python3 -c "
import fitz, os
doc = fitz.open('document.pdf')
os.makedirs('/tmp/ocr_pages', exist_ok=True)
for i in range(len(doc)):
    page = doc[i]
    pix = page.get_pixmap(dpi=300)
    pix.save(f'/tmp/ocr_pages/page_{i+1:03d}.png')
    print(f'Rendered page {i+1}/{len(doc)}')
"
```

### Step 3: Batch OCR with tesseract

```bash
cd /tmp/ocr_pages && for f in page_*.png; do
  base="${f%.png}"
  tesseract "$f" "${base}_ocr" -l eng --psm 6 2>/dev/null
done
```

**⚠️ Pitfall:** Do NOT use `execute_code` for batch tesseract — it blocks subprocess calls. Use a single `terminal()` call with a shell loop instead. For 55+ pages, set timeout=600.

### Step 4: Combine output

```bash
cat /tmp/ocr_pages/page_*_ocr.txt > /tmp/full_ocr.txt
```

### Step 6: Parse structured tables from noisy OCR

When OCR garbles product names but preserves numbers (prices, stock quantities), use a **price-based matching strategy** rather than name matching:

1. **Parse the OCR output** — each product row starts with a line number followed by a product code. The name may span multiple lines. Stock/price/total numbers appear as the last 3 comma-formatted numbers on the first line of the row.

2. **Extract (price, category) pairs** from the OCR — these are more reliable than garbled names. Build a lookup dict: `{(price, category): stock}`.

3. **Match against clean data** — if you have a clean product list from another source (e.g. a markdown table extracted in a previous pass), match by `(price, category)` instead of by name. This handles OCR noise where "BEEF LOAP" should be "BEEF LOAF" and "1 11,000 1" gets interleaved into the name.

4. **Handle multi-line names** — when a product row's first line has the numbers but the name continues on subsequent lines, collect all continuation lines until the next row number. Strip trailing numbers from the assembled name.

5. **Fallback for unmatched products** — products whose (price, category) pair doesn't appear in the OCR get stock=0. This is expected for items that were out of stock at report time.

See `references/inventory-pdf-parsing.md` for a complete working parser example.

### Pitfall: Large SQL seed files get silently truncated by write_file

When generating a SQL seed file with 1000+ product rows (~80KB), `write_file` silently truncates at ~50KB. The file appears valid but cuts off mid-row, causing MySQL syntax errors at import time.

**Fix**: Use `terminal` with a heredoc instead:

```python
from hermes_tools import terminal

# Build the SQL string in Python, then write via heredoc
sql = "\n".join(sql_parts)
terminal(f"cat > /path/to/seed.sql << 'SQLEOF'\n{sql}\nSQLEOF")
```

**Detection**: After writing a large seed file, always verify with `wc -c` and compare to the expected size. If truncated, re-write via heredoc.

### Step 6: Parse structured tables from noisy OCR

When OCR garbles product names but preserves numbers (prices, stock quantities), use a **price-based matching strategy** rather than name matching:

1. **Parse the OCR output** — each product row starts with a line number followed by a product code. The name may span multiple lines. Stock/price/total numbers appear as the last 3 comma-formatted numbers on the first line of the row.

2. **Extract (price, category) pairs** from the OCR — these are more reliable than garbled names. Build a lookup dict: `{(price, category): stock}`.

3. **Match against clean data** — if you have a clean product list from another source (e.g. a markdown table extracted in a previous pass), match by `(price, category)` instead of by name. This handles OCR noise where "BEEF LOAP" should be "BEEF LOAF" and "1 11,000 1" gets interleaved into the name.

4. **Handle multi-line names** — when a product row's first line has the numbers but the name continues on subsequent lines, collect all continuation lines until the next row number. Strip trailing numbers from the assembled name.

5. **Fallback for unmatched products** — products whose (price, category) pair doesn't appear in the OCR get stock=0. This is expected for items that were out of stock at report time.

See `references/inventory-pdf-parsing.md` for a complete working parser example.

### When to use this pipeline vs marker-pdf

| Factor | pymupdf + tesseract | marker-pdf |
|--------|---------------------|------------|
| Install size | ~200MB | ~3-5GB |
| Speed (55 pages) | ~5 min | ~1-2 min |
| Table accuracy | Fair (needs manual cleanup) | Good |
| Disk space needed | Low | High (PyTorch) |
| Best for | Quick OCR of structured tables | Complex layouts, equations |

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

---

## Image OCR (photos, receipts, screenshots)

When the user sends a standalone image file (JPEG, PNG, WebP) — not a PDF — that contains text:

### Step 1: Try `vision_analyze` first

```
vision_analyze(image_url="/path/to/image.jpg", question="Read all text visible in this image.")
```

This is normally the best path, but some model providers (e.g. DeepSeek) don't support `image_url` content blocks. If it fails with a schema error (`unknown variant image_url`), fall through to tesseract.

**⚠️ Critical pitfall — do NOT retry vision_analyze on schema errors.** If the error is `unknown variant 'image_url'`, `expected 'text'` (or similar JSON schema rejection about image content blocks), it means the current model simply does not support vision/multimodal input. Retrying with different prompts, resized images, or alternative URLs will produce the same error. Fall through to tesseract immediately or tell the user their model doesn't support vision — don't burn rounds trying.

### Step 2: Check/install tesseract

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
# For multi-language: add tesseract-ocr-chi-sim, tesseract-ocr-tha, etc.
```

### Step 3: Run tesseract with progressive PSM fallback

Receipts, screenshots, and photos each need different layout modes. PSM=6 (uniform block) is the best starting point for receipts. Sampled in order of usefulness:

| PSM | Use case |
|-----|----------|
| **6** | Receipts, uniform text blocks — **best first try for photos** |
| **4** | Single column of variable-sized text |
| **3** | Fully automatic (default) — conservative, may miss detail |
| **1** | Auto + orientation detection |
| **11** | Sparse text — last resort |

```bash
# Primary: PSM 6, English-only often beats mixed-language for garbled receipts
tesseract image.jpg stdout -l eng --psm 6

# Try with target language if known (e.g. Thai receipt)
tesseract image.jpg stdout -l tha+eng --psm 6

# For confidence metadata (bbox + word confidences):
tesseract image.jpg stdout -l eng --psm 6 -c tessedit_create_hocr=1
```

### Step 4: If OCR is noisy, try preprocessing

```bash
# ImageMagick preprocessing (if available)
convert image.jpg -resize 200% -sharpen 0x3 -contrast-stretch 5% enhanced.jpg
tesseract enhanced.jpg stdout -l eng --psm 6
```

### Calibration & transparency (CRITICAL)

Receipt photos, angled shots, and low-contrast images produce garbled OCR. **Never present noisy OCR as a confident reading.** Always tier your output:

- **Confident** — text that repeated across multiple PSM runs or has high hOCR confidence (x_wconf ≥ 80)
- **Fuzzy/uncertain** — text that appeared once, or has garbled neighbors, or low confidence
- **Acknowledge what you can't read** — explicitly say which parts are unclear

Presenting partial OCR as a clean read is worse than saying "the quality is too poor — here's my best guess with uncertainty marked." Users will correct you when you're wrong, and overconfidence erodes trust faster than acknowledged gaps.

When the user identifies errors in your reading, ask what specifically was wrong so you can calibrate and encode the correction. Don't just apologize — extract the lesson.

### Stop signal: when to accept the limitation

If the user says **"stop"**, **"stop that"**, **"it's still wrong"**, or otherwise signals frustration after you've presented garbled OCR, do NOT iterate on more PSM modes, preprocessing tricks, or alternative tools. The window for iterative improvement has closed. Instead:

1. **Acknowledge the limitation explicitly** — "This model doesn't support vision, and tesseract can't handle this image quality."
2. **Offer the high-value pivot** — "Want me to switch to a vision-capable model?" or "Is there another approach you'd prefer?"
3. **Move on** — don't re-read, re-analyze, or try again unless the user asks.

The stop signal means the user has already concluded the tool isn't up to the task. Continuing to try different angles of the same approach erodes trust faster than accepting the limitation and offering a real solution (model switch, different tool, or a different task entirely).

---

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
- **Image OCR**: tesseract PSM=6 first, English-only often beats mixed-language for receipts, always tier confidence, never over-present garbled output
