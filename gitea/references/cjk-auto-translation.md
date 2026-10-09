# CJK Auto-Translation for Gitea MIPS Report

## Technique

The script auto-detects CJK characters (Japanese ひらがな/カタカナ/漢字 and Chinese 汉字) and translates them to English using the [MyMemory Translation API](https://mymemory.translated.net/doc/spec.php).

### Detection
- Regex: `[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]`
- Hiragana 3040-309F → langpair `JA|EN`
- Katakana + Kanji 30A0-9FAF → langpair `JA|EN`
- Han characters without Japanese syllabary → langpair `ZH|EN`

### Skipping low-CJK content
- If CJK chars < 10% of total text AND text > 50 chars → skip (avoids translating URLs that coincidentally contain `の`)

### API endpoint
```
GET https://api.mymemory.translated.net/get?q=<url-encoded-text>&langpair=<lang>|EN
```
- Free tier: 50 requests/day, 1000 words/day
- `responseData.translatedText` → the translation

### Implementation in script
```python
CJK_RE = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u4E00-\u9FFF]")

def translate_text(text):
    if not text or not CJK_RE.search(text):
        return text, ""
    cjk_count = len(CJK_RE.findall(text))
    total = len(text.replace(" ", "").replace("\n", ""))
    if cjk_count / max(total, 1) < 0.1 and total > 50:
        return text, ""
    langpair = "JA|EN" if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", text) else "ZH|EN"
    try:
        q = urllib.parse.quote(text[:500])
        url = f"https://api.mymemory.translated.net/get?q={q}&langpair={langpair}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        trans = data.get("responseData", {}).get("translatedText", "")
        if trans and trans != text:
            return trans.strip(), langpair.split("|")[0]
    except Exception:
        pass
    return text, ""
```

### Where translation applies
1. **Task Details** (title): translated after stripping `fix/feat/chore` prefixes
2. **Notes** (body hint): first meaningful sentence from body, then translated
3. Fallback: original text if API fails or returns empty
