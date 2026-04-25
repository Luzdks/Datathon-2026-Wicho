import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict

# URL del backend (FastAPI)
BACKEND_URL = "http://localhost:8000"

# Configuración de la página
st.set_page_config(
    page_title="🏦 Chatbot Hey Banco",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .chat-message {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 14px;
    }
    .user-message {
        background-color: #e8f4f8;
        text-align: right;
        margin-left: 30%;
    }
    .assistant-message {
        background-color: #f0f0f0;
        margin-right: 30%;
    }
    .profile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .stat-box {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #667eea;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR: LOGIN ====================

st.sidebar.title("🏦 Hey Banco")
st.sidebar.markdown("---")

# Verificar si backend está activo
try:
    response = requests.get(f"{BACKEND_URL}/")
    backend_status = response.status_code == 200
except:
    backend_status = False

if not backend_status:
    st.error("⚠️ Backend no está activo. Ejecuta primero: `python backend.py`")
    st.stop()

# Session state para login
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_profile = None
    st.session_state.user_name = None

st.sidebar.subheader("Iniciar Sesión")

# Cargar lista de usuarios desde el backend
try:
    response = requests.get(f"{BACKEND_URL}/users")
    if response.status_code == 200:
        users_data = response.json()
        available_users = users_data.get("users", [])
    else:
        available_users = []
except:
    available_users = []

if not available_users:
    st.error("❌ No se pudieron cargar los usuarios del backend")
    st.stop()

selected_user = st.sidebar.selectbox(
    f"Selecciona tu usuario ({len(available_users)} disponibles):",
    available_users,
    index=None,
    placeholder="Elige un usuario..."
)

if st.sidebar.button("🔓 Ingresar", use_container_width=True):
    # Intentar cargar perfil del backend
    try:
        response = requests.get(f"{BACKEND_URL}/users/{selected_user}/profile")
        if response.status_code == 200:
            st.session_state.user_id = selected_user
            st.session_state.user_profile = response.json()
            st.session_state.user_name = response.json().get("nombre", "Usuario")
            st.sidebar.success(f"✅ Bienvenido, {st.session_state.user_name}!")
            st.rerun()
        else:
            st.sidebar.error(f"❌ Usuario {selected_user} no encontrado")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("❌ No se puede conectar al backend")
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)}")

# ==================== SIDEBAR: PERFIL DEL USUARIO ====================

if st.session_state.user_profile:
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 Tu Perfil")
    
    profile = st.session_state.user_profile
    
    # Tarjeta de perfil
    st.sidebar.markdown(f"""
    <div class="profile-card">
        <h3 style="margin: 0;">👋 {profile.get('nombre', 'N/A')}</h3>
        <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">ID: {profile.get('user_id', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información
    st.sidebar.markdown(f"""
    <div class="stat-box">
        <strong>Edad:</strong> {profile.get('edad', 'N/A')} años
    </div>
    <div class="stat-box">
        <strong>Ocupación:</strong> {profile.get('ocupacion', 'N/A')}
    </div>
    <div class="stat-box">
        <strong>Ingreso mensual:</strong> ${profile.get('ingreso_mensual_mxn', 0):,.0f} MXN
    </div>
    <div class="stat-box">
        <strong>Estado:</strong> {profile.get('estado', 'N/A')}
    </div>
    """, unsafe_allow_html=True)
    
    # Hey Pro status
    if profile.get("es_hey_pro"):
        st.sidebar.success("✨ **Hey Pro activo**")
    else:
        st.sidebar.info("Upgrade a **Hey Pro** para más beneficios")
    
    # Score Buró
    score = profile.get("score_buro", 0)
    st.sidebar.metric("Score Buró", f"{score}", "")
    
    # Satisfacción
    satisfaccion = profile.get("satisfaccion_1_10", 0)
    st.sidebar.metric("Satisfacción", f"{satisfaccion}/10", "")
    
    # Productos activos
    if profile.get("productos_activos"):
        st.sidebar.markdown("**Productos:**")
        for producto in profile.get("productos_activos", []):
            st.sidebar.write(f"• {producto}")
    
    # Botón logout
    if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.user_profile = None
        st.session_state.user_name = None
        st.rerun()

# ==================== MAIN: CHAT ====================

if not st.session_state.user_id:
    st.info("👈 Selecciona un usuario en el sidebar e ingresa para comenzar")
    st.stop()

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title(f"🤖 Havi - Hey Banco")
st.markdown(f"Chatbot personalizado para {st.session_state.user_name}")
st.markdown("---")

# Mostrar historial de chat
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>Tú:</strong> {msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>Havi:</strong> {msg["content"]}
            </div>
            """, unsafe_allow_html=True)

# Input de usuario
st.markdown("---")

# Usar clave única para evitar reprocessing
if "last_processed_message" not in st.session_state:
    st.session_state.last_processed_message = None

user_input = st.text_input("Escribe tu pregunta:", placeholder="¿Cómo puedo ayudarte?")

if user_input and user_input != st.session_state.last_processed_message:
    # Marcar que ya procesamos este mensaje
    st.session_state.last_processed_message = user_input
    
    # Agregar mensaje del usuario
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Mostrar mensaje del usuario
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>Tú:</strong> {user_input}
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener respuesta del backend
    with st.spinner("🤔 Havi está pensando..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "user_id": st.session_state.user_id,
                    "message": user_input
                }
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                assistant_message = chat_response.get("response", "No se recibió respuesta")
                
                # Agregar respuesta al historial
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                # Mostrar respuesta
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Havi:</strong> {assistant_message}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ No se puede conectar al backend.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
    🏦 Hey Banco - Chatbot Inteligente | Powered by Groq + FastAPI
</div>
""", unsafe_allow_html=True)
