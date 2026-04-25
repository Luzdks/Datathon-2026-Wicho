import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("📊 VERIFICANDO DATOS Y MODELOS")
print("=" * 60)

# 1. Verificar usuarios en CSV
print("\n📁 Usuarios en CSV:")
try:
    clientes = pd.read_csv("data/hey_clientes.csv")
    usuarios = clientes["user_id"].unique()[:10]  # Primeros 10
    print(f"✅ Total de usuarios: {len(clientes)}")
    print(f"Primeros usuarios: {list(usuarios)}")
except Exception as e:
    print(f"❌ Error: {e}")

# 2. Verificar modelos disponibles en Groq
print("\n🤖 Modelos disponibles en Groq:")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    try:
        url = "https://api.groq.com/openai/v1/models"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            models = response.json().get("data", [])
            print(f"✅ Modelos disponibles ({len(models)}):")
            for model in models:
                model_id = model.get("id", "?")
                print(f"   • {model_id}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ GROQ_API_KEY no configurada")

print("\n" + "=" * 60)
