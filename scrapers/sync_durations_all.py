"""
sync_durations_all.py

Fetches video durations from YouTube concurrently for all datasets and syncs the
results to JS, JSON, and CSV files in datasets/.
Adds 'duracion' (e.g. "14:25") and 'duracion_segundos' (e.g. 865) to CSV files.
"""

import json
import csv
import re
import urllib.request
import urllib.error
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(BASE_DIR, 'datasets', 'js')
JSON_DIR = os.path.join(BASE_DIR, 'datasets', 'json')
CSV_DIR = os.path.join(BASE_DIR, 'datasets', 'csv')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def format_duration(seconds):
    if seconds is None or seconds == '':
        return ""
    try:
        sec = int(seconds)
        m_fmt, s_fmt = divmod(sec, 60)
        h_fmt, m_fmt = divmod(m_fmt, 60)
        if h_fmt > 0:
            return f"{h_fmt:02d}:{m_fmt:02d}:{s_fmt:02d}"
        else:
            return f"{m_fmt:02d}:{s_fmt:02d}"
    except Exception:
        return ""

def fetch_duration(vid, retries=2):
    if not vid:
        return vid, None
    for attempt in range(retries + 1):
        try:
            url = f"https://www.youtube.com/watch?v={vid}"
            req = urllib.request.Request(url, headers=HEADERS)
            html = urllib.request.urlopen(req, timeout=6).read().decode('utf-8', errors='ignore')
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
                time.sleep(1 + random.uniform(0, 1))
                continue
            return vid, None
        except Exception:
            if attempt < retries:
                time.sleep(0.5)
                continue
            return vid, None
    return vid, None

def load_js_records(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    start = content.index('[')
    end = content.rindex('];') + 1
    return json.loads(content[start:end])

def save_js_records(path, records):
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

def update_csv_file(csv_path, vid_duration_map):
    if not os.path.exists(csv_path):
        return
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        
        if 'duracion' not in fieldnames:
            idx = fieldnames.index('fecha_publicacion') + 1 if 'fecha_publicacion' in fieldnames else len(fieldnames)
            fieldnames.insert(idx, 'duracion')
            fieldnames.insert(idx + 1, 'duracion_segundos')
        elif 'duracion_segundos' not in fieldnames:
            idx = fieldnames.index('duracion') + 1
            fieldnames.insert(idx, 'duracion_segundos')

        for row in reader:
            enlace = row.get('enlace', '')
            vid_match = re.search(r'v=([a-zA-Z0-9_-]+)', enlace)
            vid = vid_match.group(1) if vid_match else ''
            
            sec = vid_duration_map.get(vid)
            if sec is not None and sec != '':
                row['duracion_segundos'] = str(sec)
                row['duracion'] = format_duration(sec)
            else:
                row['duracion_segundos'] = row.get('duracion_segundos', '')
                row['duracion'] = row.get('duracion', '')
            rows.append(row)

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def update_json_file(json_path, vid_duration_map):
    if not os.path.exists(json_path):
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for r in data:
        vid = r.get('vid')
        if vid in vid_duration_map and vid_duration_map[vid] is not None:
            r['duration_seconds'] = vid_duration_map[vid]
            r['duracion'] = format_duration(vid_duration_map[vid])
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    js_files = sorted([f for f in os.listdir(JS_DIR) if f.endswith('.js')])
    print(f"Found {len(js_files)} dataset JS files.\n")

    for i, js_file in enumerate(js_files, 1):
        path = os.path.join(JS_DIR, js_file)
        try:
            records = load_js_records(path)
            missing = [r for r in records if r.get('duration_seconds') is None and r.get('vid')]
            
            vid_map = {}
            if missing:
                vids = [r['vid'] for r in missing]
                print(f"[{i}/{len(js_files)}] {js_file} — Fetching {len(vids)} durations...")
                with ThreadPoolExecutor(max_workers=32) as executor:
                    futures = {executor.submit(fetch_duration, vid): vid for vid in vids}
                    for future in as_completed(futures):
                        vid, dur = future.result()
                        if dur is not None:
                            vid_map[vid] = dur

            for r in records:
                vid = r.get('vid')
                if vid in vid_map:
                    r['duration_seconds'] = vid_map[vid]
                    r['duracion'] = format_duration(vid_map[vid])
                elif r.get('duration_seconds') is not None:
                    r['duracion'] = format_duration(r['duration_seconds'])

            save_js_records(path, records)

            # Sync JSON
            if js_file == 'tutorials_data.js':
                json_name = 'touchdesigner_tutorials.json'
                csv_name = 'touchdesigner_tutorials.csv'
            else:
                json_name = js_file.replace('_data.js', '.json')
                csv_name = js_file.replace('_data.js', '.csv')

            json_path = os.path.join(JSON_DIR, json_name)
            dataset_dur_map = {r['vid']: r.get('duration_seconds') for r in records if r.get('vid')}
            update_json_file(json_path, dataset_dur_map)

            csv_path = os.path.join(CSV_DIR, csv_name)
            update_csv_file(csv_path, dataset_dur_map)

            cnt = sum(1 for r in records if r.get('duration_seconds') is not None)
            print(f"  ✓ {js_file} -> {csv_name} ({cnt}/{len(records)} updated)\n")

        except Exception as e:
            print(f"Error processing {js_file}: {e}\n")

    print("\n🎉 ALL CSV, JS, AND JSON DATASETS UPDATED WITH VIDEO DURATIONS!")

if __name__ == '__main__':
    main()
