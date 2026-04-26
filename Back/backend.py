from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import pandas as pd
import os
import pickle
from dotenv import load_dotenv
from typing import Optional, Dict, List

load_dotenv()

# Inicializar FastAPI
app = FastAPI(title="Hey Banco - Havi Backend")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY no encontrada en .env")
groq_client = Groq(api_key=GROQ_API_KEY)

# Cargar datasets
print("Cargando datasets...")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "Back", "models")

try:
    clientes = pd.read_csv(os.path.join(DATA_DIR, "hey_clientes.csv"))
    productos = pd.read_csv(os.path.join(DATA_DIR, "hey_productos.csv"))
    transacciones = pd.read_csv(os.path.join(DATA_DIR, "hey_transacciones.csv"))
    print(f"✅ Datasets cargados: {len(clientes)} clientes")
    print(f"   Primer usuario: {clientes['user_id'].iloc[0]}")
except FileNotFoundError as e:
    print(f"❌ Error cargando datasets: {e}")

# Cargar modelo de clustering
clustering_model = None
cluster_profiles = None
try:
    with open(os.path.join(MODELS_DIR, "clustering_model.pkl"), 'rb') as f:
        clustering_model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "cluster_profiles.pkl"), 'rb') as f:
        cluster_profiles = pickle.load(f)
    print(f"✅ Modelo de clustering cargado (5 clusters)")
except FileNotFoundError:
    print("⚠️ Modelo de clustering no encontrado. Ejecuta: python train_clustering_model.py")

# Modelos Pydantic
class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_history: List[Dict] = []  # Histórico de conversación

class ChatResponse(BaseModel):
    response: str
    user_name: Optional[str] = None

# ==================== FUNCIONES ====================

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Obtener perfil del usuario desde CSV (con caché)."""
    # Validar que existe en clientes
    if user_id not in clientes["user_id"].values:
        return None
    
    cliente_data = clientes[clientes["user_id"] == user_id].iloc[0].to_dict()
    
    # Productos activos
    productos_usuario = productos[productos["user_id"] == user_id]
    productos_activos = []
    if not productos_usuario.empty:
        productos_activos = productos_usuario[
            productos_usuario["estatus"].str.lower().isin(["activo", "vigente"])
        ]["tipo_producto"].tolist()
    
    # Últimas 5 transacciones
    ultimas_5_trans = []
    trans_usuario = transacciones[transacciones["user_id"] == user_id]
    if not trans_usuario.empty:
        trans_copia = trans_usuario.copy()
        trans_copia["fecha_hora"] = pd.to_datetime(trans_copia["fecha_hora"], errors='coerce')
        ultimas_5_trans = trans_copia.nlargest(5, "fecha_hora")[
            ["fecha_hora", "tipo_operacion", "monto", "descripcion_libre"]
        ].to_dict(orient="records")
    
    cliente_data["productos_activos"] = productos_activos
    cliente_data["ultimas_transacciones"] = ultimas_5_trans
    
    return cliente_data


def predict_user_cluster(user_id: str) -> Optional[int]:
    """Predecir el cluster de un usuario usando el modelo entrenado."""
    if not clustering_model:
        return None
    
    try:
        cliente = clientes[clientes["user_id"] == user_id].copy()
        if cliente.empty:
            return None
        
        # Agregar features de transacciones
        trans_usuario = transacciones[transacciones["user_id"] == user_id]
        if not trans_usuario.empty:
            monto_total = trans_usuario["monto"].sum()
            monto_promedio = trans_usuario["monto"].mean()
            num_transacciones = len(trans_usuario)
        else:
            monto_total = 0
            monto_promedio = 0
            num_transacciones = 0
        
        cliente.loc[cliente.index[0], "monto_total"] = monto_total
        cliente.loc[cliente.index[0], "monto_promedio"] = monto_promedio
        cliente.loc[cliente.index[0], "num_transacciones"] = num_transacciones
        
        # Obtener features en el mismo orden del entrenamiento
        feature_cols = clustering_model['feature_columns']
        
        # Validar que todos los features existen
        missing_cols = [col for col in feature_cols if col not in cliente.columns]
        if missing_cols:
            print(f"⚠️ Features faltantes para {user_id}: {missing_cols}")
            return None
        
        X_user = cliente[feature_cols].values
        
        # Aplicar scaler y PCA
        X_scaled = clustering_model['scaler'].transform(X_user)
        embedding = clustering_model['pca'].transform(X_scaled)
        
        # Predecir cluster
        cluster = clustering_model['kmeans'].predict(embedding)[0]
        return int(cluster)
    except Exception as e:
        print(f"❌ Error prediciendo cluster para {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def build_system_prompt(profile: Optional[Dict] = None, cluster: Optional[int] = None) -> str:
    """System prompt dinámico basado en perfil y cluster del usuario."""
    
    # ===== SIN IDENTIFICACIÓN (usuario genérico) =====
    if not profile:
        return """Eres Havi, asistente de Hey Banco.

