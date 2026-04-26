# TODO: Hacer respuestas de Havi más abiertas y conversacionales

## Problema
Las respuestas de Havi están muy cerradas, cortas y robóticas. El usuario siente que casi no responde nada aunque ya esté identificado.

## Causas identificadas en `Back/backend.py`
1. `max_tokens=150` en ambas llamadas a Groq → respuestas forzosamente cortas
2. System prompt muy restrictivo: "RESPONDE EXACTAMENTE lo que pregunten" y "Sé directo"
3. Falta de personalidad cálida y conversacional en los prompts
4. Temperature 0.7 un poco bajo para un asistente conversacional

## Plan de cambios
- [x] Aumentar `max_tokens` de 150 → 800 en `chat_with_groq()` y endpoint `/chat`
- [x] Subir `temperature` de 0.7 → 0.85
- [x] Reescribir system prompt anónimo: más cálido, proactivo, con emojis, invita a conversar
- [x] Reescribir system prompt identificado: eliminar restricciones duras, usar perfil como contexto no como límite, permitir recomendaciones y seguimientos
- [x] Integrar modelo de clusters (`ModeloClustersUsuarios.ipynb`) desde CSV
- [x] Inyectar estrategias de atención personalizadas por cluster en el system prompt
- [x] Actualizar endpoint `/users/{user_id}/cluster` para usar nuevo modelo con fallback legacy
- [x] Actualizar endpoint `/chat` para obtener cluster name, pasarlo al prompt y devolverlo
- [x] Actualizar frontend para mostrar label de cluster al identificar usuario
- [x] Reiniciar backend y probar

## Archivos editados
- `Back/backend.py`
- `Front/index.html`
- `TODO.md`

## Estado
✅ COMPLETADO

