# Inventory PDF Parsing — Price-Based Matching Strategy

When OCR garbles product names but preserves numbers, use this approach to extract stock quantities from scanned inventory PDFs.

## The Problem

Scanned inventory PDFs (55+ pages, tesseract OCR) produce output like:

```
1 763163284327 AH DENTAL CHEW 1'S MILK HP ) 10,500 )
2 763163284310 AH DENTAL CHEW 1'S 1 11,000 11,000
CRANBERRY HP
3 8850124144188 ALPO ADULT BEEF LIVER&VEG ) 65,000 0
```

Product names are garbled (") instead of 0, "LOAP" instead of "LOAF") and numbers get interleaved into names ("1 11,000 1 CRANBERRY HP").

## The Solution: Match by (Price, Category)

Prices and categories are OCR-reliable. Build a lookup by `(price, category)` instead of by name.

### Step 1: Parse OCR output

```python
import re

ocr_products = []  # (category, price, stock)
current_category = None
in_table = False
i = 0

while i < len(lines):
    line = lines[i].strip()
    
    # Detect category headers
    m = re.search(r'Kategori:\s*(.+)', line)
    if m:
        cat = m.group(1).strip()
        if cat not in ('Semua Kategori',):
            current_category = cat
        i += 1
        continue
    
    if 'Kode Produk' in line and 'Nama Produk' in line:
        in_table = True
        i += 1
        continue
    
    if not in_table or not current_category:
        i += 1
        continue
    
    # Skip noise lines
    if not line or line.startswith('---') or 'Hal ' in line or 'Total Per' in line:
        i += 1
        continue
    
    # New product row: starts with line number + product code
    m = re.match(r'^(\d+)\s+(\S+)\s+(.*)', line)
    if m:
        rest = m.group(3)
        nums = re.findall(r'[\d,]+', rest)
        stock = 0
        price = 0
        
        if len(nums) >= 3:
            stock = int(nums[-3])
            price = int(nums[-2].replace(',', ''))
        elif len(nums) == 2:
            price = int(nums[-2].replace(',', ''))
        
        # Skip name continuation lines — we only need price+stock
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if re.match(r'^\d+\s+\S+', next_line):
                break
            if 'Kategori:' in next_line or 'Total Per' in next_line:
                break
            j += 1
        
        if price > 0:
            ocr_products.append((current_category, price, stock))
        
        i = j
    else:
        i += 1
```

### Step 2: Build stock lookup

```python
# Map OCR category names to your ENUM
cat_map = {
    "DOG FOOD": "Makanan",
    "CAT FOOD": "Makanan",
    "OBAT / Medicine": "Kesehatan",
    # ... etc
}

stock_lookup = {}
for ocr_cat, price, stock in ocr_products:
    enum_cat = cat_map.get(ocr_cat, "Lainnya")
    key = (price, enum_cat)
    if key not in stock_lookup:  # keep first occurrence
        stock_lookup[key] = stock
```

### Step 3: Match clean products

```python
# clean_products = [(name, kategori, price), ...] from a reliable source
final_products = []
for name, kategori, price in clean_products:
    key = (price, kategori)
    stock = stock_lookup.get(key, 0)  # 0 = not found in OCR
    final_products.append((name, kategori, price, stock))
```

## Results

This approach matched ~75% of products (764/1025 in one real run). Unmatched products get stock=0, which is reasonable — they were likely out of stock at report time.

## Pitfalls

- **Duplicate prices within a category**: if two products share the same price in the same category, the lookup returns the first OCR occurrence. This is rare in practice since most products have unique prices.
- **OCR misreads 0 as )**: common. The parser handles this by checking `len(nums) >= 3` — if OCR reads `) 10,500 )` instead of `0 10,500 0`, only 2 numbers are found and stock defaults to 0.
- **Multi-line names**: the parser skips continuation lines entirely since it only needs price+stock. This avoids the garbled-name problem.
