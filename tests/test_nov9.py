import asyncio,json,sys,re
sys.argv=[sys.argv[0]]
exec(open('/home/claude/test_upd.py').read().rsplit("async def main():",1)[0])
nov1=open('/home/claude/test_nov1.py').read().rsplit("async def main():",1)[0]
ok=0;bad=0
def chk(n,c,x=''):
    global ok,bad
    if c: ok+=1;print('  ✓',n)
    else: bad+=1;print('  ✗',n,x)
async def main():
    async with async_playwright() as p:
        # ---------- A. Herramienta Google (PC y móvil) ----------
        env={}
        exec(nov1,env)
        for W,H,tag in [(1280,800,'PC'),(390,844,'móvil')]:
            b,pg,errs=await env['boot'](p,W,H);await env['login'](pg);E=pg.evaluate
            await E("toolOpen('google');0");await pg.wait_for_timeout(900)
            await E("document.getElementById('ggUrl').value='hola esto no es de google';ggCheck();0");await pg.wait_for_timeout(300)
            r=await E("""(()=>{const i=document.getElementById('ggUrl'),bt=i.parentElement.querySelector('button'),f=document.getElementById('modalFields');const links=[...document.querySelectorAll('.ggt-links a')].map(a=>({t:a.textContent,deco:getComputedStyle(a).textDecorationLine,h:Math.round(a.getBoundingClientRect().height)}));return {iw:Math.round(i.getBoundingClientRect().width),bw:Math.round(bt.getBoundingClientRect().width),type:i.type,chips:document.querySelectorAll('.ggt .gg-chip').length,links,txt:f.innerText,over:document.documentElement.scrollWidth>innerWidth+1}})()""")
            chk(f"{tag}: el campo del enlace es ancho y «Pegar» es un botón normal (no se estira)",r['iw']>=(300 if W>600 else 150) and r['bw']<=160,(r['iw'],r['bw']))
            chk(f"{tag}: el campo ya no es type=url (se acabó el aviso «Introduce una URL»)",r['type']=='text')
            chk(f"{tag}: la herramienta no pone tarjetas sueltas junto a sus propios botones",r['chips']==0,r['chips'])
            chk(f"{tag}: «Abrir directamente» son botones (sin subrayado, altura ≥ 40 px): Mi Drive, Nueva videollamada y Calendario",[l['t'] for l in r['links']]==['Mi Drive','Nueva videollamada','Calendario'] and all(l['deco']=='none' and l['h']>=40 for l in r['links']),r['links'])
            chk(f"{tag}: Classroom ya no aparece en la herramienta",'Classroom' not in r['txt'])
            chk(f"{tag}: sin desbordes hacia los lados",not r['over'])
            await E("document.getElementById('ggUrl').value='';ggCheck();0")
            chk(f"{tag}: con el campo vacío no sale ningún aviso rojo",await E("document.getElementById('ggRes').innerHTML==''"))
            if W>600:
                await pg.screenshot(path='/home/claude/gg_despues.png',clip={"x":150,"y":40,"width":980,"height":640})
            await b.close()
        b,pg,errs=await env['boot'](p,1280,800);await env['login'](pg);E=pg.evaluate
        chk("un enlace de Classroom ya no se reconoce como de Google (ni sale tarjeta)",await E("ggParse('https://classroom.google.com/c/AbCdEf1234567')===null"))
        await E("data.posts=[{id:'pc1',n:'Marga',au:'u1',t:'Mirad https://classroom.google.com/c/AbCdEf1234567 y https://meet.google.com/abc-defg-hij',ts:Date.now(),pin:false,poll:null,img:null,comments:[]}];renderAll();goTab('Inicio');0");await pg.wait_for_timeout(1000)
        chk("en un anuncio solo sale tarjeta del enlace de Meet, no del de Classroom",await E("[...document.querySelectorAll('#classView .gg-chip')].map(c=>c.getAttribute('aria-label'))")==['Videollamada de Google Meet'])
        # ---------- B. Iconos del menú ----------
        print("MENÚ DEL PERFIL: ICONOS")
        await E("userMenu(document.getElementById('topAvatar'));0");await pg.wait_for_timeout(500)
        r=await E("""[...document.querySelectorAll('#amCard li.nz-item')].map(li=>({t:(li.querySelector('.nz-label,.nz-lab')||li).textContent.trim().slice(0,40),n:li.querySelectorAll('svg path,svg circle,svg rect,svg line,svg polyline').length}))""")
        sin=[x['t'] for x in r if x['n']==0]
        chk("todas las opciones del menú del perfil tienen icono (antes faltaban «Centro educativo» y «Unuvia Pro»)",len(r)>=6 and not sin,sin)
        chk("«Unuvia Pro» y «Centro educativo» están en el menú con su icono",any('Unuvia Pro' in x['t'] and x['n']>0 for x in r) and any('Centro educativo' in x['t'] and x['n']>0 for x in r),r)
        await E("closeMenu();0")
        src=await (await pg.request.get('http://localhost:8766/app.js')).text()
        used=sorted(set(re.findall(r'k:"(?:act|hold|toggle)"[^}]{0,200}?icon:"([a-z0-9]+)"',src)))
        have=await E("Object.keys(NZ)")
        chk("ningún menú de la app pide un icono que no exista (instalar, responder, avisos, descargar…)",[u for u in used if u not in have]==[],[u for u in used if u not in have])
        chk("y si algún día faltara uno, no sale «undefined» dentro del dibujo",'undefined' not in await E("nzSvg('inventado')"))
        await b.close()
        # ---------- C. Botón «Actualizar ahora» ----------
        print("ACTUALIZAR: SIN QUEDARSE EN UNA PÁGINA DE ERROR")
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        navs=[]
        pg.on('framenavigated',lambda f:navs.append(f.url) if f==pg.main_frame else None)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        await pg.evaluate("caches.open('unuvia-prueba').then(c=>c.put('/x',new Response('x')))");await pg.wait_for_timeout(200)
        kill=lambda r:r.abort()
        await pg.route('**/version.json*',kill)
        n0=len(navs)
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(2000)
        s=await pg.evaluate("""async()=>({st:document.getElementById('updSt').textContent,btn:document.getElementById('updGo').textContent,dis:document.getElementById('updGo').disabled,tries:sessionStorage.getItem('unuvia_upd_try'),u:/[?&]u=/.test(location.search),caches:await caches.keys()})""")
        chk("sin conexión con Unuvia: lo dice con claridad («Comprueba tu internet y vuelve a pulsar…»)",'No hay conexión con Unuvia' in s['st'] and 'Actualizar ahora' in s['st'],s['st'])
        chk("y el botón se puede volver a pulsar (no se queda en «Actualizando…»)",s['btn']=='Actualizar ahora' and not s['dis'],s)
        chk("NO recarga la página, NO deja el ?u= y no gasta el intento",len(navs)==n0 and not s['u'] and s['tries'] in (None,'0'),(len(navs)-n0,s['u'],s['tries']))
        chk("NO borra ninguna copia guardada (sin conexión borrarlas era lo que dejaba la página en blanco)",'unuvia-prueba' in s['caches'],s['caches'])
        await pg.unroute('**/version.json*',kill)
        await pg.evaluate("window.__cd=[];const d=caches.delete.bind(caches);caches.delete=k=>{sessionStorage.setItem('cdel',(sessionStorage.getItem('cdel')||'')+'|'+k);return d(k)};0")
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(5500)
        s=await pg.evaluate("({gate:!!document.getElementById('updGate'),tries:sessionStorage.getItem('unuvia_upd_try'),cdel:sessionStorage.getItem('cdel')||''})")
        chk("con conexión, el PRIMER intento recarga la página y NO borra las copias",s['tries']=='1' and s['cdel']=='',s)
        await pg.evaluate("caches.open('unuvia-prueba').then(c=>c.put('/x',new Response('x')));const d=caches.delete.bind(caches);caches.delete=k=>{sessionStorage.setItem('cdel',(sessionStorage.getItem('cdel')||'')+'|'+k);return d(k)};0");await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(5500)
        s=await pg.evaluate("({tries:sessionStorage.getItem('unuvia_upd_try'),cdel:sessionStorage.getItem('cdel')||''})")
        chk("el SEGUNDO intento sí hace la limpieza a fondo (borra las copias de Unuvia)",s['tries']=='2' and 'unuvia-prueba' in s['cdel'],s)
        await b.close()
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        navs=[]
        pg.on('framenavigated',lambda f:navs.append(f.url) if f==pg.main_frame else None)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        await pg.evaluate("navigator.serviceWorker.getRegistration=()=>Promise.resolve({update:()=>new Promise(()=>{})});0")
        n0=len(navs)
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(7000)
        chk("aunque el service worker no conteste a «update», no se queda colgado: recarga en unos 4 segundos",len(navs)>n0,len(navs)-n0)
        await b.close()
        print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
