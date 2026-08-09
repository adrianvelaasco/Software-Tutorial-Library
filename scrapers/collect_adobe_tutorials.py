import scrapetube
import pandas as pd
import numpy as np
import re
import os
import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "datasets", "csv")
JS_DIR = os.path.join(BASE_DIR, "datasets", "js")
JSON_DIR = os.path.join(BASE_DIR, "datasets", "json")

ADOBE_SOFTWARES = {
    "premiere": {
        "title": "Adobe Premiere Pro",
        "csv_500": os.path.join(CSV_DIR, "premiere_tutorials.csv"),
        "csv": os.path.join(CSV_DIR, "premiere_tutorials.csv"),
        "js": os.path.join(JS_DIR, "premiere_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "premiere_tutorials.json"),
        "queries": [
            "Adobe Premiere Pro tutorial",
            "Premiere Pro beginner tutorial",
            "Premiere Pro video editing tutorial",
            "Premiere Pro color grading tutorial Lumetri",
            "Premiere Pro transition effect tutorial",
            "Premiere Pro audio editing tutorial",
            "Premiere Pro text animation tutorial",
            "Premiere Pro speed ramp tutorial",
            "Premiere Pro green screen keying tutorial",
            "Premiere Pro export settings 4k tutorial",
            "Premiere Pro multi cam tutorial",
            "Premiere Pro fast workflow tips tutorial",
            "Premiere Pro cinematic look tutorial",
            "Premiere Pro lower thirds tutorial",
            "Cinecom net Premiere Pro tutorial",
            "Peter McKinnon Premiere Pro tutorial",
            "Premiere Gal tutorial",
            "Justin Odisho Premiere Pro tutorial",
            "Daniel Schiffer Premiere Pro tutorial",
            "Becky and Chris Premiere Pro"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "first steps", "learn", "for beginners", "course", "start", "walkthrough", "interface", "timeline"]),
            ("Video Editing & Cutting", ["editing", "cut", "trim", "transitions", "ripple edit", "multicam", "sequence", "speed ramp", "montage", "pacing"]),
            ("Color Grading & Lumetri", ["lumetri", "color grading", "color correction", "lut", "luts", "scopes", "cinematic look", "teal and orange", "skin tones"]),
            ("Audio Editing & Sound", ["audio", "sound", "noise removal", "mixing", "voiceover", "music", "sound design", "audio effects", "essential sound"]),
            ("Titles & Motion Graphics", ["titles", "lower thirds", "text", "mogrt", "essential graphics", "typography", "animation", "motion graphics"]),
            ("VFX & Green Screen", ["keying", "chroma key", "green screen", "masking", "tracking", "opacity", "blending", "visual effects", "vfx"]),
            ("Export & Settings", ["export", "render", "h264", "mp4", "4k", "bit rate", "encoder", "workflow", "sequence settings"])
        ]
    },
    "aftereffects": {
        "title": "Adobe After Effects",
        "csv_500": os.path.join(CSV_DIR, "aftereffects_tutorials.csv"),
        "csv": os.path.join(CSV_DIR, "aftereffects_tutorials.csv"),
        "js": os.path.join(JS_DIR, "aftereffects_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "aftereffects_tutorials.json"),
        "queries": [
            "Adobe After Effects tutorial",
            "After Effects beginner tutorial",
            "After Effects motion graphics tutorial",
            "After Effects text animation tutorial",
            "After Effects 3D camera tracker tutorial",
            "After Effects expressions tutorial",
            "After Effects particle effect tutorial Particular",
            "After Effects logo animation tutorial",
            "After Effects character animation tutorial DUIK",
            "After Effects green screen rotoscoping tutorial",
            "After Effects VFX compositing tutorial",
            "After Effects kinetic typography tutorial",
            "After Effects liquid animation tutorial",
            "After Effects HUD sci-fi UI tutorial",
            "Ben Marriott After Effects tutorial",
            "Sonduck Film After Effects tutorial",
            "Jake In Motion After Effects tutorial",
            "Manuel Does Motion After Effects",
            "Avnish Parker After Effects",
            "Video Copilot Andrew Kramer After Effects"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "keyframes", "composition"]),
            ("Motion Graphics & Typography", ["motion graphics", "mograph", "kinetic typography", "text animation", "shape layers", "logo animation", "liquid animation"]),
            ("VFX & Compositing", ["vfx", "compositing", "green screen", "keying", "tracking", "camera tracking", "rotoscoping", "element 3d", "saber", "stardust"]),
            ("3D & Camera Tracker", ["3d", "3d camera", "camera tracking", "3d space", "depth", "cinema 4d", "element 3d", "lighting", "shadows"]),
            ("Expressions & Automation", ["expression", "expressions", "code", "script", "loop", "wiggle", "math", "automation", "slider control", "macro"]),
            ("Visual Effects & Particles", ["particle", "trapcode", "particular", "optical flares", "glow", "glitch", "distortion", "liquid", "hud", "sci-fi"]),
            ("Character Animation & Rigging", ["character", "rigging", "duik", "limbs", "walk cycle", "puppet tool", "joysticks 'n sliders", "character animation"])
        ]
    },
    "photoshop": {
        "title": "Adobe Photoshop",
        "csv_500": os.path.join(CSV_DIR, "photoshop_tutorials.csv"),
        "csv": os.path.join(CSV_DIR, "photoshop_tutorials.csv"),
        "js": os.path.join(JS_DIR, "photoshop_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "photoshop_tutorials.json"),
        "queries": [
            "Adobe Photoshop tutorial",
            "Photoshop beginner tutorial",
            "Photoshop photo editing retouching tutorial",
            "Photoshop photo manipulation compositing tutorial",
            "Photoshop poster design tutorial",
            "Photoshop text effects tutorial",
            "Photoshop digital painting tutorial",
            "Photoshop background removal tutorial",
            "Photoshop frequency separation tutorial",
            "Photoshop Generative Fill AI tutorial Firefly",
            "Photoshop YouTube thumbnail tutorial",
            "Photoshop Camera Raw tutorial",
            "PiXimperfect Photoshop tutorial",
            "Phlearn Photoshop tutorial",
            "Nemanja Sekulic Photoshop tutorial",
            "Benny Productions Photoshop tutorial",
            "Unmesh Dinda Photoshop tutorial",
            "Photoshop Training Channel tutorial",
            "Spoon Graphics Photoshop tutorial",
            "Texturelabs Photoshop tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "layers", "selection", "mask", "tools"]),
            ("Photo Editing & Retouching", ["retouching", "skin", "portrait", "frequency separation", "dodge and burn", "eyes", "teeth", "color grading", "camera raw", "lightroom"]),
            ("Photo Manipulation & Compositing", ["photo manipulation", "compositing", "blend", "blending", "fantasy", "surreal", "poster", "background removal", "shadows", "lighting"]),
            ("Graphic Design & Poster", ["poster", "flyer", "banner", "graphic design", "thumbnail", "youtube thumbnail", "branding", "layout", "typography"]),
            ("Digital Painting & Drawing", ["painting", "digital painting", "brush", "brushes", "illustration", "concept art", "drawing", "shading", "tablet"]),
            ("Text Effects & Typography", ["text effect", "3d text", "chrome", "neon", "gold", "typography", "layer styles", "bevel", "emboss", "drop shadow"]),
            ("Generative AI & Firefly", ["generative fill", "firefly", "ai", "generative", "remove background", "neural filters", "smart object", "content aware"])
        ]
    }
}

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

