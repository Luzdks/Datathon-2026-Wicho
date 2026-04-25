# 🏦 Hey Banco - Havi Chatbot

Asistente bancario inteligente y personalizado para Hey Banco, construido con Streamlit + FastAPI + Groq.

## 🏗️ Arquitectura
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  FRONTEND (Streamlit)                                           │
│  - Login con selección de usuarios                              │
│  - Interfaz de chat en tiempo real                              │
│  - Visualización de perfil personalizado                        │
│  - Historial de mensajes                                        │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (requests)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  BACKEND (FastAPI)                                              │
│  - Carga datos desde CSVs (clientes, productos, transacciones)  │
│  - Construye system prompt dinámico según perfil del usuario    │
│  - Conecta con API de Groq                                      │
│  - Endpoints: /users, /users/{id}/profile, /chat               │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  GROQ API (IA)                                                  │
│  Modelo: llama-3.3-70b-versatile                                │
│  - Procesa contexto personalizado                               │
│  - Genera respuestas según perfil del cliente                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:
```
GROQ_API_KEY=tu_api_key_aqui
```

### 3. Ejecutar el Backend (FastAPI)
```bash
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: **http://localhost:8000**

### 4. Ejecutar el Frontend (Streamlit) - EN OTRA TERMINAL
```bash
python -m streamlit run app.py
```

El frontend estará disponible en: **http://localhost:8502**

---

## 📊 Datos

### Usuarios
- **Archivo:** `data/hey_clientes.csv`
- **Campos:** user_id, edad, ocupación, ingreso, Hey Pro status, score buró, satisfacción, etc.
- **Total:** 15,025 usuarios reales

### Productos
- **Archivo:** `data/hey_productos.csv`
- **Vinculación:** Por usuario

### Transacciones
- **Archivo:** `data/hey_transacciones.csv`
- **Vinculación:** Por usuario

---

## 💬 Cómo Funciona

1. **Login:** Selecciona un usuario (USR-00001, USR-00002, etc.)
2. **Perfil:** El sistema carga automáticamente:
   - Datos demográficos
   - Productos activos
   - Últimas transacciones
   - Score buró y satisfacción
3. **Chat:** Escribe tu pregunta → Backend construye contexto personalizado → Groq genera respuesta inteligente
4. **Personalización:** Havi adapta su tono y recomendaciones según:
   - Hey Pro status (beneficios exclusivos)
   - Score buró (educación financiera vs ofertas)
   - Nivel de satisfacción (atención empática si es bajo)

---

## 📁 Estructura de Archivos

```
.
├── Front
|   └── app.py                 # Frontend Streamlit
├── Back 
|   └── backend.py             # Backend FastAPI
├── requirements.txt       # Dependencias
├── .env                   # Variables de entorno (no incluido en git)
├── .gitignore            # Configuración de git
├── data/
│   ├── hey_clientes.csv
│   ├── hey_productos.csv
│   └── hey_transacciones.csv
└── README.md
```

---

## 🔌 Endpoints del Backend

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/users` | Lista todos los usuarios disponibles |
| GET | `/users/{user_id}/profile` | Perfil completo de un usuario |
| POST | `/chat` | Enviar mensaje y obtener respuesta |

---

## ✨ Características

✅ **Chat inteligente** - Groq genera respuestas en tiempo real  
✅ **Personalización** - Adapta tono según perfil del cliente  
✅ **Datos reales** - 15,025 usuarios con información completa  
✅ **Productos y transacciones** - Contexto completo del cliente  
✅ **Interfaz moderna** - UI limpia con Streamlit  
✅ **Arquitectura escalable** - Frontend/Backend separados  

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **Backend:** FastAPI (Python)
- **IA:** Groq API (llama-3.3-70b-versatile)
- **Data:** Pandas + CSV
- **Web Server:** Uvicorn

---

## 📝 Notas

- El backend se relaodea automáticamente cuando haces cambios (modo `--reload`)
- Cada usuario tiene un contexto único que se incluye en el system prompt
- Los tokens de Groq se usan solo cuando haces una pregunta (no en loops)

---

**Datathon 2026** 🚀