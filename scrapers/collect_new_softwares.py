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

NEW_SOFTWARES = {
    "illustrator": {
        "title": "Adobe Illustrator",
        "csv": os.path.join(CSV_DIR, "illustrator_tutorials.csv"),
        "js": os.path.join(JS_DIR, "illustrator_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "illustrator_tutorials.json"),
        "queries": [
            "Adobe Illustrator tutorial",
            "Illustrator beginner tutorial",
            "Illustrator logo design tutorial",
            "Illustrator pen tool tutorial",
            "Illustrator vector illustration tutorial",
            "Illustrator typography text effect tutorial",
            "Illustrator 3D inflation tutorial",
            "Illustrator pattern design tutorial",
            "Illustrator packaging design tutorial",
            "Spoon Graphics Illustrator tutorial",
            "Dansky Illustrator tutorial",
            "Yes I'm a Designer Illustrator tutorial",
            "Satori Graphics Illustrator tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "tools", "interface"]),
            ("Vector & Pen Tool", ["pen tool", "vector", "shapes", "bezier", "pathfinder", "shape builder", "anchor points", "tracing", "live trace"]),
            ("Logo & Branding", ["logo", "logo design", "branding", "monogram", "icon", "badge", "identity", "brand"]),
            ("Typography & Text", ["typography", "text", "font", "lettering", "text effect", "type", "calligraphy", "3d text"]),
            ("Illustration & Art", ["illustration", "vector art", "drawing", "flat design", "character", "isometric", "shading", "gradients"]),
            ("Pattern & Packaging", ["pattern", "seamless", "packaging", "label", "repeating", "textile", "mockup"])
        ]
    },
    "davinci": {
        "title": "DaVinci Resolve",
        "csv": os.path.join(CSV_DIR, "davinci_tutorials.csv"),
        "js": os.path.join(JS_DIR, "davinci_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "davinci_tutorials.json"),
        "queries": [
            "DaVinci Resolve tutorial",
            "DaVinci Resolve beginner tutorial",
            "DaVinci Resolve color grading tutorial Lumetri",
            "DaVinci Resolve Fusion motion graphics tutorial",
            "DaVinci Resolve Fairlight audio tutorial",
            "DaVinci Resolve edit page tutorial",
            "DaVinci Resolve cinematic look LUT tutorial",
            "DaVinci Resolve speed ramp transition tutorial",
            "Casey Faris DaVinci Resolve tutorial",
            "Warped Perception DaVinci Resolve",
            "Cullen Kelly DaVinci Resolve color grading",
            "Darren Mostyn DaVinci Resolve"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "cut page", "edit page"]),
            ("Color Grading & Wheels", ["color grading", "color correction", "color wheels", "lut", "scopes", "cinematic look", "color space transform", "node tree", "log"]),
            ("Fusion & Motion Graphics", ["fusion", "vfx", "motion graphics", "nodes", "tracking", "keying", "green screen", "titles", "lower thirds"]),
            ("Editing & Workflow", ["editing", "cut", "transition", "speed ramp", "multi cam", "proxy", "render", "export", "workflow"]),
            ("Fairlight Audio", ["fairlight", "audio", "sound", "noise reduction", "eq", "compressor", "mixing", "dialogue"])
        ]
    },
    "sibelius": {
        "title": "Avid Sibelius",
        "csv": os.path.join(CSV_DIR, "sibelius_tutorials.csv"),
        "js": os.path.join(JS_DIR, "sibelius_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "sibelius_tutorials.json"),
        "queries": [
            "Avid Sibelius tutorial",
            "Sibelius beginner tutorial notation",
            "Sibelius score layout orchestral tutorial",
            "Sibelius shortcuts fast input tutorial",
            "Sibelius playback NotePerformer tutorial",
            "Sibelius arranging composing tutorial",
            "Sibelius lead sheet chord symbols tutorial",
            "Music Notation Sibelius tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "interface", "note input"]),
            ("Note Input & Shortcuts", ["note input", "keypad", "shortcuts", "speedy", "step time", "flexi-time", "midi keyboard", "entry"]),
            ("Score Formatting & Layout", ["layout", "formatting", "parts", "dynamic parts", "engraving", "page setup", "staves", "system", "score"]),
            ("Playback & NotePerformer", ["playback", "sound", "noteperformer", "vst", "sounds", "expression", "mixer", "audio export"]),
            ("Arranging & Lead Sheets", ["arranging", "lead sheet", "chords", "chord symbols", "lyrics", "orchestration", "transposition", "piano score"])
        ]
    },
    "vsc": {
        "title": "Visual Studio Code",
        "csv": os.path.join(CSV_DIR, "vsc_tutorials.csv"),
        "js": os.path.join(JS_DIR, "vsc_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "vsc_tutorials.json"),
        "queries": [
            "Visual Studio Code tutorial",
            "VS Code beginner tutorial",
            "VS Code extensions best 2024 tutorial",
            "VS Code shortcuts productivity tips",
            "VS Code debugging tutorial",
            "VS Code Git GitHub integration tutorial",
            "VS Code web development HTML CSS JS tutorial",
            "Fireship VS Code tips",
            "Traversy Media VS Code tutorial",
            "Web Dev Simplified VS Code"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "installation", "setup"]),
            ("Extensions & Customization", ["extensions", "plugins", "theme", "customization", "settings.json", "icons", "prettier", "eslint", "copilot"]),
            ("Shortcuts & Productivity", ["shortcuts", "productivity", "tips", "tricks", "multi cursor", "keybindings", "command palette", "snippets"]),
            ("Debugging & Terminal", ["debugging", "debugger", "terminal", "launch.json", "breakpoints", "console", "integrated terminal"]),
            ("Git & Source Control", ["git", "github", "source control", "version control", "merge conflict", "branch", "commit", "push"])
        ]
    },
    "unity": {
        "title": "Unity Engine",
        "csv": os.path.join(CSV_DIR, "unity_tutorials.csv"),
        "js": os.path.join(JS_DIR, "unity_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "unity_tutorials.json"),
        "queries": [
            "Unity tutorial game development",
            "Unity beginner tutorial 2D 3D",
            "Unity C# scripting tutorial",
            "Unity Shader Graph tutorial",
            "Unity UI canvas tutorial",
            "Unity physics Rigidbody tutorial",
            "Unity animation Animator state machine tutorial",
            "Brackeys Unity tutorial",
            "Code Monkey Unity tutorial",
            "Sebastian Lague Unity tutorial",
            "Infallible Code Unity"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "installation", "game loop"]),
            ("C# Scripting", ["c#", "csharp", "scripting", "programming", "code", "mono-behaviour", "variables", "functions", "events"]),
            ("3D & 2D Physics", ["3d", "2d", "physics", "rigidbody", "collider", "collision", "raycast", "movement", "character controller"]),
            ("Shader Graph & Visuals", ["shader graph", "shader", "materials", "urp", "hdrp", "post processing", "lighting", "particles", "vfx graph"]),
            ("UI & Animation", ["ui", "canvas", "menu", "hud", "animator", "animation", "blend tree", "state machine", "sprites"])
        ]
    },
    "unreal": {
        "title": "Unreal Engine",
        "csv": os.path.join(CSV_DIR, "unreal_tutorials.csv"),
        "js": os.path.join(JS_DIR, "unreal_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "unreal_tutorials.json"),
        "queries": [
            "Unreal Engine 5 tutorial",
            "UE5 beginner tutorial",
            "Unreal Engine Blueprints visual scripting tutorial",
            "Unreal Engine Nanite Lumen lighting tutorial",
            "Unreal Engine Niagara particle FX tutorial",
            "Unreal Engine landscape foliage environment tutorial",
            "Unreal Engine MetaHuman character tutorial",
            "Unreal Sensei UE5 tutorial",
            "William Faucher Unreal tutorial",
            "Smart Materials Unreal Engine"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "ue5", "interface"]),
            ("Blueprints Scripting", ["blueprints", "blueprint", "visual scripting", "event graph", "functions", "macro", "character blueprint", "logic"]),
            ("Lumen & Lighting", ["lumen", "nanite", "lighting", "ray tracing", "shadows", "post process", "global illumination", "virtual shadow maps"]),
            ("Niagara VFX & Particles", ["niagara", "vfx", "particles", "smoke", "fire", "explosion", "magic", "fluid", "chaos"]),
            ("Environment & Materials", ["landscape", "foliage", "environment", "materials", "quixel", "megascans", "open world", "biomes"])
        ]
    },
    "python": {
        "title": "Python",
        "csv": os.path.join(CSV_DIR, "python_tutorials.csv"),
        "js": os.path.join(JS_DIR, "python_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "python_tutorials.json"),
        "queries": [
            "Python tutorial",
            "Python beginner tutorial full course",
            "Python object oriented programming OOP tutorial",
            "Python data science Pandas Numpy tutorial",
            "Python web scraping BeautifulSoup Selenium tutorial",
            "Python machine learning PyTorch TensorFlow tutorial",
            "Python automation script tutorial",
            "Python Django FastAPI web tutorial",
            "Corey Schafer Python tutorial",
            "Programming with Mosh Python",
            "FreeCodeCamp Python full course",
            "Tech With Tim Python"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "variables", "loops", "functions"]),
            ("Object-Oriented (OOP)", ["oop", "object oriented", "classes", "inheritance", "polymorphism", "methods", "dunder", "dataclass"]),
            ("Data Science & AI", ["data science", "pandas", "numpy", "matplotlib", "machine learning", "ai", "pytorch", "tensorflow", "scikit-learn"]),
            ("Automation & Scraping", ["automation", "scraping", "web scraping", "beautifulsoup", "selenium", "requests", "bot", "auto", "script"]),
            ("Web Frameworks (Django/FastAPI)", ["web", "django", "fastapi", "flask", "api", "rest api", "backend", "database", "sqlalchemy"])
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
        results = scrapetube.get_search(query, limit=45)
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
    print("=== Iniciando Generación de Datasets CSV para Illustrator, DaVinci, Sibelius, VSC, Unity, Unreal y Python ===", flush=True)
    for sw_key, cfg in NEW_SOFTWARES.items():
        process_software(sw_key, cfg)
    print("\n=== GENERACIÓN COMPLETA DE LOS 7 NUEVOS SOFTWARES CON ÉXITO TOTAL ===", flush=True)

if __name__ == "__main__":
    main()
