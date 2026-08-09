import scrapetube
import pandas as pd
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CSV = os.path.join(BASE_DIR, "datasets", "csv", "touchdesigner_tutorials.csv")

# Expanded, rich search queries
SEARCH_QUERIES = [
    "TouchDesigner tutorial",
    "TouchDesigner beginner tutorial",
    "TouchDesigner generative art tutorial",
    "TouchDesigner 3D tutorial",
    "TouchDesigner Python script tutorial",
    "TouchDesigner GLSL shader tutorial",
    "TouchDesigner audio reactive tutorial",
    "TouchDesigner instancing tutorial",
    "TouchDesigner pixel mapping tutorial",
    "TouchDesigner Kantan mapper tutorial",
    "TouchDesigner particles tutorial",
    "TouchDesigner feedback loop tutorial",
    "TouchDesigner kinect tracking tutorial",
    "TouchDesigner UI interface tutorial",
    "TouchDesigner raymarching tutorial",
    "TouchDesigner DMX LED tutorial",
    "TouchDesigner SOP TOP CHOP DAT tutorial",
    "TouchDesigner projection mapping tutorial",
    "TouchDesigner visualizer tutorial",
    "TouchDesigner advanced tutorial",
    "TouchDesigner full course",
    "TouchDesigner beginner guide",
    "TouchDesigner tip trick tutorial",
    "TouchDesigner pattern tutorial",
    "TouchDesigner texture tutorial",
    "TouchDesigner animation tutorial",
    "TouchDesigner geometry tutorial",
    "TouchDesigner camera render tutorial",
    "TouchDesigner OSC MIDI tutorial",
    "TouchDesigner notch spout syphon tutorial",
    "TouchDesigner workflow tutorial",
    "TouchDesigner live visual tutorial",
    "TouchDesigner real time graphics tutorial",
    "TouchDesigner node tutorial",
    "TouchDesigner UI widget tutorial"
]

CHANNEL_USERNAMES = [
    "elekktronaut",
    "paketa12",
    "interactiveimmersivehq",
    "acrylicode",
    "DerivativeTD",
    "torinblankensmith",
    "MatthewRagan",
    "LakeHeckaman",
    "nootoo",
    "PPPanik"
]

# Categorization taxonomy rules
RULES = [
    ("Generative Art", ["generative", "pattern", "abstract", "noise", "mandala", "art", "visual", "loop", "flower", "organic", "displace", "wave", "shape", "vector", "perlin", "simplex"]),
    ("3D Model & Geometry", ["3d", "model", "sop", "geometry", "fbx", "obj", "camera", "lighting", "shading", "texture", "material", "render", "mesh", "extrusion", "depth", "light"]),
    ("Scripting & Python", ["python", "script", "dat", "code", "api", "execute", "custom operator", "function", "variable", "class", "pandas", "json", "module"]),
    ("Pixel Mapping & LED", ["pixel mapping", "dmx", "artnet", "led", "lighting control", "fixture", "pixel", "strip", "sacn"]),
    ("Audio Reactive", ["audio", "sound", "music", "beat", "fft", "spectrum", "reactive", "frequency", "microphone", "audio in", "track", "audio-reactive"]),
    ("Instancing & Particles", ["instancing", "instance", "particle", "gpu particle", "pop", "flock", "attractor", "emitter", "field", "point cloud", "points"]),
    ("GLSL & Shaders", ["glsl", "shader", "raymarching", "fragment", "vertex", "compute", "sdf", "signed distance"]),
    ("Feedback & Post-Processing", ["feedback", "bloom", "post-processing", "blur", "color grading", "top", "trail", "echo", "displace", "post processing"]),
    ("Projection Mapping", ["projection mapping", "kantan", "mapper", "mapping", "projector", "calibration", "perspective", "warping"]),
    ("Interactive & Sensors", ["kinect", "tracking", "midi", "osc", "sensor", "touch", "leap motion", "webcam", "real-time", "interaction", "body", "face"]),
    ("UI & Systems", ["ui", "interface", "widget", "control panel", "parameter", "system", "dashboard", "preset", "component", "container"]),
    ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "first steps", "learn", "for beginners", "course", "start", "walkthrough"])
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

def categorize(title, snippet):
    text = (title + " " + snippet).lower()
    matched_categories = []
    
    for category_name, keywords in RULES:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                matched_categories.append(category_name)
                break

    if not matched_categories:
        matched_categories.append("Generative Art")
    
    primary = matched_categories[0]
    descriptors = ", ".join(matched_categories)
    return f"{primary} ({descriptors})"

def fetch_query(query):
    items = []
    try:
        results = scrapetube.get_search(query, limit=40)
        for v in results:
            vid = v.get('videoId')
            if not vid:
                continue
            title = extract_title(v)
            if not title:
                continue
            author = extract_author(v)
            snippet = extract_snippet(v)
            url = f"https://www.youtube.com/watch?v={vid}"
            cat_desc = categorize(title, snippet)
            items.append({
                "vid": vid,
                "autor": author,
                "titulo": title,
                "enlace": url,
                "categoria_descriptores": cat_desc
            })
    except Exception as e:
        print(f"Error query '{query}': {e}")
    return items

def fetch_channel(channel):
    items = []
    try:
        results = scrapetube.get_channel(channel_username=channel, limit=60)
        for v in results:
            vid = v.get('videoId')
            if not vid:
                continue
            title = extract_title(v)
            if not title:
                continue
            author = extract_author(v)
            if author == "Desconocido":
                author = channel
            snippet = extract_snippet(v)
            url = f"https://www.youtube.com/watch?v={vid}"
            cat_desc = categorize(title, snippet)
            items.append({
                "vid": vid,
                "autor": author,
                "titulo": title,
                "enlace": url,
                "categoria_descriptores": cat_desc
            })
    except Exception as e:
        print(f"Error channel '{channel}': {e}")
    return items

def main():
    print("Iniciando recolección paralela de tutoriales de TouchDesigner...")
    all_items = []
    seen_ids = set()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for q in SEARCH_QUERIES:
            futures.append(executor.submit(fetch_query, q))
        for ch in CHANNEL_USERNAMES:
            futures.append(executor.submit(fetch_channel, ch))

        for future in as_completed(futures):
            res = future.result()
            for item in res:
                if item["vid"] not in seen_ids:
                    seen_ids.add(item["vid"])
                    all_items.append(item)

    print(f"Total recolectado sin duplicados: {len(all_items)}")

    df = pd.DataFrame(all_items)
    df.drop(columns=["vid"], inplace=True)
    df.drop_duplicates(subset=["enlace"], inplace=True)

    if len(df) > 500:
        df = df.iloc[:500]

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Guardado exitosamente {len(df)} tutoriales en CSV: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