Responde preguntas sobre:
- Productos Hey Banco (cuentas, tarjetas, créditos, Hey Pro)
- Servicios generales
- Financias

Si preguntan sobre SALDO, SUS PRODUCTOS, o datos personales → sugiere escribir USR-XXXXX para ver.

NUNCA: tarjetas, PINs, contraseñas."""
    
    # ===== CON IDENTIFICACIÓN =====
    ocupacion = profile.get("ocupacion", "Usuario").title()
    edad = profile.get("edad", "?")
    productos_activos = profile.get("productos_activos", [])
    ultimas_trans = profile.get("ultimas_transacciones", [])
    
    # Calcular saldo aproximado (suma de últimas transacciones)
    saldo = sum([t.get("monto", 0) for t in ultimas_trans]) if ultimas_trans else 0
    
    # Datos del cliente
    datos = f"DATOS: {ocupacion}, {edad} años"
    if productos_activos:
        datos += f" | Productos: {', '.join(productos_activos)}"
    if saldo > 0:
        datos += f" | Saldo aprox: ${saldo:,.0f}"
    
    return f"""Eres Havi. Cliente identificado.
{datos}

RESPONDE EXACTAMENTE lo que pregunten:
- Si preguntan SALDO → di el monto
- Si preguntan PRODUCTOS → lista los productos
- Si preguntan TRANSACCIONES → explica movimientos
- Si preguntan BENEFICIOS → menciona Hey Pro o features

NUNCA: tarjetas, PINs, contraseñas, códigos.

Sé directo, natural, en español."""


def chat_with_groq(message: str, system_prompt: str) -> str:
    """Obtener respuesta de Groq."""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error Groq: {str(e)}"


# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    """Health check."""
    return {"status": "✅ Backend Hey Banco activo"}


@app.get("/users")
def list_users():
    """Lista de usuarios."""
    return {"count": len(clientes), "users": clientes["user_id"].unique().tolist()}


@app.get("/users/{user_id}/profile")
def get_profile(user_id: str):
    """Obtener perfil del usuario."""
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    return profile


@app.get("/users/{user_id}/cluster")
def get_cluster(user_id: str):
    """Predecir cluster del usuario."""
    # Validar que existe el usuario
    if user_id not in clientes["user_id"].values:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    
    cluster = predict_user_cluster(user_id)
    if cluster is None:
        raise HTTPException(status_code=500, detail="Error prediciendo cluster")
    
    cluster_info = {}
    if clustering_model:
        cluster_names = clustering_model.get('cluster_names', {})
        cluster_info['name'] = cluster_names.get(cluster, f"Cluster {cluster}")
    
    if cluster_profiles:
        cluster_info['profile'] = cluster_profiles.get(cluster, {})
    
    return {
        "user_id": user_id,
        "cluster": cluster,
        "info": cluster_info
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: MessageRequest):
    """Enviar mensaje y obtener respuesta (con contexto de conversación y clustering)."""
    
    profile = None
    user_name = None
    cluster = None
    
    # DEBUG: Mostrar qué recibimos
    print(f"\n📨 MENSAJE RECIBIDO:")
    print(f"   Mensaje: {request.message[:50]}...")
    print(f"   User ID enviado: {request.user_id}")
    
    # Cargar perfil si hay user_id
    if request.user_id:
        print(f"   → Buscando perfil de {request.user_id}...")
        profile = get_user_profile(request.user_id)
        if profile:
            print(f"   ✅ Perfil encontrado: {profile.get('ocupacion')}, {profile.get('edad')} años")
            print(f"   ✅ Productos: {profile.get('productos_activos')}")
            user_name = profile.get("nombre")
            # Predecir cluster del usuario
            cluster = predict_user_cluster(request.user_id)
            print(f"   ✅ Cluster predicho: {cluster}")
        else:
            print(f"   ❌ Usuario NO encontrado en BD")
    else:
        print(f"   → Sin user_id → respondiendo como usuario anónimo")
    
    # Construir system prompt (con perfil y cluster)
    system_prompt = build_system_prompt(profile, cluster)
    print(f"   → Modo: {'IDENTIFICADO' if profile else 'ANÓNIMO'}")
    
    # Preparar mensajes: histórico + mensaje actual
    messages = []
    
    # Agregar histórico de conversación
    if request.conversation_history:
        messages.extend(request.conversation_history)
    
    # Agregar mensaje actual
    messages.append({"role": "user", "content": request.message})
    
    # Obtener respuesta de Groq
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.7,
            max_tokens=150
        )
        response_text = response.choices[0].message.content
        print(f"   ✅ Groq respondió: {response_text[:60]}...")
    except Exception as e:
        response_text = f"❌ Error: {str(e)}"
        print(f"   ❌ Error Groq: {e}")
    
    return ChatResponse(response=response_text, user_name=user_name)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
