# TODO - Arreglar Infraestructura Havi

## Pasos a completar

- [x] 1. Corregir bug en `Front/index.html`: agregar `await` a `res.json()` en función `identifyUser`.
- [x] 2. Limpiar puerto 8000 (PowerShell): matar procesos que usen el puerto y cualquier python.exe residual, esperar 3 segundos y verificar que esté libre.
- [x] 3. Iniciar backend desde `Back/`: `python backend.py` (usar `.venv`) y verificar mensajes esperados.
- [x] 4. Iniciar frontend desde `Front/`: `python -m http.server 8080` y verificar que sirva en 8080.
- [x] 5. Abrir navegador en `http://localhost:8080`.
- [x] 6. Validar:
   - Estado "Conectado" en verde.
   - Identificación con `USR-00001`.
   - Streaming de respuesta letra por letra.
   - Scroll del chat funcional.

