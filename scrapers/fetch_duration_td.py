"""
fetch_duration_td.py
Fetches video duration (in seconds) for all TouchDesigner tutorials
by scraping the YouTube page HTML — no API key required.
Adds a `duration_seconds` field to each record in tutorials_data.js.
"""

import json
import re
import urllib.request
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_PATH = os.path.join(BASE_DIR, 'datasets', 'js', 'tutorials_data.js')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

def fetch_duration(vid):
    if not vid:
        return vid, None
    url = f"https://www.youtube.com/watch?v={vid}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
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
    except Exception as e:
        print(f"  Warning: Error fetching {vid}: {e}")
        return vid, None


def load_records():
    with open(JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find the JSON array between the first [ and the matching ];
    start = content.index('[')
    end = content.rindex('];') + 1  # include the ]
    return json.loads(content[start:end])


def save_records(records):
    with open(JS_PATH, 'w', encoding='utf-8') as f:
        f.write('const TUTORIALS_DATA = ' + json.dumps(records, ensure_ascii=False, indent=2) + ';\n')
        f.write('window.TD_DATA = TUTORIALS_DATA;\n')


def main():
    print("Loading tutorials_data.js ...")
    records = load_records()
    total = len(records)
    print(f"  {total} records found.")

    missing = [r for r in records if r.get('duration_seconds') is None]
    print(f"  {len(missing)} records missing duration — fetching...")

    if not missing:
        print("All records already have duration. Done.")
        return

    vids = [r['vid'] for r in missing if r.get('vid')]
    results = {}
    done = 0

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_duration, vid): vid for vid in vids}
        for future in as_completed(futures):
            vid, duration = future.result()
            results[vid] = duration
            done += 1
            if done % 50 == 0 or done == len(vids):
                pct = round(done / len(vids) * 100)
                print(f"  -> {done}/{len(vids)} ({pct}%)")

    patched = 0
    for record in records:
        vid = record.get('vid')
        if vid in results and results[vid] is not None:
            record['duration_seconds'] = results[vid]
            patched += 1
        elif record.get('duration_seconds') is None:
            record['duration_seconds'] = None

    print(f"\nPatched {patched}/{len(missing)} records with duration.")
    failed = len(missing) - patched
    if failed:
        print(f"  Warning: {failed} records could not be fetched (set to null).")

    save_records(records)
    print(f"Saved -> {JS_PATH}")


if __name__ == '__main__':
    main()
