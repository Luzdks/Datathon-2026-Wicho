"""
Script para entrenar y guardar el modelo de clustering (KMeans + PCA)
Basado en el notebook EDA_tablatransaccionfinal.ipynb
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "Back", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 70)
print("🤖 ENTRENANDO MODELO DE CLUSTERING (KMeans + PCA)")
print("=" * 70)

# 1. Cargar datos
print("\n[1] Cargando datos...")
clientes = pd.read_csv(os.path.join(DATA_DIR, "hey_clientes.csv"))
productos = pd.read_csv(os.path.join(DATA_DIR, "hey_productos.csv"))
transacciones = pd.read_csv(os.path.join(DATA_DIR, "hey_transacciones.csv"))
print(f"✅ {len(clientes)} clientes cargados")

# 2. Preparar features
print("\n[2] Preparando features...")

# Features numéricas y binarias
numericas = [
    'edad', 'ingreso_mensual_mxn', 'score_buro', 'satisfaccion_1_10'
]

binarias = ['es_hey_pro']

# Crear DataFrame con features disponibles (filtrar a los que existan)
available_cols = [col for col in numericas + binarias if col in clientes.columns]
df = clientes[['user_id'] + available_cols].copy()

# Rellenar NaN
for col in available_cols:
    if col in numericas:
        df[col] = df[col].fillna(df[col].median())
    else:
        df[col] = df[col].fillna(0)

# Agregar features agregadas de transacciones
trans_agg = transacciones.groupby('user_id').agg({
    'monto': ['sum', 'mean', 'count'],
}).reset_index()
trans_agg.columns = ['user_id', 'monto_total', 'monto_promedio', 'num_transacciones']

df = df.merge(trans_agg, on='user_id', how='left')
df[['monto_total', 'monto_promedio', 'num_transacciones']] = df[['monto_total', 'monto_promedio', 'num_transacciones']].fillna(0)

print(f"✅ Features preparados: {df.shape[1]-1} características")

# 3. Escalado
print("\n[3] Escalando features...")
feature_cols = [col for col in df.columns if col != 'user_id']
X = df[feature_cols].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"✅ Datos escalados: {X_scaled.shape}")

# 4. PCA (reducción dimensional)
# Usar min(n_features - 1, 5) para no exceder dimensiones disponibles
n_pca_components = min(X_scaled.shape[1] - 1, 5)
print(f"\n[4] Aplicando PCA ({n_pca_components} componentes)...")
pca = PCA(n_components=n_pca_components, random_state=42)
embedding = pca.fit_transform(X_scaled)
var_explicada = pca.explained_variance_ratio_.sum() * 100
print(f"✅ PCA completado: {var_explicada:.1f}% varianza explicada")

# 5. KMeans con k=5
print("\n[5] Entrenando KMeans (k=5)...")
km = KMeans(n_clusters=5, random_state=42, n_init=10)
clusters = km.fit_predict(embedding)
df['cluster'] = clusters

print(f"✅ Clustering completado:")
print(df['cluster'].value_counts().sort_index().to_string())

# 6. Guardarel modelo
print("\n[6] Guardando modelo...")
model_data = {
    'scaler': scaler,
    'pca': pca,
    'kmeans': km,
    'feature_columns': feature_cols,
    'cluster_names': {
        0: "Clientes Activos (High-Value)",
        1: "Usuarios Digitales",
        2: "Clientes Básicos",
        3: "Clientes Premium",
        4: "Usuarios en Crecimiento"
    }
}

model_path = os.path.join(MODEL_DIR, "clustering_model.pkl")
with open(model_path, 'wb') as f:
    pickle.dump(model_data, f)
print(f"✅ Modelo guardado: {model_path}")

# 7. Guardar perfiles de clusters
print("\n[7] Generando perfiles de clusters...")
perfil = df.groupby('cluster').agg(
    n_clientes=('user_id', 'count'),
    edad_prom=('edad', 'mean'),
    ingreso_prom=('ingreso_mensual_mxn', 'mean'),
    score_buro_prom=('score_buro', 'mean'),
    satisfaccion_prom=('satisfaccion_1_10', 'mean'),
    pct_hey_pro=('es_hey_pro', 'mean'),
    monto_promedio=('monto_promedio', 'mean'),
    transacciones_prom=('num_transacciones', 'mean'),
).round(2)

print("\nPerfiles de Clusters:")
print(perfil.to_string())

cluster_profiles = perfil.to_dict(orient='index')
with open(os.path.join(MODEL_DIR, "cluster_profiles.pkl"), 'wb') as f:
    pickle.dump(cluster_profiles, f)

print("\n" + "=" * 70)
print("✅ MODELO ENTRENADO Y GUARDADO")
print("=" * 70)
