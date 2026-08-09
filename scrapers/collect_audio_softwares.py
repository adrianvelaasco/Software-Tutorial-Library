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

AUDIO_SOFTWARES = {
    "maxmsp": {
        "title": "Max/MSP",
        "csv": os.path.join(CSV_DIR, "maxmsp_tutorials.csv"),
        "js": os.path.join(JS_DIR, "maxmsp_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "maxmsp_tutorials.json"),
        "queries": [
            "Max MSP tutorial",
            "Max MSP beginner tutorial",
            "Cycling 74 Max MSP tutorial",
            "Max MSP Jitter tutorial 3D visuals",
            "Max MSP MSP audio synth tutorial",
            "Max for Live tutorial M4L",
            "Max MSP MIDI OSC controller tutorial",
            "Max MSP generative audio tutorial",
            "Max MSP gen~ tutorial DSP",
            "Max MSP matrix video processing tutorial",
            "Max MSP projection mapping jitter tutorial",
            "Max MSP interactive sensor Arduino tutorial",
            "Delicious Max MSP tutorial",
            "Federico Foderaro Max MSP tutorial",
            "Kadenze Max MSP tutorial",
            "Ned Rush Max MSP tutorial",
            "Dude837 Max MSP tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "objects", "patch", "patching"]),
            ("Jitter & Visuals", ["jitter", "jit.cellblock", "jit.pworld", "jit.gl.gridshape", "jit.gl.render", "jit.mo", "matrix", "video processing", "glsl", "shaders", "3d", "generative visuals"]),
            ("MSP Audio & DSP", ["dsp", "msp", "audio", "dac~", "adc~", "cycle~", "buffer~", "groove~", "sfplay~", "synth", "synthesis", "filter", "delay", "reverb", "signal processing"]),
            ("Max for Live (M4L)", ["max for live", "m4l", "live", "ableton", "device", "live.object", "live.path", "rack", "custom device"]),
            ("MIDI & OSC Control", ["midi", "osc", "open sound control", "controller", "serial", "arduino", "udpreceive", "udpsend", "sensor", "hardware"]),
            ("Generative Audio & Algorithmic", ["generative", "algorithmic", "random", "probability", "urn", "counter", "markov", "sequencing", "granular synthesis"]),
            ("Advanced & Gen~", ["gen~", "codebox", "c++", "jitter gen", "dsp gen", "low level", "matrix math", "jitter codebox"])
        ]
    },
    "logicpro": {
        "title": "Logic Pro",
        "csv": os.path.join(CSV_DIR, "logicpro_tutorials.csv"),
        "js": os.path.join(JS_DIR, "logicpro_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "logicpro_tutorials.json"),
        "queries": [
            "Logic Pro tutorial",
            "Logic Pro beginner tutorial",
            "Logic Pro X tutorial",
            "Logic Pro beat making tutorial",
            "Logic Pro Alchemy synth tutorial",
            "Logic Pro vocal processing tutorial Flex Pitch",
            "Logic Pro mixing mastering tutorial",
            "Logic Pro drum machine designer tutorial",
            "Logic Pro smart controls automation tutorial",
            "Logic Pro orchestral score tutorial",
            "Logic Pro Sampler Quick Sampler tutorial",
            "Logic Pro X fast workflow tips tutorial",
            "Music Tech Help Guy Logic Pro tutorial",
            "Why Logic Pro Rules tutorial",
            "EDM Prod Logic Pro tutorial",
            "Sevdaliza Logic Pro tutorial",
            "Charles Cleyn Logic Pro tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "interface", "track setup"]),
            ("Beat Making & Drums", ["drums", "drum machine designer", "step sequencer", "beat", "hip hop", "trap", "boom bap", "rhythm", "pattern"]),
            ("Synth & Sound Design", ["alchemy", "retro synth", "es2", "quick sampler", "sampler", "synth", "sound design", "lead", "bass", "pad"]),
            ("Vocal Processing & Flex Pitch", ["vocal", "vocals", "flex pitch", "pitch correction", "tuning", "harmony", "vocal chain", "reverb", "delay"]),
            ("Mixing & Mastering", ["mixing", "mastering", "eq", "channel eq", "vintage eq", "compressor", "limiter", "loudness", "bus", "aux", "mix engineer"]),
            ("Automation & Smart Controls", ["automation", "smart controls", "midi fx", "arpeggiator", "modifier", "flex time", "quantize", "workflow tips"]),
            ("Orchestral & Composition", ["orchestral", "film score", "cinematic", "strings", "brass", "midi", "articulation", "score editor", "arrangement"])
        ]
    },
    "reaper": {
        "title": "Cockos REAPER",
        "csv": os.path.join(CSV_DIR, "reaper_tutorials.csv"),
        "js": os.path.join(JS_DIR, "reaper_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "reaper_tutorials.json"),
        "queries": [
            "REAPER tutorial DAW",
            "REAPER beginner tutorial Cockos",
            "REAPER mixing tutorial ReaEQ ReaComp",
            "REAPER customization SWS ReaPack tutorial",
            "REAPER audio editing comping tutorial",
            "REAPER MIDI virtual instrument VST tutorial",
            "REAPER JSFX stock plugin tutorial",
            "REAPER game audio FMOD Wwise tutorial",
            "REAPER mastering LUFS tutorial",
            "REAPER custom actions workflow tutorial",
            "REAPER Mania Kenny Gioia tutorial",
            "The REAPER Blog Jon Tidey tutorial",
            "REAPER Made Easy tutorial",
            "HopPole Studios REAPER tutorial"
        ],
        "rules": [
            ("Beginner & Fundamentals", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "overview", "fundamentals", "learn", "course", "start", "walkthrough", "interface", "preferences"]),
            ("Mixing & Mastering", ["mixing", "mastering", "eq", "reaeq", "reacomp", "compressor", "limiter", "routing", "folder tracks", "bus", "loudness", "lufs", "mix"]),
            ("Customization & Scripts", ["reascript", "script", "custom actions", "reapack", "sws", "extension", "toolbar", "theme", "shortcut", "workflow"]),
            ("Audio Editing & Comping", ["editing", "comping", "razor edit", "ripple edit", "time stretch", "pitch shift", "take envelopes", "item properties"]),
            ("MIDI & Virtual Instruments", ["midi", "vst", "vsti", "virtual instrument", "piano roll", "midi editor", "cc lane", "quantization", "drum mapping"]),
            ("JSFX & Stock Plugins", ["jsfx", "js plugin", "readelay", "reaverb", "reaxcomp", "reagate", "stock plugin", "custom jsfx"]),
            ("Game Audio & Sound Design", ["game audio", "wwise", "fmod", "sound design", "foley", "batch render", "subproject", "spatial audio", "ambisonics"])
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
    print("=== Iniciando Generación de Datasets CSV para Max/MSP, Logic Pro y REAPER ===", flush=True)
    for sw_key, cfg in AUDIO_SOFTWARES.items():
        process_software(sw_key, cfg)
    print("\n=== GENERACIÓN COMPLETA DE AUDIO SOFTWARES CON ÉXITO TOTAL ===", flush=True)

if __name__ == "__main__":
    main()
