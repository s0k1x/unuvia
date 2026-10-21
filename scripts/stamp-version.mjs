// Pone un número de versión nuevo (fecha y hora UTC) en index.html y version.json ANTES de publicar.
// Así la pantalla de «hay una versión nueva» funciona sola, sin que nadie toque números.
// Las «Novedades» salen del mensaje del commit si empieza por «Novedades:»  (ej.: «Novedades: nuevo horario por días»).
import fs from 'node:fs';
const root = process.argv[2] || '.';
const d = new Date(), p = n => String(n).padStart(2, '0');
const v = `${d.getUTCFullYear()}${p(d.getUTCMonth() + 1)}${p(d.getUTCDate())}${p(d.getUTCHours())}${p(d.getUTCMinutes())}`;
const idx = `${root}/index.html`, vj = `${root}/version.json`;
let h = fs.readFileSync(idx, 'utf8');
const n = (h.match(/(?:app\.js|styles\.css)\?v=\d+/g) || []).length;
if (n < 2) throw new Error('No encuentro app.js?v=… y styles.css?v=… en index.html');
h = h.replace(/((?:app\.js|styles\.css)\?v=)\d+/g, '$1' + v);
fs.writeFileSync(idx, h);
let j = {}; try { j = JSON.parse(fs.readFileSync(vj, 'utf8')); } catch { /* si no existe, se crea */ }
const first = String(process.env.COMMIT_MSG || '').split('\n')[0];
const m = first.match(/^novedades:\s*(.+)$/i);
j.v = v; j.force = j.force === false ? false : true; j.notes = m ? m[1].slice(0, 300) : '';
fs.writeFileSync(vj, JSON.stringify(j, null, 2) + '\n');
console.log('Versión', v, j.notes ? '· novedades: ' + j.notes : '· sin novedades');
