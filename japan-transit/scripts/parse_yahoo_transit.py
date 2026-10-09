#!/usr/bin/env python3
"""Parse Yahoo Transit search results HTML into route summaries.

Usage: python3 parse_yahoo_transit.py /path/to/yahoo_transit.html

Extracts each route's departure/arrival times, stations, and line names.
Works on the HTML saved by curl from transit.yahoo.co.jp/search/result.
"""
import re
import html
import sys

def parse(path):
    data = open(path, encoding='utf-8', errors='replace').read()
    parts = data.split('<div class="routeDetail">')[1:]
    routes = []
    for i, d in enumerate(parts[:15]):
        # station name + time pairs: <li>HH:MM</li> ... <dt><a>STATION</a></dt>
        st = re.findall(
            r'<li>(\d+:\d+)</li></ul><p class="icon">.*?<dt><a[^>]*>(.*?)</a></dt>',
            d, re.S)
        lines = re.findall(
            r'<p class="line">.*?<span class="[^"]*">(.*?)</span>', d, re.S)
        if not st:
            continue
        dep = st[0][0]
        arr = st[-1][0]
        dep_st = html.unescape(st[0][1]).strip()
        arr_st = html.unescape(st[-1][1]).strip()
        line_names = [html.unescape(l).strip() for l in lines[:4]]
        routes.append((dep, arr, dep_st, arr_st, line_names))
    return routes

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: parse_yahoo_transit.py <html_file>", file=sys.stderr)
        sys.exit(1)
    for i, (dep, arr, dep_st, arr_st, lines) in enumerate(parse(sys.argv[1])):
        print(f"Route {i+1}: {dep} -> {arr} | {dep_st} -> {arr_st}")
        for l in lines:
            print(f"    line: {l}")
