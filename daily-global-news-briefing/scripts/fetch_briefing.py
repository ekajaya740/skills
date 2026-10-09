#!/usr/bin/env python3
"""
Fetch RSS feeds and emit a draft markdown briefing.
Usage: python fetch_briefing.py [--llm]
Output: draft briefing to stdout; pipe to file or directly return.
"""

import sys
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

FEEDS = {
    "BBC World":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Business":   "https://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "BBC US/Canada":  "https://feeds.bbci.co.uk/news/us_and_canada/rss.xml",
}

def _fetch(name, url, timeout=20):
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return name, r.text
    except Exception as e:
        return name, f"<!-- ERROR: {e} -->"

def parse_feed(xml_text, max_items=5):
    """Parse an RSS XML string and return list of (title, link, desc, pubDate)."""
    items = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            # Try RSS 1.0 / Atom fallback root
            channel = root
        for item in channel.findall("item")[:max_items]:
            def get(tag):
                el = item.find(tag)
                text = el.text if el is not None else ""
                if text and text.startswith("<![CDATA["):
                    text = text[9:-3]
                return text.strip() if text else ""
            title = get("title")
            link = get("link")
            desc = get("description")
            pub = get("pubDate")
            if title:
                items.append((title, link, desc, pub))
    except Exception:
        pass
    return items

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Draft global news briefing from RSS feeds.")
    parser.add_argument("--llm", action="store_true", help="Pipe headlines to LLM for synthesis (not implemented; stub)")
    parser.add_argument("--max-items", type=int, default=5, help="Max stories per feed")
    parser.add_argument("--feeds", nargs="*", default=None, help="Override feed URLs as 'Name=URL'")
    args = parser.parse_args()

    feeds = FEEDS.copy()
    if args.feeds:
        feeds = {}
        for pair in args.feeds:
            name, url = pair.split("=", 1)
            feeds[name.strip()] = url.strip()

    # Fetch in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch, name, url): name for name, url in feeds.items()}
        for future in as_completed(futures):
            name = futures[future]
            _, text = future.result()
            results[name] = text

    # Parse each feed
    all_stories = {}
    for name, xml_text in results.items():
        if xml_text.startswith("<!-- ERROR"):
            all_stories[name] = []
            continue
        stories = parse_feed(xml_text, max_items=args.max_items)
        all_stories[name] = stories

    # Print draft markdown
    now = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"# Daily Global News Briefing — {now}\n")

    cat_map = {
        "BBC World": "Geopolitics",
        "BBC Business": "Business & Economy",
        "BBC Technology": "Tech & Science",
        "BBC US/Canada": "Geopolitics",
    }

    by_category = {}
    refs = []
    ref_counter = [0]

    def make_ref(link, source):
        ref_counter[0] += 1
        n = ref_counter[0]
        refs.append((n, link, source))
        return f"[{n}]"

    for feed_name, stories in all_stories.items():
        cat = cat_map.get(feed_name, "Other")
        by_category.setdefault(cat, []).extend(stories)

    for cat in ["Geopolitics", "Business & Economy", "Tech & Science", "Other"]:
        if cat not in by_category:
            continue
        print(f"## {cat} {'🌍' if cat=='Geopolitics' else '💰' if cat=='Business & Economy' else '🔬' if cat=='Tech & Science' else ''}\n")
        shown = 0
        for title, link, desc, pub in by_category[cat][:3]:
            shown += 1
            ref = make_ref(link, cat)
            print(f"**• {title}** {ref}")
            clean_desc = re.sub(r'<[^>]+>', '', desc)
            if clean_desc:
                print(clean_desc[:200] + ("..." if len(clean_desc) > 200 else ""))
            print()
        if shown == 0:
            print("*(no stories from available sources)*\n")

    print("## Big Picture\n")
    print("*(synthesis placeholder — add 2–3 sentences connecting top stories)*\n")

    print("---\n")
    print("## References\n")
    for n, link, source in refs:
        print(f"[{n}] {link}")
    print(f"\n*Compiled: {now}*")

if __name__ == "__main__":
    main()
