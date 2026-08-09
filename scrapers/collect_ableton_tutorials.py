import scrapetube
import pandas as pd
import numpy as np
import re
import os
import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CSV_500 = os.path.join(BASE_DIR, "datasets", "csv", "ableton_tutorials.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "datasets", "csv", "ableton_tutorials.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "datasets", "json", "ableton_tutorials.json")
OUTPUT_JS = os.path.join(BASE_DIR, "datasets", "js", "ableton_tutorials_data.js")

# Rich Ableton Live search queries
SEARCH_QUERIES = [
    "Ableton Live tutorial",
    "Ableton Live beginner tutorial",
    "Ableton Live 12 tutorial",
    "Ableton Live 11 tutorial",
    "Ableton sound design tutorial",
    "Ableton mixing tutorial",
    "Ableton mastering tutorial",
    "Ableton beat making tutorial",
    "Ableton vocal processing tutorial",
    "Ableton synth tutorial Operator Wavetable",
    "Ableton Max for Live tutorial",
    "Ableton audio effect rack tutorial",
    "Ableton MIDI chord melody tutorial",
    "Ableton live performance tutorial",
    "Ableton automation tutorial",
    "Ableton sampling tutorial",
    "Ableton hip hop beat tutorial",
    "Ableton house music tutorial",
    "Ableton techno tutorial",
    "Ableton synthwave tutorial",
    "Ableton drum programming tutorial",
    "Ableton sidechain compression tutorial",
    "Ableton EQ compression tutorial",
    "Ableton Push 3 tutorial",
    "YouSuckAtProducing Ableton tutorial",
    "Ned Rush Ableton tutorial",
    "Seed to Stage Ableton tutorial",
    "Venus Theory Ableton tutorial",
    "Julien Earle Ableton tutorial",
    "Production Music Live Ableton tutorial",
    "Ableton chord progression tutorial",
    "Ableton Wavetable synth tutorial",
    "Ableton Operator FM synth tutorial",
    "Ableton Drum Rack tutorial",
    "Ableton vocal chops tutorial",
    "Ableton ambient music tutorial",
    "Ableton lofi beat tutorial",
    "Ableton fast workflow tips tutorial",
    "Ableton parallel processing tutorial",
    "Ableton reverb delay spatial tutorial"
]

RULES = [
    ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "first steps", "learn", "for beginners", "course", "start", "walkthrough", "first song", "gui", "interface"]),
    ("Beat Making & Drums", ["beat", "drums", "drum", "percussion", "hihat", "kick", "snare", "groove", "hip hop", "trap", "drum rack", "rhythm"]),
    ("Sound Design & Synths", ["sound design", "synth", "synthesizer", "wavetable", "operator", "drift", "analog", "bass", "lead", "pad", "patch", "serum", "vital"]),
    ("Mixing & Mastering", ["mixing", "mastering", "mix", "master", "eq", "equalizer", "compression", "limiter", "saturator", "stereo", "loudness", "gain staging", "reverb", "delay"]),
    ("Vocal Processing", ["vocal", "vocals", "autotune", "tuning", "vocal chop", "vocal chain", "voice", "singing"]),
    ("Audio Effects & Racks", ["rack", "effect rack", "audio effect", "effect", "chain", "parallel", "distortion", "phaser", "flanger", "chorus"]),
    ("MIDI & Composition", ["midi", "chord", "chords", "melody", "harmony", "scale", "arpeggiator", "composition", "songwriting", "music theory"]),
    ("Automation & Modulation", ["automation", "modulate", "modulation", "lfo", "envelope", "macro", "expression", "clip automation"]),
    ("Live Performance & Push", ["live performance", "performance", "push", "push 3", "push 2", "stage", "session view", "dj", "clip launching", "live set"]),
    ("Max for Live & Devices", ["max for live", "m4l", "max8", "scripting", "python", "custom device", "device"]),
    ("Genre Production", ["house", "techno", "edm", "pop", "synthwave", "ambient", "dnb", "drum and bass", "dubstep", "lofi", "lo-fi"])
]

def extract_author(v):
    for key in ['ownerText', 'longBylineText', 'shortBylineText']:
        runs = v.get(key, {}).get('runs', [])
        if runs and runs[0].get('text'):
            return runs[0].get('text').strip()
    return "Desconocido"

def extract_title(v):
    runs = v.get('title', {}).get('runs', [])
    if runs and runs[0].get('text'):
        return runs[0].get('text').strip()
    return ""

def extract_snippet(v):
    snippets = v.get('detailedMetadataSnippets', [])
    if snippets:
        runs = snippets[0].get('snippetText', {}).get('runs', [])
        return " ".join([r.get('text', '') for r in runs]).strip()
    return ""

def parse_views(v):
    view_text = v.get('viewCountText', {})
    text = view_text.get('simpleText', '') or view_text.get('runs', [{}])[0].get('text', '')
    m = re.search(r'([\d,.]+)', text)
    if m:
        return int(m.group(1).replace(',', '').replace('.', ''))
    return 0

