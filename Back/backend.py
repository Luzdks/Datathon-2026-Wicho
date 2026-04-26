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
TRANS_DIR = os.path.join(DATA_DIR, "dataset_transacciones")
MODELS_DIR = os.path.join(BASE_DIR, "Back", "models")

try:
    clientes = pd.read_csv(os.path.join(DATA_DIR, "hey_clientes.csv"))
    productos = pd.read_csv(os.path.join(DATA_DIR, "hey_productos.csv"))
    transacciones = pd.read_csv(os.path.join(DATA_DIR, "hey_transacciones.csv"))
    print(f"✅ Datasets cargados: {len(clientes)} clientes")
    print(f"   Primer usuario: {clientes['user_id'].iloc[0]}")
except FileNotFoundError as e:
    print(f"❌ Error cargando datasets: {e}")

# Cargar clusters del nuevo modelo (ModeloClustersUsuarios.ipynb)
user_clusters = {}
try:
    df_clusters = pd.read_csv(os.path.join(TRANS_DIR, "hey_clientes_perfil_completo_final.csv"))
    user_clusters = dict(zip(df_clusters['user_id'], df_clusters['cluster']))
    print(f"✅ Clusters cargados: {len(user_clusters)} usuarios clasificados")
    print(f"   Grupos: {sorted(set(user_clusters.values()))}")
except FileNotFoundError:
    print("⚠️ CSV de clusters no encontrado. Clustering no disponible.")

# Cargar modelo de clustering legacy (fallback)
clustering_model = None
cluster_profiles = None
try:
    with open(os.path.join(MODELS_DIR, "clustering_model.pkl"), 'rb') as f:
        clustering_model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "cluster_profiles.pkl"), 'rb') as f:
        cluster_profiles = pickle.load(f)
    print(f"✅ Modelo de clustering legacy cargado")
except FileNotFoundError:
    print("⚠️ Modelo de clustering legacy no encontrado.")

# Modelos Pydantic
class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_history: List[Dict] = []

class ChatResponse(BaseModel):
    response: str
    user_name: Optional[str] = None
    cluster: Optional[str] = None

# ==================== FUNCIONES ====================

