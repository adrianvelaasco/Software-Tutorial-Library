"""
fetch_duration_all.py — v2
Fetches video duration for ALL datasets. Uses fewer threads and
retries to avoid YouTube rate-limiting.
"""

import json
import re
import urllib.request
import urllib.error
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(BASE_DIR, 'datasets', 'js')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def fetch_duration(vid, retries=2):
    if not vid:
        return vid, None
    for attempt in range(retries + 1):
        try:
            url = f"https://www.youtube.com/watch?v={vid}"
            req = urllib.request.Request(url, headers=HEADERS)
            html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
            m = re.search(r'"lengthSeconds":"(\d+)"', html)
            if m:
                return vid, int(m.group(1))
            m2 = re.search(r'"duration":"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"', html)
            if m2:
                h = int(m2.group(1) or 0)
                mn = int(m2.group(2) or 0)
                s = int(m2.group(3) or 0)
                return vid, h * 3600 + mn * 60 + s
            return vid, None
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(2 + random.uniform(0, 2))
                continue
            return vid, None
        except Exception:
            if attempt < retries:
                time.sleep(1)
                continue
            return vid, None
    return vid, None


def load_records(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    start = content.index('[')
    end = content.rindex('];') + 1
    return json.loads(content[start:end])


def save_records(path, records):
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    const_match = re.match(r'(const \w+ = )', original)
    const_prefix = const_match.group(1) if const_match else 'const DATA = '
    after_match = re.search(r'\];\s*\n(.*)', original, re.DOTALL)
    trailing = after_match.group(1) if after_match else ''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(const_prefix + json.dumps(records, ensure_ascii=False, indent=2) + ';\n')
        if trailing.strip():
            f.write(trailing)


def process_file(js_file):
    path = os.path.join(JS_DIR, js_file)
    records = load_records(path)

    missing = [r for r in records if r.get('duration_seconds') is None]
    if not missing:
        print(f"  [{js_file}] All {len(records)} records already have duration. Skipping.")
        return 0, 0

    vids = [r['vid'] for r in missing if r.get('vid')]
    results = {}
    done = 0
    total_vids = len(vids)

    # Use 8 threads — safe rate for YouTube scraping
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_duration, vid): vid for vid in vids}
        for future in as_completed(futures):
            vid, duration = future.result()
            results[vid] = duration
            done += 1
            if done % 100 == 0 or done == total_vids:
                pct = round(done / total_vids * 100)
                print(f"    -> {done}/{total_vids} ({pct}%)")

    patched = 0
    for record in records:
        vid = record.get('vid')
        if vid in results and results[vid] is not None:
            record['duration_seconds'] = results[vid]
            patched += 1
        elif record.get('duration_seconds') is None:
            record['duration_seconds'] = None

    save_records(path, records)
    failed = len(missing) - patched
    return patched, failed


def main():
    js_files = sorted([f for f in os.listdir(JS_DIR) if f.endswith('.js')])
    print(f"Found {len(js_files)} dataset files.\n")

    total_patched = 0
    total_failed = 0

    for i, js_file in enumerate(js_files, 1):
        print(f"[{i}/{len(js_files)}] {js_file}")
        patched, failed = process_file(js_file)
        total_patched += patched
        total_failed += failed
        print(f"  Done: {patched} patched, {failed} failed\n")
        # Small pause between datasets to be kind to YouTube
        if i < len(js_files):
            time.sleep(1)

    print(f"ALL DONE — Total patched: {total_patched} | Failed: {total_failed}")


if __name__ == '__main__':
    main()
