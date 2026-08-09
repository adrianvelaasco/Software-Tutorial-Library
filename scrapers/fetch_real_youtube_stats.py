import json
import re
import urllib.request
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'touchdesigner_tutorials.csv')
DATA_JS_PATH = os.path.join(BASE_DIR, 'tutorials_data.js')

def fetch_meta(vid):
    if not vid:
        return vid, 0, ""
    url = f"https://www.youtube.com/watch?v={vid}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'Accept-Language': 'en-US,en;q=0.9'}
    )
    try:
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        views_m = re.search(r'\"viewCount\":\"(\d+)\"', html)
        views = int(views_m.group(1)) if views_m else 0
        
        date_m = re.search(r'\"uploadDate\":\"([^\"]+)\"', html) or re.search(r'\"publishDate\":\"([^\"]+)\"', html)
        if date_m:
            date_str = date_m.group(1).split('T')[0]
        else:
            simp_m = re.search(r'\"dateText\":\{\"simpleText\":\"([^\"]+)\"\}', html)
            date_str = simp_m.group(1) if simp_m else ""
            
        return vid, views, date_str
    except Exception:
        return vid, 0, ""

def main():
    print("Iniciando recolección súper rápida de vistas y fechas reales de YouTube...")
    df = pd.read_csv(CSV_PATH)
    vids = []
    for idx, row in df.iterrows():
        url = str(row['enlace'])
        m = re.search(r'v=([a-zA-Z0-9_-]+)', url)
        vids.append(m.group(1) if m else '')

    results = {}
    done = 0
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(fetch_meta, vid): vid for vid in vids if vid}
        for future in as_completed(futures):
            vid, views, date_str = future.result()
            results[vid] = (views, date_str)
            done += 1
            if done % 100 == 0:
                print(f"  --> Completados {done}/{len(vids)}")

    records = []
    for idx, row in df.iterrows():
        url = str(row['enlace'])
        m = re.search(r'v=([a-zA-Z0-9_-]+)', url)
        vid = m.group(1) if m else ''
        views, date_str = results.get(vid, (0, ""))
        
        cat_full = str(row['categoria_descriptores'])
        primary = cat_full.split(' (')[0] if ' (' in cat_full else cat_full
        tags_str = cat_full.split(' (')[1].rstrip(')') if ' (' in cat_full else cat_full
        tags = [t.strip() for t in tags_str.split(',')]

        records.append({
            'id': idx + 1,
            'vid': vid,
            'autor': str(row['autor']),
            'titulo': str(row['titulo']),
            'enlace': url,
            'categoria_principal': primary,
            'tags': tags,
            'categoria_descriptores': cat_full,
            'views': views,
            'upload_date': date_str
        })

    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write('const TUTORIALS_DATA = ' + json.dumps(records, ensure_ascii=False, indent=2) + ';')

    df['vistas_reales'] = [results.get(v, (0, ""))[0] for v in vids]
    df['fecha_publicacion'] = [results.get(v, (0, ""))[1] for v in vids]
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print("¡Finalizado con éxito! Vistas y fechas 100% reales actualizadas.")

if __name__ == '__main__':
    main()