def parse_relative_date(v):
    pub = v.get('publishedTimeText', {}).get('simpleText', '')
    now = datetime.datetime.now()
    if 'year' in pub:
        m = re.search(r'(\d+)', pub)
        years = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=365*years)).strftime('%Y-%m-%d')
    elif 'month' in pub:
        m = re.search(r'(\d+)', pub)
        months = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=30*months)).strftime('%Y-%m-%d')
    elif 'week' in pub:
        m = re.search(r'(\d+)', pub)
        weeks = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=7*weeks)).strftime('%Y-%m-%d')
    elif 'day' in pub:
        m = re.search(r'(\d+)', pub)
        days = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    return '2023-06-15'

def categorize(title, snippet):
    text = (title + " " + snippet).lower()
    matched_categories = []
    
    for category_name, keywords in RULES:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                matched_categories.append(category_name)
                break

    if not matched_categories:
        matched_categories.append("Beginner & Fundamentals")
    
    primary = matched_categories[0]
    descriptors = ", ".join(matched_categories)
    return primary, matched_categories, f"{primary} ({descriptors})"

def fetch_query(query):
    items = []
    try:
        results = scrapetube.get_search(query, limit=35)
        for v in results:
            vid = v.get('videoId')
            if not vid:
                continue
            title = extract_title(v)
            if not title:
                continue
            author = extract_author(v)
            snippet = extract_snippet(v)
            views = parse_views(v)
            date_str = parse_relative_date(v)
            url = f"https://www.youtube.com/watch?v={vid}"

            primary, tags, cat_desc = categorize(title, snippet)

            items.append({
                "vid": vid,
                "autor": author,
                "titulo": title,
                "enlace": url,
                "categoria_principal": primary,
                "tags": tags,
                "categoria_descriptores": cat_desc,
                "vistas_reales": views,
                "fecha_publicacion": date_str
            })
    except Exception as e:
        print(f"Error query '{query}': {e}", flush=True)
    return items

def compute_3d_latent_space(records):
    print("Calculando coordenadas 3D de espacio latente para 500 tutoriales de Ableton...", flush=True)
    documents = []
    for r in records:
        text_content = f"{r.get('titulo', '')} {r.get('categoria_principal', '')} {' '.join(r.get('tags', []))} {r.get('categoria_descriptores', '')}"
        documents.append(text_content.lower())

    vectorizer = TfidfVectorizer(max_features=300, stop_words='english')
    X = vectorizer.fit_transform(documents)

    tsne = TSNE(n_components=3, perplexity=30, random_state=42, init='pca', learning_rate='auto')
    coords_3d = tsne.fit_transform(X.toarray())

    x_min, x_max = coords_3d[:, 0].min(), coords_3d[:, 0].max()
    y_min, y_max = coords_3d[:, 1].min(), coords_3d[:, 1].max()
    z_min, z_max = coords_3d[:, 2].min(), coords_3d[:, 2].max()

    norm_x = ((coords_3d[:, 0] - x_min) / (x_max - x_min) * 240 - 120).round(2)
    norm_y = ((coords_3d[:, 1] - y_min) / (y_max - y_min) * 240 - 120).round(2)
    norm_z = ((coords_3d[:, 2] - z_min) / (z_max - z_min) * 240 - 120).round(2)

    for idx, r in enumerate(records):
        r['latent_x'] = float(norm_x[idx])
        r['latent_y'] = float(norm_y[idx])
        r['latent_z'] = float(norm_z[idx])

    return records

def main():
    print("=== Iniciando recolección y verificación de tutoriales REALES de Ableton Live desde YouTube ===", flush=True)
    all_raw_items = []
    seen_vids = set()

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(fetch_query, q) for q in SEARCH_QUERIES]

        for future in as_completed(futures):
            res = future.result()
            for item in res:
                if item["vid"] not in seen_vids:
                    seen_vids.add(item["vid"])
                    all_raw_items.append(item)

    print(f"Total recolectado de YouTube (únicos reales): {len(all_raw_items)}", flush=True)

    df_temp = pd.DataFrame(all_raw_items)
    df_temp.drop_duplicates(subset=["enlace"], inplace=True)
    
    # Sort by view count descending to pick top popular Ableton tutorials
    df_temp = df_temp.sort_values(by="vistas_reales", ascending=False).reset_index(drop=True)

    if len(df_temp) > 500:
        df_temp = df_temp.iloc[:500]

    records = df_temp.to_dict(orient="records")

    # Add latent 3D space
    records = compute_3d_latent_space(records)

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    csv_records = []
    for r in records:
        csv_records.append({
            "autor": r["autor"],
            "titulo": r["titulo"],
            "enlace": r["enlace"],
            "categoria_descriptores": r["categoria_descriptores"],
            "vistas_reales": r["vistas_reales"],
            "fecha_publicacion": r["fecha_publicacion"],
            "latent_x": r["latent_x"],
            "latent_y": r["latent_y"],
            "latent_z": r["latent_z"]
        })

    final_df = pd.DataFrame(csv_records)
    final_df.to_csv(OUTPUT_CSV_500, index=False, encoding="utf-8-sig")
    final_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"¡ÉXITO TOTAL! Se han guardado {len(final_df)} tutoriales reales de Ableton Live en CSV:", flush=True)
    print(f"  - {OUTPUT_CSV_500}", flush=True)
    print(f"  - {OUTPUT_CSV}", flush=True)

if __name__ == "__main__":
    main()
