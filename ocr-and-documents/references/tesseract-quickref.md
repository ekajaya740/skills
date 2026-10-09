# Tesseract Quick Reference

## PSM modes (best → worst for photos)

| PSM | Mode | Best for |
|-----|------|----------|
| 6 | Uniform block | **Receipts**, dense text photos |
| 4 | Single column | Screenshots, variable-size text |
| 3 | Fully auto | Conservative, safe fallback |
| 1 | Auto + OSD | When orientation unknown |
| 11 | Sparse text | Last resort, noisy output |

## Language selection

- **English-only (`-l eng`)** often outperforms mixed-language for garbled or low-contrast photos — the Thai/Chinese packs can inject noise into English adjacent text
- Only use `-l tha+eng` when the target language is actually mixed and the image quality is good
- Install packs: `sudo apt-get install -y tesseract-ocr-eng tesseract-ocr-tha tesseract-ocr-chi-sim`

## Confidence via hOCR

```bash
tesseract image.jpg stdout -l eng --psm 6 -c tessedit_create_hocr=1
```
hOCR output includes `x_wconf` (word confidence 0-100). Filter for ≥80 for "confident" tier.

## Preprocessing (when imagemagick available)

```bash
convert image.jpg -resize 200% -sharpen 0x3 -contrast-stretch 5% enhanced.jpg
```

## Known pitfalls

- **Photo receipts are hard**: skew, lighting, thermal-print fading, and mixed fonts defeat tesseract. Mark uncertainty explicitly.
- **Presenting noisy OCR as clean** erodes trust. Always tier: confident / fuzzy / unreadable.
- **Thai + English receipts**: tesseract struggles with mixed-script receipts. Try English-only first, then Thai-only, then combined — compare results.
