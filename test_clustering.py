#!/usr/bin/env python3
"""
Script de prueba para validar clustering integration
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
TEST_USER = "USR-00001"

print("=" * 70)
print("🧪 PRUEBAS DE CLUSTERING INTEGRATION")
print("=" * 70)

# Esperar a que el servidor esté listo
print("\n⏳ Esperando que el servidor esté listo...")
for i in range(30):
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Servidor listo")
            break
    except:
        pass
    time.sleep(1)
else:
    print("❌ Servidor no respondió en 30s")
    exit(1)

# Test 1: Get cluster prediction
print(f"\n[1] Prediciendo cluster para {TEST_USER}...")
try:
    response = requests.get(f"{BASE_URL}/users/{TEST_USER}/cluster")
    if response.status_code == 200:
        data = response.json()
        cluster = data['cluster']
        cluster_name = data['info'].get('name', 'Unknown')
        print(f"✅ Cluster {cluster}: {cluster_name}")
        print(f"   Datos: {json.dumps(data['info']['profile'], indent=2)[:200]}...")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Get user profile
print(f"\n[2] Obteniendo perfil de {TEST_USER}...")
try:
    response = requests.get(f"{BASE_URL}/users/{TEST_USER}/profile")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Perfil cargado:")
        print(f"   Nombre: {data.get('nombre')}")
        print(f"   Edad: {data.get('edad')}")
        print(f"   Score Buro: {data.get('score_buro')}")
        print(f"   Es Hey Pro: {data.get('es_hey_pro')}")
        print(f"   Productos: {data.get('productos_activos')}")
    else:
        print(f"❌ Error {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Chat without user (anonymous)
print(f"\n[3] Chat anónimo (sin cluster)...")
try:
    payload = {
        "message": "¿Cómo puedo abrir una cuenta?",
        "conversation_history": []
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Respuesta de Havi:")
        print(f"   {data['response'][:150]}...")
    else:
        print(f"❌ Error {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Chat with user (con cluster)
print(f"\n[4] Chat personalizado (con cluster y perfil)...")
try:
    payload = {
        "message": "¿Qué productos me recomiendas?",
        "user_id": TEST_USER,
        "conversation_history": []
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Respuesta de Havi (personalizada):")
        print(f"   Usuario: {data.get('user_name')}")
        print(f"   Respuesta: {data['response'][:150]}...")
    else:
        print(f"❌ Error {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Chat with conversation history
print(f"\n[5] Chat con historial de conversación...")
try:
    payload = {
        "message": "¿Y para inversiones?",
        "user_id": TEST_USER,
        "conversation_history": [
            {"role": "user", "content": "¿Qué productos me recomiendas?"},
            {"role": "assistant", "content": "Tenemos tarjetas de crédito, depósitos y Hey Pro para ti."}
        ]
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Respuesta (con contexto):")
        print(f"   {data['response'][:150]}...")
    else:
        print(f"❌ Error {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ PRUEBAS COMPLETADAS")
print("=" * 70)
