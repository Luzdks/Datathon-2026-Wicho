"""
train_modelo_hey.py
===================
Entrenamiento del clasificador de intenciones para Hey Banco.

Modelo: TF-IDF (bigramas) + Regresión Logística Multinomial
Dataset: dataset_50k_anonymized_cleaned.csv  (~50k conversaciones reales)
Accuracy: ~95% en test set (20% holdout, estratificado)

Requisitos:
    pip install pandas scikit-learn

Uso:
    python train_modelo_hey.py

Salidas:
    model_data.json   → vocabulario + coeficientes (embebible en browser)
    model.pkl         → pipeline sklearn serializado (para uso en Python)
"""

import json
import pickle
import os

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline

# ──────────────────────────────────────────────
# 1. CARGA DE DATOS
# ──────────────────────────────────────────────

CSV_PATH = "data/dataset_conversaciones/dataset_50k_anonymized_cleaned.csv"

df = pd.read_csv(CSV_PATH)
print(f"Dataset cargado: {len(df):,} filas, columnas: {df.columns.tolist()}")


# ──────────────────────────────────────────────
# 2. ETIQUETADO AUTOMÁTICO POR PALABRAS CLAVE
#    (reglas derivadas del análisis exploratorio)
# ──────────────────────────────────────────────

def label_topic(text: str):
    """Asigna un tema usando reglas de palabras clave prioritarias."""
    t = text.lower()

    # Orden importa: más específico primero
    if any(k in t for k in [
        "crédito automotriz", "credito automotriz",
        "auto", "carro", "vehículo", "moto"
    ]):
        return "Crédito Automotriz"

    if any(k in t for k in [
        "meses sin intereses", "msi", "diferir", "diferido"
    ]):
        return "Meses sin Intereses"

    if any(k in t for k in [
        "inversión", "inversion", "cetes", "rendimiento", "plazo fijo"
    ]):
        return "Inversiones"

    if any(k in t for k in [
        "transferencia", "transferir", "spei", "enviar dinero"
    ]):
        return "Transferencias"

    if any(k in t for k in [
        "cajero", "retirar", "retiro", "efectivo", "atm"
    ]):
        return "Retiros y Cajero"

    if any(k in t for k in [
        "bloqueo", "bloqueada", "bloqueado",
        "contraseña", "clave", "nip", "seguridad", "desbloquear"
    ]):
        return "Seguridad y Acceso"

    if any(k in t for k in [
        "aclaración", "aclaracion", "queja", "reporte",
        "robo", "fraude", "cargo no reconocido"
    ]):
        return "Aclaraciones"

    if any(k in t for k in [
        "terminal", "cobrar a clientes", "pos", "punto de venta"
    ]):
        return "Terminal de Pago"

    if any(k in t for k in [
        "débito", "debito", "tarjeta de débito"
    ]):
        return "Tarjeta de Débito"

    if any(k in t for k in [
        "crédito", "credito", "tdc", "limite de crédito", "límite"
    ]):
        return "Tarjeta de Crédito"

    if any(k in t for k in [
        "pago", "pagar", "cobro", "fecha de pago", "fecha límite"
    ]):
        return "Pagos"

    if any(k in t for k in [
        "cuenta", "saldo", "consultar", "estado de cuenta"
    ]):
        return "Cuenta y Saldo"

    return None  # Sin etiqueta suficiente


df["topic"] = df["input"].apply(label_topic)

# Solo mensajes con etiqueta y longitud suficiente
labeled = df[df["topic"].notna() & (df["input"].str.len() > 10)].copy()

print(f"\nMuestras etiquetadas: {len(labeled):,}")
print("\nDistribución de temas:")
print(labeled["topic"].value_counts().to_string())


# ──────────────────────────────────────────────
# 3. SPLIT TRAIN / TEST  (80/20 estratificado)
# ──────────────────────────────────────────────

X = labeled["input"]
y = labeled["topic"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"\nTrain: {len(X_train):,}  |  Test: {len(X_test):,}")


