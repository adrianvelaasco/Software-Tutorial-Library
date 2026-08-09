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
OUTPUT_CSV_500 = os.path.join(BASE_DIR, "datasets", "csv", "blender_tutorials.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "datasets", "csv", "blender_tutorials.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "datasets", "json", "blender_tutorials.json")
OUTPUT_JS = os.path.join(BASE_DIR, "datasets", "js", "blender_tutorials_data.js")

# Rich Blender search queries
SEARCH_QUERIES = [
    "Blender tutorial",
    "Blender beginner tutorial",
    "Blender 4.0 tutorial",
    "Blender 4.1 tutorial",
    "Blender 4.2 tutorial",
    "Blender donut tutorial",
    "Blender 3D modeling tutorial",
    "Blender geometry nodes tutorial",
    "Blender shader tutorial",
    "Blender sculpting tutorial",
    "Blender animation tutorial",
    "Blender rigging tutorial",
    "Blender lighting cycles tutorial",
    "Blender eevee rendering tutorial",
    "Blender fluid simulation tutorial",
    "Blender cloth simulation tutorial",
    "Blender python script tutorial",
    "Blender grease pencil tutorial",
    "Blender hard surface tutorial",
    "Blender motion graphics tutorial",
    "Blender environment archviz tutorial",
    "Blender character modeling tutorial",
    "Blender texture procedural tutorial",
    "Blender low poly tutorial",
    "Blender particle simulation tutorial",
    "Blender UV unwrapping tutorial",
    "Blender retopology tutorial",
    "Blender volumetric fog tutorial",
    "Blender photorealistic render tutorial",
    "Blender compositor tutorial",
    "Blender Guru tutorial",
    "CG Boost Blender tutorial",
    "Ducky 3D Blender tutorial",
    "Grant Abbitt Blender tutorial",
    "CG Matter Blender tutorial",
    "Ryan King Art Blender tutorial",
    "Erindale Blender tutorial",
    "Ian Hubert Blender tutorial",
    "Curtis Holt Blender tutorial",
    "Joey Carlino Blender tutorial",
    "Blender Made Easy tutorial",
    "Kaizen Tutorials Blender",
    "Bad Normals Blender",
    "Cartesian Caramel Blender",
    "Daniel Krafft Blender",
    "Derek Elliott Blender tutorial",
    "Polygon Runway Blender tutorial",
    "Royal Skies Blender tutorial",
    "CG Geeks Blender tutorial",
    "CrossMind Studio Blender tutorial"
]

RULES = [
    ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "first steps", "learn", "for beginners", "course", "start", "walkthrough", "noob", "noobs", "donut"]),
    ("3D Modeling & Sculpting", ["modeling", "modelling", "sculpt", "sculpting", "mesh", "retopology", "hard surface", "subdivision", "boolean", "low poly", "character modeling", "bevel", "topology", "extrude", "model"]),
    ("Geometry Nodes & Procedural", ["geometry nodes", "geonodes", "procedural", "fields", "scatter", "procedural modeling", "node group"]),
    ("Shaders & Texturing", ["shader", "texture", "texturing", "uv mapping", "materials", "node wrangler", "pbr", "glass", "toon shader", "painting", "baking", "unwrapping", "material", "shading"]),
    ("Lighting & Rendering", ["lighting", "render", "cycles", "eevee", "compositor", "camera", "depth of field", "hdri", "volumetric", "fog", "studio lighting", "light", "rendering", "pass", "caustics"]),
    ("Rigging & Character", ["rig", "rigging", "armature", "bone", "weight paint", "character", "inverse kinematics", "ik", "shape keys", "rigify", "face rig"]),
    ("Animation & Keyframing", ["animation", "animate", "keyframe", "graph editor", "walk cycle", "camera animation", "drivers", "interpolation", "rigid body animation", "timeline"]),
    ("VFX & Physics Simulation", ["simulation", "physics", "fluid", "mantaflow", "fire", "smoke", "cloth", "rigid body", "soft body", "particle", "particles", "explosion", "destruction", "water", "ocean", "hair"]),
    ("Grease Pencil & 2D Art", ["grease pencil", "2d animation", "2d", "line art", "storyboard", "drawing", "anime", "hand drawn"]),
    ("Motion Graphics & Abstract", ["motion graphics", "mograph", "abstract", "satisfying", "neon", "generative", "visualizer", "loop", "kinetic"]),
    ("Architectural & Environment", ["archviz", "architecture", "environment", "landscape", "building", "room", "interior", "forest", "nature", "terrain", "foliage", "city", "house"]),
    ("Python & Scripting", ["python", "script", "scripting", "addon", "add-on", "automation", "bmesh", "blender api"])
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
    print("Calculando coordenadas 3D de espacio latente para 500 tutoriales de Blender...", flush=True)
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
    print("=== Iniciando recolección y verificación de tutoriales REALES de Blender desde YouTube ===", flush=True)
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
    
    # Sort by view count descending to pick top popular Blender tutorials
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

    print(f"¡ÉXITO TOTAL! Se han guardado {len(final_df)} tutoriales reales de Blender en CSV:", flush=True)
    print(f"  - {OUTPUT_CSV_500}", flush=True)
    print(f"  - {OUTPUT_CSV}", flush=True)

if __name__ == "__main__":
    main()
