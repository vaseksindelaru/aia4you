# cluster.py
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

def evaluate_clusters(data, max_clusters=5):
    df = pd.DataFrame(data)
    X = df[list(df.columns)]
    
    # Limitar max_clusters al número de muestras si es menor
    n_samples = X.shape[0]
    max_clusters = min(max_clusters, n_samples)
    
    inertias = []
    for k in range(1, max_clusters + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)
    
    diffs = np.diff(inertias)
    diffs2 = np.diff(diffs) if len(diffs) > 1 else [0]  # Evitar error si hay pocas muestras
    optimal_k = np.argmax(diffs2) + 2 if len(diffs2) > 0 else 1
    optimal_k = max(min(optimal_k, max_clusters), 1)  # Asegurar al menos 1 y no más que max_clusters
    
    return {
        "optimal_clusters": int(optimal_k),
        "inertias": inertias
    }