def clean_nan(obj):
    """Reemplaza NaN/inf por None para que JSON no truene."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(i) for i in obj]
    try:
        import math
        if obj != obj:  # NaN
            return None
        if isinstance(obj, float) and (math.isinf(obj) or math.isnan(obj)):
            return None
    except:
        pass
    return obj


def get_user_profile(user_id: str) -> Optional[Dict]:
    """Obtener perfil del usuario desde CSV."""
    if user_id not in clientes["user_id"].values:
        return None

    cliente_data = clientes[clientes["user_id"] == user_id].iloc[0].to_dict()
    cliente_data = clean_nan(cliente_data)

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


def get_user_cluster_name(user_id: str) -> Optional[str]:
    """Obtener el nombre del cluster del nuevo modelo (CSV)."""
    return user_clusters.get(user_id)


def predict_user_cluster(user_id: str) -> Optional[int]:
    """Predecir el cluster de un usuario (legacy, como fallback)."""
    if not clustering_model:
        return None

    try:
        cliente = clientes[clientes["user_id"] == user_id].copy()
        if cliente.empty:
            return None

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

        feature_cols = clustering_model['feature_columns']
        missing_cols = [col for col in feature_cols if col not in cliente.columns]
        if missing_cols:
            print(f"⚠️ Features faltantes para {user_id}: {missing_cols}")
            return None

        X_user = cliente[feature_cols].values
        X_scaled = clustering_model['scaler'].transform(X_user)
        embedding = clustering_model['pca'].transform(X_scaled)
        cluster = clustering_model['kmeans'].predict(embedding)[0]
        return int(cluster)
    except Exception as e:
        print(f"❌ Error prediciendo cluster para {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_cluster_strategy(cluster_name: str) -> str:
    """Devuelve la estrategia de atención personalizada según el cluster."""
    strategies = {
        "Jóvenes digitales": (
            "ESTRATEGIA DE ATENCIÓN – Jóvenes Digitales:\n"
            "- Usa lenguaje fresco, emojis y referencias digitales.\n"
            "- Promueve la app, notificaciones push y beneficios de Hey Pro.\n"
            "- Ofrece créditos estudiantiles, tarjetas de débito con diseños personalizados y educación financiera gamificada.\n"
            "- Sugiere automatización de ahorros y retos de ahorro."
        ),
        "Cliente poco activo": (
            "ESTRATEGIA DE ATENCIÓN – Cliente Poco Activo:\n"
            "- Se proactivo y cálido; reactiva la relación con beneficios claros.\n"
            "- Ofrece promociones de bienvenida, cashback en compras del día a día y facilidades para usar la app.\n"
            "- Sugiere productos de bajo mantenimiento (cuenta base, débito sin comisiones).\n"
            "- Menciona seguridad y simplicidad como ventajas."
        ),
        "Cliente premium": (
            "ESTRATEGIA DE ATENCIÓN – Cliente Premium:\n"
            "- Trátalo con exclusividad; usa términos como 'beneficios exclusivos', 'atención preferencial'.\n"
            "- Ofrece productos de inversión, asesoría patrimonial, seguros premium y líneas de crédito altas.\n"
            "- Destaca experiencias, lounge access, concierge y promociones en restauranteras y viajes.\n"
            "- Sé breve pero sofisticado."
        ),
        "Empleado de nómina domiciliada": (
            "ESTRATEGIA DE ATENCIÓN – Empleado Nómina:\n"
            "- Destaca la seguridad, estabilidad y beneficios de tener la nómina en Hey Banco.\n"
            "- Ofrece préstamos pre-aprobados, adelanto de nómina y planes de ahorro automáticos.\n"
            "- Sugiere seguros de vida, gastos médicos mayores y fondos de emergencia.\n"
            "- Usa un tono confiable y familiar."
        ),
        "Profesionalista de alto ingreso": (
            "ESTRATEGIA DE ATENCIÓN – Profesionalista Alto Ingreso:\n"
            "- Sé consultivo y profesional; ofrece soluciones de crecimiento patrimonial.\n"
            "- Promueve inversiones, fondos de inversión, CETES, afores y planificación fiscal.\n"
            "- Sugiere tarjetas de crédito platinum/infinite con altos límites y seguros de viaje.\n"
            "- Destaca herramientas de análisis de gastos y reportes de inversión."
        ),
    }
    return strategies.get(cluster_name, "")


def build_system_prompt(profile: Optional[Dict] = None, cluster_name: Optional[str] = None, insights_text: str = "") -> str:
    """System prompt dinámico basado en perfil, cluster e insights."""

    # ===== SIN IDENTIFICACIÓN =====
    if not profile:
        return """Eres Havi, asistente de Hey Banco. Mexicana, cálida, directa.

Máximo 2-3 oraciones por respuesta. Guía paso a paso. No des toda la info de golpe.

Si preguntan datos personales/saldo → pide USR-XXXXX.
NUNCA pidas tarjetas, PINs, contraseñas.

Usa emojis ocasionales 😊. Tono natural."""

    # ===== CON IDENTIFICACIÓN =====
    ocupacion = profile.get("ocupacion", "Usuario").title()
    edad = profile.get("edad", "?")
    productos_activos = profile.get("productos_activos", [])
    ultimas_trans = profile.get("ultimas_transacciones", [])

    # Calcular saldo aproximado
    saldo = sum([t.get("monto", 0) for t in ultimas_trans]) if ultimas_trans else 0

    # Formatear transacciones
    transacciones_texto = ""
    if ultimas_trans:
        transacciones_texto = "\nÚLTIMAS TRANSACCIONES:\n"
        for i, t in enumerate(ultimas_trans[:5], 1):
            fecha = str(t.get('fecha_hora', 'N/A'))
            tipo = t.get('tipo_operacion', 'N/A')
            monto = t.get('monto', 0)
            desc = t.get('descripcion_libre', '')
            transacciones_texto += f"  {i}. {fecha} | {tipo} | ${monto:,.2f} | {desc}\n"

    datos = f"DATOS: {ocupacion}, {edad} años"
    if productos_activos:
        datos += f" | Productos: {', '.join(productos_activos)}"
    if saldo > 0:
        datos += f" | Saldo aprox: ${saldo:,.0f}"
    if transacciones_texto:
        datos += transacciones_texto

    # Estrategia de atención por cluster
    cluster_strategy = get_cluster_strategy(cluster_name) if cluster_name else ""

    return f"""Eres Havi, asistente de Hey Banco. Mexicana, cálida, directa.

