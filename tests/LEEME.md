# Pruebas de Unuvia (referencia)
Son las pruebas automáticas que se han usado para comprobar cada versión (navegador real con Playwright y un servidor de Supabase simulado).
Se ejecutan en un ordenador con Python, `pip install playwright` y `playwright install chromium`: sirve la carpeta de la web con
`python3 -m http.server 8766` y lanza, por ejemplo, `python3 tests/test_nov1.py`. Algunas rutas están escritas para mi entorno
(`/home/claude/...`): cámbialas por las tuyas. No se publican en la web: el flujo de GitHub las excluye (carpeta `tests`).
