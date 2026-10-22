import fs from 'node:fs'; import vm from 'node:vm';
const code=fs.readFileSync('/home/claude/out/sw.js','utf8');
const hdr=h=>h instanceof Map?Object.fromEntries(h):(h||{});
class Resp{constructor(body,init={}){this.body=body;this.status=init.status??200;this.statusText=init.statusText||'';this.headers=new Map(Object.entries(hdr(init.headers)));this.redirected=false;this.ok=this.status>=200&&this.status<300;this.type='basic'}clone(){const c=new Resp(this.body,{status:this.status,statusText:this.statusText,headers:this.headers});c.redirected=this.redirected;return c}async blob(){return {blobOf:this.body}}async text(){return String(this.body&&this.body.blobOf!==undefined?this.body.blobOf:this.body)}}
const store=new Map();let fetchImpl=async()=>new Resp('<html>web</html>'),fetchArgs=[],cachesBroken=false,puts=[];
const sandbox={console,URL,Response:Resp,Request:class{},
 fetch:(...a)=>{fetchArgs.push(a);return fetchImpl(...a)},
 caches:{open:async()=>{if(cachesBroken)throw new Error('storage');return{
   match:async(k,o)=>{const key=typeof k==='string'?k:k.url;let hit=store.get(key);if(!hit&&o&&o.ignoreSearch){const base=String(key).split('?')[0];for(const[kk,v]of store)if(String(kk).split('?')[0]===base)hit=v}return hit},
   put:async(k,r)=>{puts.push(typeof k==='string'?k:k.url);store.set(typeof k==='string'?k:k.url,r)},addAll:async()=>{},keys:async()=>[...store.keys()].map(url=>({url})),delete:async k=>{store.delete(k)}}},keys:async()=>['unuvia-v15'],delete:async()=>true},
 self:{}};
const L={};sandbox.addEventListener=(t,f)=>{L[t]=f};
sandbox.self={addEventListener:(t,f)=>{L[t]=f},skipWaiting(){},clients:{claim:async()=>{}},location:{origin:'https://unuvia.es'},registration:{}};
vm.createContext(sandbox);vm.runInContext(code,sandbox);
let ok=0,bad=0;const T=async(n,f)=>{let r=false;try{r=await f()}catch(e){console.log('   error:',e.message)}if(r){ok++;console.log('  ✓',n)}else{bad++;console.log('  ✗',n)}};
const fire=async(url,{mode='navigate',method='GET'}={})=>{let rp=null,called=false;let wp=null;L.fetch({request:{method,url,mode},respondWith:p=>{called=true;rp=p},waitUntil:p=>{wp=p}});if(!called)return{ignored:true};try{const res=await rp;if(wp)await wp;return{res}}catch(err){if(wp)await Promise.resolve(wp).catch(()=>{});return{err}}};
const reset=()=>{store.clear();fetchArgs=[];puts=[];cachesBroken=false;fetchImpl=async()=>new Resp('<html>web</html>')};
console.log('Service worker: abrir la página (navegaciones)');
reset();
await T('con internet: sirve la página y pide «sin copia vieja» con una petición NUEVA (la dirección, no la de navegación)',async()=>{const o=await fire('https://unuvia.es/?u=1');const a=fetchArgs[0];return o.res&&o.res.status===200&&a[0]==='https://unuvia.es/?u=1'&&a[1].cache==='no-cache'&&a[1].redirect==='follow'&&a[1].credentials==='same-origin'});
await T('guarda una copia para cuando no haya internet',async()=>puts.includes('https://unuvia.es/?u=1'));
reset();fetchImpl=async()=>{const r=new Resp('<html>destino</html>');r.redirected=true;return r};
await T('una respuesta «redirigida» se entrega limpia (Safari la rechazaba: «Load failed»)',async()=>{const o=await fire('https://unuvia.es/panel');return o.res&&o.res.redirected===false&&o.res.status===200});
reset();store.set('/',new Resp('<html>copia</html>'));fetchImpl=async()=>{throw new TypeError('Load failed')};
await T('sin internet y con copia: sirve la copia de la página (aunque la dirección lleve ?u=…)',async()=>{const o=await fire('https://unuvia.es/?u=999');return o.res&&String(o.res.body).includes('copia')});
reset();fetchImpl=async()=>{throw new TypeError('Load failed')};
await T('SIN internet y SIN ninguna copia (caché borrada por «Actualizar»): enseña la página «Reintentar» y NO falla',async()=>{const o=await fire('https://unuvia.es/?u=1');return !o.err&&o.res&&o.res.status===503&&/Reintentar/.test(o.res.body)&&/No se pudo cargar Unuvia/.test(o.res.body)});
await T('esa página es HTML, no se guarda en ninguna caché y se reintenta sola cuando vuelve internet',async()=>{const o=await fire('https://unuvia.es/');return /text\/html/.test(o.res.headers.get('Content-Type'))&&o.res.headers.get('Cache-Control')==='no-store'&&/navigator\.onLine/.test(o.res.body)&&puts.length===0});
reset();cachesBroken=true;fetchImpl=async()=>{throw new TypeError('Load failed')};
await T('si ni siquiera se puede abrir el almacenamiento: tampoco falla (página «Reintentar»)',async()=>{const o=await fire('https://unuvia.es/');return !o.err&&o.res&&o.res.status===503});
reset();cachesBroken=true;
await T('con el almacenamiento roto pero con internet: la web carga igual',async()=>{const o=await fire('https://unuvia.es/');return o.res&&o.res.status===200});
reset();fetchImpl=async()=>new Resp('No encontrado',{status:404});
await T('una 404 del servidor se entrega tal cual (la página 404 propia) y no se guarda',async()=>{const o=await fire('https://unuvia.es/nada');return o.res.status===404&&puts.length===0});
console.log('Service worker: lo que NO debe tocar');
reset();
await T('version.json va siempre directo a la red (el SW no responde)',async()=>(await fire('https://unuvia.es/version.json?t=1',{mode:'cors'})).ignored===true);
await T('peticiones a la base de datos (otro dominio) no se tocan',async()=>(await fire('https://akbhcirarjnfajqzafci.supabase.co/rest/v1/x',{mode:'cors'})).ignored===true);
await T('las peticiones que no son GET (guardar, enviar) no se tocan',async()=>(await fire('https://unuvia.es/',{method:'POST'})).ignored===true);
fetchImpl=async()=>{throw new TypeError('Load failed')};
await T('un archivo suelto (no página) sin internet y sin copia sigue fallando como antes (no se disfraza de página)',async()=>{const o=await fire('https://unuvia.es/app.js?v=1',{mode:'no-cors'});return !!o.err&&!(o.res&&o.res.status===503)});
reset();
await T('un archivo con ?v= con internet se sirve y se guarda',async()=>{const o=await fire('https://unuvia.es/styles.css?v=5',{mode:'no-cors'});return o.res&&o.res.status===200});
console.log(`\n${ok} correctas, ${bad} fallos`);