DATOS DEL CLIENTE:
{datos}{insights_text}

{cluster_strategy}

REGLAS:
- Máximo 2-3 oraciones por respuesta. Guía paso a paso. No des todo de golpe.
- Si preguntan saldo/productos/transacciones → responde con los datos de arriba directamente.
- NUNCA digas "no tengo acceso" sobre info que SÍ está en el contexto.
- NUNCA pidas tarjetas, PINs, contraseñas, CVV.
- Usa emojis ocasionales 😊. Tono natural."""


import re

def generate_insights(profile: Dict, cluster: Optional[int]) -> str:
    """
    Genera insights automáticos a partir del perfil y transacciones del usuario.
    Esto convierte a Havi en un motor de inteligencia que detecta patrones
    y necesidades implícitas.
    """
    insights = []
    ultimas_trans = profile.get("ultimas_transacciones", [])
    productos = profile.get("productos_activos", [])
    ocupacion = profile.get("ocupacion", "Usuario").title()
    edad = profile.get("edad", "?")

    # 1. Análisis de transacciones
    if ultimas_trans:
        tipos = {}
        monto_total = 0
        for t in ultimas_trans:
            tipo = t.get("tipo_operacion", "OTRO")
            tipos[tipo] = tipos.get(tipo, 0) + 1
            monto_total += t.get("monto", 0)

        tipo_frecuente = max(tipos, key=tipos.get) if tipos else "N/A"
        monto_promedio = monto_total / len(ultimas_trans) if ultimas_trans else 0

        insights.append(f"PATRÓN DE USO: Realiza principalmente operaciones de '{tipo_frecuente}'. "
                       f"Monto promedio por transacción: ${monto_promedio:,.2f}.")

        # Detectar necesidad implícita basada en transacciones
        if monto_promedio > 5000 and "tarjeta de crédito" not in [p.lower() for p in productos]:
            insights.append("NECESIDAD IMPLÍCITA: Sus montos de transacción son elevados. "
                           "Podría beneficiarse de una tarjeta de crédito con cashback o meses sin intereses.")

        if len(ultimas_trans) >= 5 and "inversión" not in [p.lower() for p in productos]:
            insights.append("NECESIDAD IMPLÍCITA: Alta frecuencia de movimientos. "
                           "Una cuenta de inversión o fondo podría ayudarle a hacer crecer su dinero.")

    # 2. Análisis de productos
    if not productos:
        insights.append("NECESIDAD IMPLÍCITA: No tiene productos activos. Es candidato ideal para una cuenta base o Hey Pro.")
    elif len(productos) == 1:
        insights.append(f"PATRÓN DE PRODUCTOS: Solo tiene {productos[0]}. Hay oportunidad de cross-selling con productos complementarios.")

    # 3. Insights del cluster (segmentación)
    if cluster is not None and cluster_profiles:
        cp = cluster_profiles.get(cluster, {})
        cluster_name = cp.get("name", f"Cluster {cluster}")
        cluster_desc = cp.get("description", "")
        if cluster_desc:
            insights.append(f"SEGMENTO: Pertenece al grupo '{cluster_name}'. {cluster_desc}")
        else:
            insights.append(f"SEGMENTO: Pertenece al grupo '{cluster_name}'.")

    # 4. Insights por edad y ocupación
    try:
        edad_int = int(edad)
        if edad_int < 30 and "crédito" not in [p.lower() for p in productos]:
            insights.append("NECESIDAD IMPLÍCITA: Perfil joven. Puede estar interesado en su primer crédito o tarjeta de crédito estudiantil.")
        elif edad_int > 50 and "inversión" not in [p.lower() for p in productos]:
            insights.append("NECESIDAD IMPLÍCITA: Perfil maduro. Podría estar interesado en productos de ahorro para el retiro o inversiones conservadoras.")
    except:
        pass

    if not insights:
        return ""

    return "\n\nINSIGHTS DEL MOTOR DE INTELIGENCIA (usa estos para personalizar tus respuestas y ser proactiva):\n" + "\n".join([f"• {i}" for i in insights])


def handle_data_query(message: str, profile: Dict) -> Optional[str]:
    """
    Detecta si el usuario pregunta por datos específicos de su perfil
    y responde DIRECTAMENTE con los datos del CSV, sin pasar por Groq.
    Esto evita que el LLM se ponga conservador.
    """
    msg_lower = message.lower()

    # ----- SALDO -----
    if any(p in msg_lower for p in ["saldo", "cuánto tengo", "cuanto tengo", "dinero en cuenta", "mi dinero"]):
        ultimas_trans = profile.get("ultimas_transacciones", [])
        saldo = sum([t.get("monto", 0) for t in ultimas_trans]) if ultimas_trans else 0
        if saldo > 0:
            return f"Tu saldo aproximado es de **${saldo:,.2f}** 💰"
        else:
            return "No tengo registrado un saldo activo en tu cuenta. ¿Quizás quieras revisar tus movimientos recientes?"

    # ----- PRODUCTOS -----
    if any(p in msg_lower for p in ["productos", "qué tengo", "que tengo", "mis cuentas", "mis tarjetas", "servicios contratados"]):
        productos = profile.get("productos_activos", [])
        ocupacion = profile.get("ocupacion", "Usuario").title()
        if productos:
            lista = "\n".join([f"  • {p}" for p in productos])
            return f"Estos son tus productos activos, **{ocupacion}** 😊:\n\n{lista}\n\n¿Te gustaría saber más sobre alguno en particular?"
        else:
            return f"Actualmente no tienes productos activos registrados. Si quieres, te puedo ayudar a explorar opciones como Hey Pro, tarjetas de crédito o cuentas de ahorro."

    # ----- TRANSACCIONES / MOVIMIENTOS -----
    if any(p in msg_lower for p in ["transacciones", "movimientos", "últimos movimientos", "ultimos movimientos", "última transacción", "ultima transaccion", "qué compré", "que compre", "qué gasté", "que gaste", "qué movimientos", "que movimientos"]):
        ultimas_trans = profile.get("ultimas_transacciones", [])
        if ultimas_trans:
            # Si pregunta específicamente por LA ÚLTIMA (singular o "primera" / "más reciente")
            if any(p in msg_lower for p in ["última", "ultima", "primera", "más reciente", "mas reciente", "la más reciente", "la mas reciente", "reciente"]):
                t = ultimas_trans[0]
                fecha = str(t.get('fecha_hora', 'N/A'))
                tipo = t.get('tipo_operacion', 'N/A')
                monto = t.get('monto', 0)
                desc = t.get('descripcion_libre', 'Sin descripción')
                return f"Tu última transacción fue:\n\n📅 **Fecha:** {fecha}\n💳 **Tipo:** {tipo}\n💰 **Monto:** ${monto:,.2f}\n📝 **Descripción:** {desc}\n\n¿Quieres ver más movimientos?"

            # Respuesta general con lista de las últimas 5
            lines = ["Aquí están tus últimas transacciones 📊:\n"]
            for i, t in enumerate(ultimas_trans[:5], 1):
                fecha = str(t.get('fecha_hora', 'N/A')).split('.')[0]  # quitar microsegundos
                tipo = t.get('tipo_operacion', 'N/A')
                monto = t.get('monto', 0)
                desc = t.get('descripcion_libre', '')
                lines.append(f"{i}. {fecha} | {tipo} | ${monto:,.2f} | {desc}")
            lines.append("\n¿Hay alguna transacción en la que quieras profundizar?")
            return "\n".join(lines)
        else:
            return "No tengo transacciones registradas para tu cuenta en este momento."

    # ----- PERFIL (edad, ocupación) -----
    if any(p in msg_lower for p in ["mi perfil", "mi edad", "mi ocupación", "mi ocupacion", "a qué me dedico", "a que me dedico", "quién soy", "quien soy"]):
        ocupacion = profile.get("ocupacion", "no registrada").title()
        edad = profile.get("edad", "?")
        return f"Según tu perfil, eres **{ocupacion}** y tienes **{edad} años** 🙋‍♀️. ¿Te gustaría que te diera recomendaciones basadas en tu perfil?"

    # No es una pregunta de datos → retornar None para que pase al Groq
    return None


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
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error Groq: {str(e)}"


# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    return {"status": "✅ Backend Hey Banco activo"}


@app.get("/users")
def list_users():
    return {"count": len(clientes), "users": clientes["user_id"].unique().tolist()}


@app.get("/users/{user_id}/profile")
def get_profile(user_id: str):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    return profile


@app.get("/users/{user_id}/cluster")
def get_cluster(user_id: str):
    if user_id not in clientes["user_id"].values:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")

    # Intentar obtener del nuevo modelo (CSV) primero
    cluster_name = get_user_cluster_name(user_id)
    if cluster_name:
        return {"user_id": user_id, "cluster": cluster_name, "source": "modelo_nuevo", "info": {"name": cluster_name}}

    # Fallback al modelo legacy
    cluster = predict_user_cluster(user_id)
    if cluster is None:
        raise HTTPException(status_code=500, detail="Error prediciendo cluster")

    cluster_info = {}
    if clustering_model:
        cluster_names = clustering_model.get('cluster_names', {})
        cluster_info['name'] = cluster_names.get(cluster, f"Cluster {cluster}")

    if cluster_profiles:
        cluster_info['profile'] = cluster_profiles.get(cluster, {})

    return {"user_id": user_id, "cluster": cluster, "source": "legacy", "info": cluster_info}


@app.post("/chat", response_model=ChatResponse)
def chat(request: MessageRequest):
    profile = None
    user_name = None
    cluster = None

    print(f"\n📨 MENSAJE RECIBIDO:")
    print(f"   Mensaje: {request.message[:50]}...")
    print(f"   User ID enviado: {request.user_id}")

    cluster_name = None
    if request.user_id:
        print(f"   → Buscando perfil de {request.user_id}...")
        profile = get_user_profile(request.user_id)
        if profile:
            print(f"   ✅ Perfil encontrado")
            user_name = profile.get("nombre")
            cluster = predict_user_cluster(request.user_id)
            cluster_name = get_user_cluster_name(request.user_id)
            if cluster_name:
                print(f"   ✅ Cluster (nuevo modelo): {cluster_name}")
        else:
            print(f"   ❌ Usuario NO encontrado en BD")
    else:
        print(f"   → Sin user_id → respondiendo como usuario anónimo")

    # Si el usuario está identificado y hace una pregunta de datos,
    # respondemos DIRECTAMENTE desde el CSV sin pasar por Groq.
    insights_text = ""
    if profile:
        direct_response = handle_data_query(request.message, profile)
        if direct_response:
            print(f"   ✅ Respuesta directa (datos del perfil)")
            return ChatResponse(response=direct_response, user_name=user_name, cluster=cluster_name)

        # Generar insights del motor de inteligencia para enriquecer el prompt
        insights_text = generate_insights(profile, cluster)

    system_prompt = build_system_prompt(profile, cluster_name, insights_text)
    print(f"   → Modo: {'IDENTIFICADO' if profile else 'ANÓNIMO'}")

    messages = []
    if request.conversation_history:
        messages.extend(request.conversation_history)
    messages.append({"role": "user", "content": request.message})

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.7,
            max_tokens=250
        )
        response_text = response.choices[0].message.content
        print(f"   ✅ Groq respondió: {response_text[:60]}...")
    except Exception as e:
        response_text = f"❌ Error: {str(e)}"
        print(f"   ❌ Error Groq: {e}")

    return ChatResponse(response=response_text, user_name=user_name, cluster=cluster_name)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

