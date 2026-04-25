from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import pandas as pd
import os
from dotenv import load_dotenv
from typing import Optional, Dict, List

load_dotenv()

# Inicializar FastAPI
app = FastAPI(title="Hey Banco - Havi Backend")

# Inicializar Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY no encontrada en .env")
groq_client = Groq(api_key=GROQ_API_KEY)

# Cargar datasets
print("Cargando datasets...")
try:
    clientes = pd.read_csv("data/hey_clientes.csv")
    productos = pd.read_csv("data/hey_productos.csv")
    transacciones = pd.read_csv("data/hey_transacciones.csv")
    print(f"✅ Datasets cargados: {len(clientes)} clientes")
    print(f"   Primer usuario: {clientes['user_id'].iloc[0]}")
except FileNotFoundError as e:
    print(f"❌ Error cargando datasets: {e}")

# Modelos Pydantic
class MessageRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    user_name: str

# ==================== FUNCIONES ====================

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Obtener perfil completo del usuario desde los CSVs."""
    try:
        # Buscar cliente
        cliente = clientes[clientes["user_id"] == user_id]
        if cliente.empty:
            return None
        
        cliente_data = cliente.iloc[0].to_dict()
        
        # Obtener productos activos
        productos_usuario = productos[productos["user_id"] == user_id]
        if not productos_usuario.empty:
            productos_activos_df = productos_usuario[
                (productos_usuario["estatus"].str.lower() == "activo") | 
                (productos_usuario["estatus"].str.lower() == "vigente")
            ]
            productos_activos = productos_activos_df["tipo_producto"].tolist()
        else:
            productos_activos = []
        
        # Obtener últimas 5 transacciones
        trans_usuario = transacciones[transacciones["user_id"] == user_id]
        if not trans_usuario.empty:
            trans_usuario_copy = trans_usuario.copy()
            trans_usuario_copy["fecha_hora"] = pd.to_datetime(trans_usuario_copy["fecha_hora"], errors='coerce')
            ultimas_5_trans = trans_usuario_copy.nlargest(5, "fecha_hora")[
                ["fecha_hora", "tipo_operacion", "monto", "descripcion_libre"]
            ].to_dict(orient="records")
        else:
            ultimas_5_trans = []
        
        cliente_data["productos_activos"] = productos_activos
        cliente_data["ultimas_transacciones"] = ultimas_5_trans
        
        return cliente_data
    except Exception as e:
        print(f"Error obteniendo perfil: {e}")
        return None


def build_system_prompt(user_profile: Dict) -> str:
    """Construir system prompt dinámico basado en el perfil del usuario."""
    
    nombre = user_profile.get("nombre", "Cliente")
    edad = user_profile.get("edad", "N/A")
    es_hey_pro = user_profile.get("es_hey_pro", False)
    score_buro = user_profile.get("score_buro", 600)
    satisfaccion = user_profile.get("satisfaccion_1_10", 7)
    patron_atipico = user_profile.get("patron_uso_atipico", False)
    productos = user_profile.get("productos_activos", [])
    
    base_prompt = f"""Eres Havi, un asistente bancario experto de Hey Banco, especializado en atención al cliente.

INFORMACIÓN DEL CLIENTE:
- Nombre: {nombre}
- Edad: {edad}
- Productos activos: {', '.join(productos) if productos else 'Ninguno'}
- Score Buró: {score_buro}
- Satisfacción anterior: {satisfaccion}/10

INSTRUCCIONES:
1. Responde SIEMPRE en español
2. Sé profesional, empático y resolutivo
3. Ofrece soluciones que se alineen con el perfil del cliente
4. Mantén un tono cálido y accesible

COMPORTAMIENTO DINÁMICO:"""
    
    if es_hey_pro:
        base_prompt += "\n- El cliente es Hey Pro: Menciona beneficios exclusivos, cashback y ofertas premium."
    else:
        base_prompt += "\n- El cliente no es Hey Pro: Sugiere los beneficios de actualizar a Hey Pro si es relevante."
    
    if patron_atipico:
        base_prompt += "\n- ⚠️ ALERTA DE SEGURIDAD: El cliente tiene un patrón de uso atípico. Menciona protecciones de fraude si surge en la conversación."
    
    if score_buro < 600:
        base_prompt += f"\n- Score Buró bajo ({score_buro}): Sé cuidadoso. No ofrezcas crédito adicional. Enfócate en educación financiera."
    
    if satisfaccion < 6:
        base_prompt += f"\n- Satisfacción previa baja ({satisfaccion}/10): Adopta un tono EXTRA empático y resolutivo. Busca resolver problemas rápidamente."
    
    return base_prompt


def chat_with_groq(user_message: str, system_prompt: str) -> str:
    """Enviar mensaje a Groq y obtener respuesta."""
    try:
        # Usar modelo de mejor calidad disponible
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al conectar con Groq: {str(e)}"


# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    """Health check."""
    return {"status": "✅ Backend Hey Banco activo"}


@app.get("/users")
def list_users():
    """Obtener lista de usuarios disponibles."""
    try:
        user_list = clientes["user_id"].unique().tolist()
        return {"count": len(user_list), "users": user_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/profile")
def get_profile(user_id: str):
    """Obtener perfil del usuario."""
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    return profile


@app.post("/chat", response_model=ChatResponse)
def chat(request: MessageRequest):
    """Enviar mensaje y obtener respuesta personalizada de Havi."""
    
    # Obtener perfil del usuario
    profile = get_user_profile(request.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Usuario {request.user_id} no encontrado")
    
    # Construir system prompt
    system_prompt = build_system_prompt(profile)
    
    # Obtener respuesta de Groq
    response = chat_with_groq(request.message, system_prompt)
    
    return ChatResponse(
        response=response,
        user_name=profile.get("nombre", "Cliente")
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
