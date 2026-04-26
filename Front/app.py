import streamlit as st
import requests
import re
import time

# URL del backend (FastAPI)
BACKEND_URL = "http://localhost:8000"

# Configuración de la página
st.set_page_config(
    page_title="Havi - Hey Banco",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Suprimir warnings de Streamlit
import warnings
warnings.filterwarnings("ignore")

# ==================== ESTILOS CSS ====================
st.markdown("""
<style>
    /* General */
    * { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { margin: 0; padding: 0; background: #f8f9fa; }

    /* Ocultar elementos default de Streamlit */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 0 !important; }

    /* Header */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px 20px;
        border-radius: 0 0 20px 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }

    .header h1 {
        margin: 0;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .header p {
        margin: 8px 0 0 0;
        font-size: 13px;
        opacity: 0.9;
        font-weight: 500;
    }

    /* Status bar */
    .status-bar {
        background: white;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 16px;
        border-left: 4px solid #667eea;
        font-size: 13px;
        color: #555;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .status-bar.connected { border-left-color: #10b981; }

    /* Chat messages */
    .chat-container {
        padding: 0 8px 8px 8px;
    }

    .chat-message {
        margin: 12px 0;
        display: flex;
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .msg-user { justify-content: flex-end; }

    .msg-bubble {
        max-width: 75%;
        padding: 12px 16px;
        border-radius: 16px;
        word-wrap: break-word;
        font-size: 14px;
        line-height: 1.4;
    }

    .bubble-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 4px;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
    }

    .bubble-assistant {
        background: white;
        color: #333;
        border-bottom-left-radius: 4px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    /* User badge */
    .user-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25);
    }
    
    /* Input styling */
    input { border-radius: 25px !important; }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_cluster" not in st.session_state:
    st.session_state.user_cluster = None
if "voice_processed" not in st.session_state:
    st.session_state.voice_processed = None
# FIX BUG 3: guardamos mensaje pendiente para sobrevivir el rerun de identificación
if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

# ==================== VERIFICAR BACKEND ====================
try:
    response = requests.get(f"{BACKEND_URL}/", timeout=2)
    backend_active = response.status_code == 200
except:
    backend_active = False

# ==================== HEADER ====================
st.markdown("""
<div class="header">
    <h1>Havi</h1>
    <p>Tu asistente de Hey Banco</p>
</div>
""", unsafe_allow_html=True)

# ==================== STATUS BAR ====================
status_text = "✓ Conectado" if backend_active else "✗ Error: Backend no disponible"
status_class = "connected" if backend_active else ""
st.markdown(f'<div class="status-bar {status_class}">{status_text}</div>', unsafe_allow_html=True)

if not backend_active:
    st.error("Backend no está activo. Ejecuta: python backend.py")
    st.stop()

# ==================== BADGE DE USUARIO ====================
if st.session_state.user_id:
    cluster_text = f" • {st.session_state.user_cluster}" if st.session_state.user_cluster else ""
    st.markdown(
        f'<div class="user-badge">Identificado: {st.session_state.user_name}{cluster_text}</div>',
        unsafe_allow_html=True
    )

# ==================== CHAT DISPLAY ====================
# FIX BUG 2: container con altura fija = scroll interno, página no se mueve
chat_area = st.container(height=430, border=False)

with chat_area:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
<div class="chat-message">
    <div class="msg-bubble bubble-assistant">
        ¡Hola! Soy Havi 👋 Ingresa tu ID de usuario (USR-XXXXX) para comenzar.
    </div>
</div>
""", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'''
<div class="chat-message msg-user">
    <div class="msg-bubble bubble-user">{msg["content"]}</div>
</div>
''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
<div class="chat-message">
    <div class="msg-bubble bubble-assistant">{msg["content"]}</div>
</div>
''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== INPUT AREA ====================
# Usar st.chat_input que es el nativo y mejor de Streamlit
col_input, col_voice = st.columns([6, 1], gap="small")

with col_input:
    user_input = st.chat_input("Escribe o ingresa USR-XXXXX...")

with col_voice:
    try:
        audio_bytes = st.audio_input("Label", label_visibility="hidden")
    except:
        audio_bytes = None

# ==================== PROCESAR VOZ ====================
voice_message = None
if audio_bytes and st.session_state.voice_processed != id(audio_bytes):
    st.session_state.voice_processed = id(audio_bytes)
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes, sample_rate=16000, sample_width=2)
        voice_message = recognizer.recognize_google(audio_data, language="es-ES")
    except Exception as e:
        pass  # Silenciar errores de voz

# Voz tiene prioridad si no hay texto escrito
final_input = user_input or voice_message

# ==================== LÓGICA PRINCIPAL ====================
if final_input and final_input.strip():
    msg = final_input.strip()

    # ¿Es un user_id?
    if re.match(r'^USR-\d{5}$', msg, re.IGNORECASE):
        user_id = msg.upper()
        try:
            resp = requests.get(f"{BACKEND_URL}/users/{user_id}/profile", timeout=5)
            if resp.status_code == 200:
                profile = resp.json()
                ocupacion = profile.get("ocupacion", "Usuario").title()
                edad = profile.get("edad", "?")

                st.session_state.user_id = user_id
                st.session_state.user_name = f"{ocupacion}, {edad} años"

                # Obtener cluster
                try:
                    cr = requests.get(f"{BACKEND_URL}/users/{user_id}/cluster", timeout=5)
                    if cr.status_code == 200:
                        st.session_state.user_cluster = cr.json().get("info", {}).get("name", "")
                except:
                    pass

                # NO hacer rerun, simplemente guardar en historial y continuar
                if not st.session_state.messages or st.session_state.messages[-1]["role"] != "assistant":
                    bienvenida = "¡Te identifiqué! Soy Havi, tu asistente personal de Hey Banco. ¿En qué te puedo ayudar hoy?"
                    st.session_state.messages.append({"role": "assistant", "content": bienvenida})

            else:
                st.error(f"Usuario {user_id} no encontrado.")
        except Exception as e:
            st.error(f"Error conectando al backend: {str(e)}")

    else:
        # ==================== MENSAJE NORMAL AL BOT ====================
        if not st.session_state.user_id:
            st.error("Primero identifícate con tu usuario (USR-XXXXX)")
        else:
            st.session_state.messages.append({"role": "user", "content": msg})

            # Mostrar "escribiendo..." dentro del área de chat
            with chat_area:
                typing_placeholder = st.empty()
                typing_placeholder.markdown('''
<div class="chat-message">
    <div class="msg-bubble bubble-assistant"><em>Escribiendo...</em></div>
</div>
''', unsafe_allow_html=True)

            try:
                conversation_history = st.session_state.messages[:-1]

                resp = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "message": msg,
                        "user_id": st.session_state.user_id,
                        "conversation_history": conversation_history
                    },
                    timeout=30
                )

                if resp.status_code == 200:
                    assistant_message = resp.json().get("response", "Sin respuesta")
                else:
                    assistant_message = "Hubo un error en el servidor. Intenta de nuevo."

            except requests.Timeout:
                assistant_message = "El servidor tardó demasiado. Intenta de nuevo."
            except Exception as e:
                assistant_message = f"Error de conexión: {str(e)}"

            # Efecto de escritura letra por letra dentro del área de chat
            with chat_area:
                typing_placeholder.empty()
                msg_placeholder = st.empty()
                displayed_text = ""

                for char in assistant_message:
                    displayed_text += char
                    msg_placeholder.markdown(f'''
<div class="chat-message">
    <div class="msg-bubble bubble-assistant">{displayed_text}▌</div>
</div>
''', unsafe_allow_html=True)
                    time.sleep(0.015)

                # Quitar cursor parpadeante al terminar
                msg_placeholder.empty()

            # Guardar en historial y rerenderizar limpio
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            st.rerun()