# ──────────────────────────────────────────────
# 4. PIPELINE: TF-IDF  +  REGRESIÓN LOGÍSTICA
# ──────────────────────────────────────────────

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=3000,   # vocabulario reducido → rápido y embebible
        ngram_range=(1, 2),  # unigramas + bigramas
        min_df=2,            # ignora términos rarísimos
        sublinear_tf=True,   # log(tf) reduce dominancia de términos frecuentes
    )),
    ("clf", LogisticRegression(
        max_iter=500,
        C=5,                 # regularización moderada
        solver="lbfgs",
    )),
])

print("\nEntrenando pipeline…")
pipeline.fit(X_train, y_train)

# ──────────────────────────────────────────────
# 5. EVALUACIÓN
# ──────────────────────────────────────────────

y_pred = pipeline.predict(X_test)
print("\n── Reporte de clasificación ──")
print(classification_report(y_test, y_pred))


# ──────────────────────────────────────────────
# 6. EXPORTAR MODELO COMPLETO  →  model.pkl
# ──────────────────────────────────────────────

with open("model.pkl", "wb") as f:
    pickle.dump(pipeline, f)
print("✔ model.pkl guardado")


# ──────────────────────────────────────────────
# 7. EXPORTAR PESOS PARA EL BROWSER  →  model_data.json
#    (compatible con el clasificador JS embebido en hey_asistente.html)
# ──────────────────────────────────────────────

# Sugerencias proactivas por tema
TOPIC_SUGGESTIONS = {
    "Tarjeta de Crédito": [
        "¿Cuándo es mi fecha límite de pago?",
        "¿Cómo puedo aumentar mi límite de crédito?",
        "¿Cómo activo meses sin intereses?",
        "¿Cómo cancelo mi tarjeta?",
        "¿Cómo consulto mis estados de cuenta?",
    ],
    "Cuenta y Saldo": [
        "¿Cómo consulto mi saldo?",
        "¿Cómo descargo mi estado de cuenta?",
        "¿Cuántas transferencias puedo hacer al día?",
        "¿Cómo actualizo mis datos personales?",
        "¿Cómo abro una cuenta Hey?",
    ],
    "Transferencias": [
        "¿Cuánto puedo transferir al día?",
        "¿Cuánto tiempo tarda una transferencia SPEI?",
        "¿Cómo hago una transferencia a otro banco?",
        "¿Hay costo por transferir?",
        "¿Puedo cancelar una transferencia?",
    ],
    "Pagos": [
        "¿Cuándo es mi fecha límite de pago?",
        "¿Puedo pagar en OXXO o 7-Eleven?",
        "¿Cómo configuro pago automático?",
        "¿Qué pasa si no pago a tiempo?",
        "¿Cómo pago servicios gubernamentales?",
    ],
    "Seguridad y Acceso": [
        "¿Cómo cambio mi NIP?",
        "¿Cómo desbloqueo mi tarjeta?",
        "¿Cómo recupero acceso a mi cuenta?",
        "¿Qué hago si olvidé mi contraseña?",
        "¿Cómo reporto un cargo no reconocido?",
    ],
    "Retiros y Cajero": [
        "¿En qué cajeros puedo retirar sin comisión?",
        "¿Cuál es el límite de retiro diario?",
        "¿Puedo retirar en OXXO?",
        "¿Cómo cambio el límite de retiro?",
        "¿Puedo retirar sin tarjeta?",
    ],
    "Crédito Automotriz": [
        "¿Cuáles son las tasas de interés?",
        "¿Qué documentos necesito?",
        "¿Cuál es el enganche mínimo?",
        "¿En cuántos meses puedo pagar?",
        "¿Aplica para autos seminuevos?",
    ],
    "Inversiones": [
        "¿Cuál es el rendimiento actual de CETES?",
        "¿Cuánto es lo mínimo para invertir?",
        "¿Puedo retirar mi inversión antes de tiempo?",
        "¿Cuántos plazos están disponibles?",
        "¿Cómo abro una cuenta de inversión?",
    ],
    "Meses sin Intereses": [
        "¿En qué comercios aplican MSI?",
        "¿Cómo activo meses sin intereses?",
        "¿Cuál es el mínimo de compra para MSI?",
        "¿Puedo diferir una compra ya hecha?",
        "¿A cuántos meses puedo diferir?",
    ],
    "Terminal de Pago": [
        "¿Cuánto cuesta la terminal?",
        "¿Cuándo me depositan las ventas?",
        "¿Qué comisión cobra la terminal?",
        "¿Funciona sin internet?",
        "¿Cómo solicito la terminal?",
    ],
    "Aclaraciones": [
        "¿Cómo reporto un cargo no reconocido?",
        "¿Cuánto tiempo tarda una aclaración?",
        "¿Cómo contacto a un asesor?",
        "¿Puedo hacer una aclaración por chat?",
        "¿Qué documentos necesito para la aclaración?",
    ],
    "Tarjeta de Débito": [
        "¿Cómo activo mi tarjeta de débito?",
        "¿Cómo cambio el límite de compras?",
        "¿Cómo bloqueo mi tarjeta?",
        "¿Dónde puedo usarla en el extranjero?",
        "¿Puedo pedir una tarjeta física?",
    ],
}

