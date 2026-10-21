import asyncio,json,re
from playwright.async_api import async_playwright
UA_IOS="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
UA_AND="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36"
CUR="202610202300"; NEW="202610202400"
async def mk(p,ver=None,ua=None,mobile=False,rewrite_index=None,delay=0):
    b=await p.chromium.launch(args=["--no-sandbox"])
    kw=dict(viewport={"width":390 if mobile else 1280,"height":844 if mobile else 800},device_scale_factor=1,is_mobile=mobile,has_touch=mobile)
    if ua: kw['user_agent']=ua
    ctx=await b.new_context(**kw)
    pg=await ctx.new_page(); st={'ver':ver,'idx':rewrite_index}
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:160]))
    async def vj(route):
        v=st['ver']
        if v is None: await route.fulfill(status=500,body="x"); return
        if v=='abort': await route.abort(); return
        await route.fulfill(status=200,content_type="application/json",body=json.dumps(v),headers={"Cache-Control":"no-store"})
    await pg.route("**/version.json*",vj)
    async def idx(route):
        r=await route.fetch(); t=await r.text()
        if st['idx']: t=t.replace(CUR,st['idx'])
        await route.fulfill(response=r,body=t)
    await pg.route(re.compile(r".*/(\?.*)?$"),idx)
    await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
    await pg.add_init_script("try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_cookies','1')}catch(e){}")
    return b,pg,st,errs