def categorize(title, snippet, rules):
    text = (title + " " + snippet).lower()
    matched_categories = []
    
    for category_name, keywords in rules:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                matched_categories.append(category_name)
                break

    if not matched_categories:
        matched_categories.append("Beginner & Fundamentals")
    
    primary = matched_categories[0]
    descriptors = ", ".join(matched_categories)
    return primary, matched_categories, f"{primary} ({descriptors})"

def fetch_query(query, rules):
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

            primary, tags, cat_desc = categorize(title, snippet, rules)

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

def process_software(sw_key, cfg):
    print(f"\n=================================================================", flush=True)
    print(f"  Recolección y verificación para {cfg['title']} ({sw_key})", flush=True)
    print(f"=================================================================", flush=True)
    
    all_raw_items = []
    seen_vids = set()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_query, q, cfg['rules']) for q in cfg['queries']]

        for future in as_completed(futures):
            res = future.result()
            for item in res:
                if item["vid"] not in seen_vids:
                    seen_vids.add(item["vid"])
                    all_raw_items.append(item)

    print(f"Total recolectado de YouTube para {sw_key}: {len(all_raw_items)} únicos reales", flush=True)

    df_temp = pd.DataFrame(all_raw_items)
    df_temp.drop_duplicates(subset=["enlace"], inplace=True)
    df_temp = df_temp.sort_values(by="vistas_reales", ascending=False).reset_index(drop=True)

    if len(df_temp) > 500:
        df_temp = df_temp.iloc[:500]

    records = df_temp.to_dict(orient="records")

    # Add 3D latent space
    records = compute_3d_latent_space(records)

    with open(cfg['json'], 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    csv_records = []
    js_records = []
    for idx, r in enumerate(records):
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
        
        js_records.append({
            'id': idx + 1,
            'vid': r["vid"],
            'autor': r["autor"],
            'titulo': r["titulo"],
            'enlace': r["enlace"],
            'categoria_principal': r["categoria_principal"],
            'tags': r["tags"],
            'categoria_descriptores': r["categoria_descriptores"],
            'views': r["vistas_reales"],
            'upload_date': r["fecha_publicacion"],
            'latent_x': r["latent_x"],
            'latent_y': r["latent_y"],
            'latent_z': r["latent_z"]
        })

    final_df = pd.DataFrame(csv_records)
    final_df.to_csv(cfg['csv_500'], index=False, encoding="utf-8-sig")
    final_df.to_csv(cfg['csv'], index=False, encoding="utf-8-sig")

    var_name = f"{sw_key.upper()}_TUTORIALS_DATA"
    window_name = f"window.{sw_key.upper()}_DATA"
    with open(cfg['js'], 'w', encoding='utf-8') as f:
        f.write(f"const {var_name} = " + json.dumps(js_records, ensure_ascii=False, indent=2) + f";\n{window_name} = {var_name};\n")

    print(f"¡ÉXITO! {len(final_df)} tutoriales guardados para {cfg['title']}:", flush=True)
    print(f"  - {cfg['csv_500']}", flush=True)
    print(f"  - {cfg['csv']}", flush=True)
    print(f"  - {cfg['js']}", flush=True)

def main():
    print("=== Iniciando Generación de Datasets CSV para Adobe Premiere, After Effects y Photoshop ===", flush=True)
    for sw_key, cfg in ADOBE_SOFTWARES.items():
        process_software(sw_key, cfg)
    print("\n=== GENERACIÓN COMPLETA DE ADOBE SUITE CON ÉXITO TOTAL ===", flush=True)

if __name__ == "__main__":
    main()
