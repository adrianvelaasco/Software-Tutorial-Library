import os
import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'touchdesigner_tutorials.csv')
DATA_JS_PATH = os.path.join(BASE_DIR, 'tutorials_data.js')

def main():
    print("Calculando proyecciones 3D (x, y, z) de espacio latente para 500 tutoriales...")
    
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        text = f.read()
        records = json.loads(text.replace('const TUTORIALS_DATA = ', '').rstrip(';'))
        
    print(f"Cargados {len(records)} registros.")
    
    documents = []
    for r in records:
        text_content = f"{r.get('titulo', '')} {r.get('categoria_principal', '')} {' '.join(r.get('tags', []))} {r.get('categoria_descriptores', '')}"
        documents.append(text_content.lower())

    vectorizer = TfidfVectorizer(max_features=300, stop_words='english')
    X = vectorizer.fit_transform(documents)

    # 3D Dimensionality reduction using t-SNE
    tsne = TSNE(n_components=3, perplexity=30, random_state=42, init='pca', learning_rate='auto')
    coords_3d = tsne.fit_transform(X.toarray())

    # Normalize coordinates to [-120, 120] range in 3D space
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

    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write('const TUTORIALS_DATA = ' + json.dumps(records, ensure_ascii=False, indent=2) + ';')

    df = pd.read_csv(CSV_PATH)
    df['latent_x'] = norm_x
    df['latent_y'] = norm_y
    df['latent_z'] = norm_z
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')

    print("¡Coordenadas 3D (x, y, z) guardadas exitosamente!")

if __name__ == '__main__':
    main()
