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

VJ_AI_SOFTWARES = {
    "resolume": {
        "title": "Resolume Arena",
        "csv": os.path.join(CSV_DIR, "resolume_tutorials.csv"),
        "js": os.path.join(JS_DIR, "resolume_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "resolume_tutorials.json"),
        "queries": [
            "Resolume Arena tutorial",
            "Resolume Arena beginner tutorial",
            "Resolume VJ performance tutorial",
            "Resolume Arena projection mapping tutorial",
            "Resolume Wire tutorial generative",
            "Resolume Arena DMX LED pixel mapping tutorial",
            "Resolume Arena NDI Syphon Spout tutorial",
            "Resolume Arena BPM sync audio reactive tutorial",
            "DocOptic Resolume tutorial",
            "Hybrid VJ Resolume tutorial",
            "Sean Bowes Resolume tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "interface", "decks", "clips"]),
            ("Projection & Advanced Output", ["projection mapping", "advanced output", "edge blending", "slices", "output shading", "keystone", "warp", "mapping"]),
            ("Resolume Wire & Generative", ["wire", "resolume wire", "generative", "nodes", "custom effect", "node-based", "patch"]),
            ("DMX & Pixel Mapping", ["dmx", "artnet", "e1.31", "pixel mapping", "led", "fixture", "lighting", "dmx output"]),
            ("NDI, Spout & Routing", ["ndi", "spout", "syphon", "routing", "video input", "capture card", "screen capture", "osc", "midi"])
        ]
    },
    "comfyui": {
        "title": "ComfyUI",
        "csv": os.path.join(CSV_DIR, "comfyui_tutorials.csv"),
        "js": os.path.join(JS_DIR, "comfyui_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "comfyui_tutorials.json"),
        "queries": [
            "ComfyUI tutorial",
            "ComfyUI beginner tutorial node graph",
            "ComfyUI Stable Diffusion XL SDXL tutorial",
            "ComfyUI ControlNet IPAdapter tutorial",
            "ComfyUI AnimateDiff video tutorial",
            "ComfyUI Flux tutorial",
            "ComfyUI custom nodes tutorial",
            "ComfyUI img2img upscaling tutorial",
            "Latent Vision ComfyUI tutorial",
            "Purz ComfyUI tutorial",
            "Scott Detweiler ComfyUI tutorial",
            "Olivio Sarikas ComfyUI"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "installation", "nodes"]),
            ("SDXL, Flux & Models", ["sdxl", "flux", "checkpoint", "lora", "clip", "vae", "model", "stable diffusion", "diffusion"]),
            ("ControlNet & IPAdapter", ["controlnet", "ipadapter", "openpose", "canny", "depth", "reference", "style transfer"]),
            ("AnimateDiff & AI Video", ["animatediff", "video", "animation", "frame", "fps", "video2video", "video to video", "deforum"]),
            ("Upscaling & Custom Nodes", ["upscale", "ultimate sd upscale", "custom nodes", "manager", "comfyui-manager", "hires fix", "tiled ksampler"])
        ]
    },
    "madmapper": {
        "title": "MadMapper",
        "csv": os.path.join(CSV_DIR, "madmapper_tutorials.csv"),
        "js": os.path.join(JS_DIR, "madmapper_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "madmapper_tutorials.json"),
        "queries": [
            "MadMapper tutorial",
            "MadMapper beginner tutorial projection mapping",
            "MadMapper LED pixel mapping DMX ArtNet tutorial",
            "MadMapper 3D calibration Spatial Scanner tutorial",
            "MadMapper materials shaders ISF tutorial",
            "MadMapper Syphon Spout NDI tutorial",
            "MadMapper laser control tutorial",
            "GarageCube MadMapper tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "interface", "surface"]),
            ("Projection Mapping & 3D", ["projection mapping", "3d", "spatial scanner", "calibration", "mesh warping", "masking", "architectural", "building"]),
            ("LED & DMX Fixtures", ["led", "dmx", "artnet", "pixel mapping", "fixtures", "strips", "spi", "madlight"]),
            ("Materials & Shaders", ["materials", "isf", "shaders", "generative", "procedural", "lines", "visuals", "content"]),
            ("Laser & Hardware Integration", ["laser", "dac", "pangolin", "etherdream", "midi", "osc", "syphon", "spout", "ndi"])
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
        results = scrapetube.get_search(query, limit=50)
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
    final_df['latent_x'] = final_df['latent_x'].round(2)
    final_df['latent_y'] = final_df['latent_y'].round(2)
    final_df['latent_z'] = final_df['latent_z'].round(2)
    final_df.to_csv(cfg['csv'], index=False, encoding="utf-8-sig")

    var_name = f"{sw_key.upper()}_TUTORIALS_DATA"
    window_name = f"window.{sw_key.upper()}_DATA"
    with open(cfg['js'], 'w', encoding='utf-8') as f:
        f.write(f"const {var_name} = " + json.dumps(js_records, ensure_ascii=False, indent=2) + f";\n{window_name} = {var_name};\n")

    print(f"¡ÉXITO! {len(final_df)} tutoriales guardados para {cfg['title']}:", flush=True)
    print(f"  - {cfg['csv']}", flush=True)
    print(f"  - {cfg['js']}", flush=True)

def main():
    print("=== Iniciando Generación de Datasets CSV para Resolume Arena, ComfyUI y MadMapper ===", flush=True)
    for sw_key, cfg in VJ_AI_SOFTWARES.items():
        process_software(sw_key, cfg)
    print("\n=== GENERACIÓN COMPLETA DE RESOLUME, COMFYUI Y MADMAPPER CON ÉXITO TOTAL ===", flush=True)

if __name__ == "__main__":
    main()