TOPIC_ICONS = {
    "Tarjeta de Crédito":   "💳",
    "Cuenta y Saldo":       "🏦",
    "Transferencias":       "↔️",
    "Pagos":                "💰",
    "Seguridad y Acceso":   "🔐",
    "Retiros y Cajero":     "🏧",
    "Crédito Automotriz":   "🚗",
    "Inversiones":          "📈",
    "Meses sin Intereses":  "📅",
    "Terminal de Pago":     "🖥️",
    "Aclaraciones":         "📋",
    "Tarjeta de Débito":    "💳",
}

vec = pipeline.named_steps["tfidf"]
clf = pipeline.named_steps["clf"]

# Reentrenar vectorizador sobre TODO el conjunto etiquetado para JSON final
vec_full = TfidfVectorizer(
    max_features=3000, ngram_range=(1, 2), min_df=2, sublinear_tf=True
)
clf_full = LogisticRegression(max_iter=500, C=5, solver="lbfgs")
X_all = vec_full.fit_transform(labeled["input"])
clf_full.fit(X_all, labeled["topic"])

model_data = {
    "vocab":             {k: int(v) for k, v in vec_full.vocabulary_.items()},
    "idf":               [float(x) for x in vec_full.idf_],
    "classes":           clf_full.classes_.tolist(),
    "coef":              [[float(x) for x in row] for row in clf_full.coef_],
    "intercept":         [float(x) for x in clf_full.intercept_],
    "topic_suggestions": TOPIC_SUGGESTIONS,
    "topic_icons":       TOPIC_ICONS,
}

with open("model_data.json", "w", encoding="utf-8") as f:
    json.dump(model_data, f, ensure_ascii=False, separators=(",", ":"))

size_kb = os.path.getsize("model_data.json") / 1024
print(f"✔ model_data.json guardado  ({size_kb:.0f} KB)")


# ──────────────────────────────────────────────
# 8. DEMO: PREDICCIÓN RÁPIDA CON model.pkl
# ──────────────────────────────────────────────

demo_queries = [
    "¿Cómo transfiero dinero a otro banco?",
    "Mi tarjeta está bloqueada, ¿qué hago?",
    "Quiero invertir en CETES",
    "¿Cuándo debo pagar mi tarjeta de crédito?",
    "¿Puedo diferir una compra a meses sin intereses?",
]

print("\n── Demo de predicciones ──")
for q in demo_queries:
    pred = pipeline.predict([q])[0]
    prob = pipeline.predict_proba([q]).max()
    print(f"  '{q[:55]}…'  →  {pred}  ({prob:.0%})")