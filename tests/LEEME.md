# Pruebas de Unuvia (referencia)
Pruebas automáticas usadas para comprobar cada versión (navegador real con Playwright y un servidor de Supabase simulado).
Se ejecutan en un ordenador con Python, `pip install playwright` y `playwright install chromium`: sirve la carpeta de la web con
`python3 -m http.server 8766` y lanza, por ejemplo, `python3 tests/test_nov4.py`. Algunas rutas están escritas para mi entorno
(`/home/claude/...`): cámbialas por las tuyas. `a11y_scan.py` y `a11y_contrast.py` revisan accesibilidad (nombres de botones/campos y contraste de color).
No se publican en la web: el flujo de GitHub excluye la carpeta `tests`.
