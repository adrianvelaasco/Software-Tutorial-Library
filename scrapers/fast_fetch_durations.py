"""
fast_fetch_durations.py

High-speed parallel batch duration fetcher using yt-dlp.
Updates JS, JSON, and CSV datasets progressively after each batch!
"""

import json
import csv
import re
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(BASE_DIR, 'datasets', 'js')
JSON_DIR = os.path.join(BASE_DIR, 'datasets', 'json')
CSV_DIR = os.path.join(BASE_DIR, 'datasets', 'csv')

def format_duration(seconds):
    if seconds is None or seconds == '':
        return ""
    try:
        sec = int(float(seconds))
        m_fmt, s_fmt = divmod(sec, 60)
        h_fmt, m_fmt = divmod(m_fmt, 60)
        if h_fmt > 0:
            return f"{h_fmt:02d}:{m_fmt:02d}:{s_fmt:02d}"
        else:
            return f"{m_fmt:02d}:{s_fmt:02d}"
    except Exception:
        return ""

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
            rows.append(row)

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def fetch_chunk(chunk):
    results = {}
    urls = [f"https://www.youtube.com/watch?v={vid}" for vid in chunk]
    cmd = ['yt-dlp', '--skip-download', '--no-warnings', '--ignore-errors', '--print', '%(id)s|%(duration)s'] + urls
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stdout = res.stdout or ''
        for line in stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                vid = parts[0].strip()
                try:
                    dur = int(float(parts[1].strip()))
                    results[vid] = dur
                except Exception:
                    pass
    except Exception:
        pass
    return results

def main():
    js_files = sorted([f for f in os.listdir(JS_DIR) if f.endswith('.js')])
    print(f"Found {len(js_files)} dataset files.\n")

    for i, js_file in enumerate(js_files, 1):
        path = os.path.join(JS_DIR, js_file)
        if js_file == 'tutorials_data.js':
            csv_name = 'touchdesigner_tutorials.csv'
        else:
            csv_name = js_file.replace('_data.js', '.csv')

        csv_path = os.path.join(CSV_DIR, csv_name)

        try:
            records = load_js_records(path)
            missing = [r['vid'] for r in records if r.get('duration_seconds') is None and r.get('vid')]
            
            if missing:
                print(f"[{i}/{len(js_files)}] {js_file} — Fetching {len(missing)} durations...")
                batch_size = 15
                chunks = [missing[j:j + batch_size] for j in range(0, len(missing), batch_size)]
                
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {executor.submit(fetch_chunk, chunk): chunk for chunk in chunks}
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            for r in records:
                                vid = r.get('vid')
                                if vid in res:
                                    r['duration_seconds'] = res[vid]
                                    r['duracion'] = format_duration(res[vid])
                            
                            save_js_records(path, records)
                            dataset_dur_map = {r['vid']: r.get('duration_seconds') for r in records if r.get('vid')}
                            update_csv_file(csv_path, dataset_dur_map)
                            print(f"  -> Progressive update {csv_name}: {sum(1 for r in records if r.get('duration_seconds') is not None)}/{len(records)} done")

            cnt = sum(1 for r in records if r.get('duration_seconds') is not None)
            print(f"  ✓ Finished {csv_name} ({cnt}/{len(records)} rows)\n")

        except Exception as e:
            print(f"Error processing {js_file}: {e}\n")

    print("\n🎉 ALL CSV DATASETS FULLY UPDATED WITH VIDEO DURATIONS!")

if __name__ == '__main__':
    main()
