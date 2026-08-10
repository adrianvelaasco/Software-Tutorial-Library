"""
sync_durations_fast.py

Ultra-fast YouTube duration synchronizer using 25 parallel yt-dlp single-video workers.
Updates JS, JSON, and CSV datasets in real time as durations are fetched!
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

def fetch_single_vid(vid):
    cmd = ['yt-dlp', '--skip-download', '--no-warnings', '--ignore-errors', '--print', '%(id)s|%(duration)s', f'https://www.youtube.com/watch?v={vid}']
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = (res.stdout or '').strip()
        if '|' in out:
            parts = out.split('|')
            v = parts[0].strip()
            dur = int(float(parts[1].strip()))
            return v, dur
    except Exception:
        pass
    return vid, None

def main():
    js_files = sorted([f for f in os.listdir(JS_DIR) if f.endswith('.js')])
    print(f"Found {len(js_files)} dataset files.\n")

    for i, js_file in enumerate(js_files, 1):
        path = os.path.join(JS_DIR, js_file)
        if js_file == 'tutorials_data.js':
            csv_name = 'touchdesigner_tutorials.csv'
            json_name = 'touchdesigner_tutorials.json'
        else:
            csv_name = js_file.replace('_data.js', '.csv')
            json_name = js_file.replace('_data.js', '.json')

        csv_path = os.path.join(CSV_DIR, csv_name)
        json_path = os.path.join(JSON_DIR, json_name)

        try:
            records = load_js_records(path)
            missing = [r['vid'] for r in records if r.get('duration_seconds') is None and r.get('vid')]
            
            if missing:
                print(f"[{i}/{len(js_files)}] {js_file} — Fetching {len(missing)} missing durations (25 threads)...")
                
                vid_dur_map = {}
                done = 0
                total = len(missing)
                start_time = time.time()

                with ThreadPoolExecutor(max_workers=25) as executor:
                    futures = {executor.submit(fetch_single_vid, vid): vid for vid in missing}
                    for future in as_completed(futures):
                        vid, dur = future.result()
                        done += 1
                        if dur is not None:
                            vid_dur_map[vid] = dur

                        if done % 25 == 0 or done == total:
                            # Progressive save to JS and CSV every 25 videos
                            for r in records:
                                v = r.get('vid')
                                if v in vid_dur_map:
                                    r['duration_seconds'] = vid_dur_map[v]
                                    r['duracion'] = format_duration(vid_dur_map[v])

                            save_js_records(path, records)
                            dataset_dur_map = {r['vid']: r.get('duration_seconds') for r in records if r.get('vid')}
                            update_csv_file(csv_path, dataset_dur_map)
                            update_json_file(json_path, dataset_dur_map)
                            
                            elapsed = time.time() - start_time
                            rate = done / elapsed if elapsed > 0 else 0
                            print(f"  -> Progress: {done}/{total} fetched ({len(vid_dur_map)} valid) - {rate:.1f} vids/sec")

            # Final dataset save
            dataset_dur_map = {r['vid']: r.get('duration_seconds') for r in records if r.get('vid')}
            update_csv_file(csv_path, dataset_dur_map)
            update_json_file(json_path, dataset_dur_map)
            save_js_records(path, records)

            cnt = sum(1 for r in records if r.get('duration_seconds') is not None)
            print(f"  ✓ Finished {csv_name} ({cnt}/{len(records)} rows)\n")

        except Exception as e:
            print(f"Error processing {js_file}: {e}\n")

    print("\n🎉 ALL CSV DATASETS FULLY UPDATED WITH VIDEO DURATIONS!")

if __name__ == '__main__':
    main()