async def main():
    ok=0;bad=0
    def chk(n,c,x=''):
        nonlocal ok,bad
        if c: ok+=1;print('  ✓',n)
        else: bad+=1;print('  ✗',n,x)
    async with async_playwright() as p:
        print("Detección")
        b,pg,st,errs=await mk(p,ver={"v":CUR,"force":True})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4200)
        chk("la versión de la app se lee de su propia dirección (app.js?v=…)",await pg.evaluate("APP_V")==CUR)
        chk("con la misma versión no pasa nada",not await pg.evaluate("!!document.getElementById('updGate')||!!document.getElementById('updBar')"))
        st['ver']={"v":"202610192200","force":True}; await pg.evaluate("updCheck();0");await pg.wait_for_timeout(800)
        chk("si el servidor tiene una versión MÁS ANTIGUA (marcha atrás) no bloquea",not await pg.evaluate("!!document.getElementById('updGate')"))
        for bad_v,name in [(None,"si el servidor falla (500)"),('abort',"si no hay internet")]:
            st['ver']=bad_v; await pg.evaluate("updCheck();0");await pg.wait_for_timeout(800)
            chk(f"{name} no bloquea nada",not await pg.evaluate("!!document.getElementById('updGate')"))
        await b.close()
        print("Bloqueo")
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":"Nuevo asistente de IA y horario por días."})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        g=await pg.evaluate("""()=>{const e=document.getElementById('updGate');if(!e)return null;const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return {w:r.width,h:r.height,z:+cs.zIndex,txt:e.textContent,inert:[...document.body.children].filter(x=>x.hasAttribute('data-upd-inert')).length,lock:document.documentElement.classList.contains('upd-lock')}}""")
        chk("sale la pantalla «Hay una versión nueva de Unuvia» a pantalla completa",bool(g) and g['w']>=1200 and g['h']>=700 and 'versión nueva' in g['txt'],g)
        chk("muestra las novedades",bool(g) and 'Nuevo asistente de IA' in g['txt'])
        chk("el resto de la app queda inutilizable (inert) y sin scroll",bool(g) and g['inert']>=2 and g['lock'])
        chk("no se puede tocar lo de debajo (el clic cae en el aviso)",await pg.evaluate("(()=>{const e=document.elementFromPoint(640,400);return !!e&&!!e.closest('#updGate')})()"))
        await pg.keyboard.press("Escape");await pg.wait_for_timeout(200)
        chk("Esc no lo cierra",await pg.evaluate("!!document.getElementById('updGate')"))
        for _ in range(12): await pg.keyboard.press("Tab")
        chk("el teclado (Tab) no puede salir del aviso",await pg.evaluate("!!document.activeElement.closest('#updGate')"))
        chk("no tiene botón de cerrar ni «más tarde»",await pg.evaluate("!document.querySelector('#updGate [aria-label*=Cerrar],#updGate .lv-x')&&!/Más tarde/.test(document.getElementById('updGate').textContent)"))
        chk("en ordenador enseña por defecto los pasos de «Ordenador» (Ctrl + F5)",'Ctrl + F5' in await pg.evaluate("document.getElementById('updHelp').textContent"))
        await pg.evaluate("document.querySelector('#updGate details').open=true;updTab('ios')");
        chk("se puede cambiar a iPhone/iPad y a Android",('Safari' in await pg.evaluate("document.getElementById('updHelp').textContent")) and (await pg.evaluate("updTab('and');document.getElementById('updHelp').textContent")).count('Android')>=0 and 'Borrar caché' in await pg.evaluate("document.getElementById('updHelp').textContent"))
        await pg.screenshot(path='/home/claude/upd_pc.png')
        await b.close()
        for ua,mob,key,txt,name in [(UA_IOS,True,'ios','Datos de sitios web','iPhone'),(UA_AND,True,'and','Información de la aplicación','Android')]:
            b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""},ua=ua,mobile=mob)
            await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
            chk(f"en {name} enseña directamente los pasos de su dispositivo",txt in await pg.evaluate("(document.getElementById('updHelp')||{}).textContent||''"))
            if key=='ios':
                await pg.evaluate("document.querySelector('#updGate details').open=true");await pg.wait_for_timeout(200)
                await pg.screenshot(path='/home/claude/upd_ios.png')
            await b.close()
        print("Botón «Actualizar ahora»")
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(4500)
        url1=pg.url
        s=await pg.evaluate("""()=>({gate:!!document.getElementById('updGate'),title:(document.getElementById('updT')||{}).textContent,open:(document.querySelector('#updGate details')||{}).open,tries:sessionStorage.getItem('unuvia_upd_try'),u:/[?&]u=/.test(location.search)})""")
        chk("recarga la página (con la caché limpia) y, si sigue la versión antigua, avisa «Todavía no se ha actualizado» con los pasos abiertos",s['gate'] and 'Todavía no' in (s['title'] or '') and s['open'] and s['tries']=='1',s)
        chk("la dirección no se queda con el parámetro ?u= de limpieza",not s['u'])
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(4500)
        chk("al segundo intento hace una limpieza más a fondo (cuenta 2)",await pg.evaluate("sessionStorage.getItem('unuvia_upd_try')")=='2')
        st['idx']=NEW   # ahora el servidor ya entrega la versión nueva del index
        await pg.evaluate("document.getElementById('updGo').click()");await pg.wait_for_timeout(5000)
        s=await pg.evaluate("({gate:!!document.getElementById('updGate'),v:APP_V,tries:sessionStorage.getItem('unuvia_upd_try'),inert:document.querySelectorAll('[data-upd-inert]').length})")
        chk("cuando ya llega la versión nueva: se actualiza, desaparece el aviso y se desbloquea todo",(not s['gate']) and s['v']==NEW and s['inert']==0,s)
        chk("se borra el contador de intentos",s['tries'] is None)
        await b.close()
        print("«Ya lo he hecho: comprobar otra vez»")
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        await pg.evaluate("document.querySelector('#updGate details').open=true;updRecheck()");await pg.wait_for_timeout(1200)
        chk("si sigue sin actualizar lo dice y sigue bloqueado",await pg.evaluate("!!document.getElementById('updGate')&&/Todavía hay una versión nueva/.test(document.getElementById('updSt').textContent)"))
        st['ver']={"v":CUR,"force":True}
        await pg.evaluate("updRecheck()");await pg.wait_for_timeout(1200)
        chk("si ya está al día se quita el bloqueo",await pg.evaluate("!document.getElementById('updGate')&&document.querySelectorAll('[data-upd-inert]').length===0"))
        await b.close()
        print("No interrumpe nada importante")
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(500)
        await pg.evaluate("EXR={done:false};const d=document.createElement('div');d.id='exam';d.textContent='examen';document.body.appendChild(d);0")
        await pg.wait_for_timeout(4200)
        s=await pg.evaluate("({gate:!!document.getElementById('updGate'),bar:(document.getElementById('updBar')||{}).textContent||''})")
        chk("durante un examen NO bloquea y avisa de que se pedirá al terminar",(not s['gate']) and 'el examen' in s['bar'],s)
        await pg.evaluate("document.getElementById('exam').remove();0");await pg.wait_for_timeout(6500)
        chk("al terminar el examen sí aparece",await pg.evaluate("!!document.getElementById('updGate')&&!document.getElementById('updBar')"))
        await b.close()
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(500)
        await pg.evaluate("const d=document.createElement('div');d.id='qg';document.body.appendChild(d);window.LV&&0;0");await pg.wait_for_timeout(4200)
        chk("durante una corrección tampoco",not await pg.evaluate("!!document.getElementById('updGate')"))
        await b.close()
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":True,"notes":""})
        await pg.clock.install()
        await pg.goto("http://localhost:8766/");await pg.clock.run_for(1000)
        await pg.evaluate("modal('post');0");await pg.clock.run_for(500)
        await pg.evaluate("const t=document.getElementById('f1');t.focus();t.value='Hola clase, mañana no hay';0")
        await pg.clock.run_for(4000)
        s=await pg.evaluate("({gate:!!document.getElementById('updGate'),bar:/terminar de escribir|terminas/.test((document.getElementById('updBar')||{}).textContent||'')||/escribir/.test((document.getElementById('updBar')||{}).textContent||'')})")
        chk("si estás escribiendo un anuncio espera un poco (avisa) en vez de cortarte",(not s['gate']) and s['bar'],s)
        await pg.clock.run_for(30000)
        chk("pero no espera para siempre: a los ~20 s bloquea",await pg.evaluate("!!document.getElementById('updGate')"))
        await b.close()
        print("Aviso suave (force:false)")
        b,pg,st,errs=await mk(p,ver={"v":NEW,"force":False,"notes":""})
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        s=await pg.evaluate("({gate:!!document.getElementById('updGate'),bar:(document.getElementById('updBar')||{}).textContent||''})")
        chk("con «force: false» solo sale un aviso con «Actualizar» y «Más tarde» (no bloquea)",(not s['gate']) and 'Actualizar' in s['bar'] and 'Más tarde' in s['bar'],s)
        await pg.evaluate("document.querySelector('#updBar .mini-btn').click()")
        chk("«Más tarde» lo oculta",not await pg.evaluate("!!document.getElementById('updBar')"))
        await b.close()
    print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
