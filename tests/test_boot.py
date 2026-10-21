import asyncio,json
from playwright.async_api import async_playwright
FAKE_SESSION=r"""
(()=>{const boom=()=>{throw new Error('red caída')};
window.__fakeSb={auth:{getSession:async()=>{if((window.__gsFail||0)>0){window.__gsFail--;throw new Error('lock timeout')}return({data:{session:window.__noSess?null:{user:window.__nullUser?null:{id:'u1',email:'prof@centro.es'},access_token:'x'}}})},onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),signOut:async()=>{localStorage.setItem('__so','1')},getUser:async()=>({data:{user:null}})},
 from:boom,rpc:boom,channel:boom,removeChannel(){},storage:{from:boom},functions:{invoke:async()=>({data:null,error:null})}};})();
"""
async def new(p,hint=True,fake=True,noSess=False,offline_cache=False,nullUser=False,gsFail=0):
    b=await p.chromium.launch(args=["--no-sandbox"])
    ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=1,is_mobile=True,has_touch=True)
    pg=await ctx.new_page(); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)[:160]))
    async def patch(route):
        r=await route.fetch(); t=await r.text()
        await route.fulfill(response=r,body=t.replace('sb=window.supabase?','sb=window.__fakeSb?window.__fakeSb:window.supabase?',1))
    await pg.route("**/app.js*",patch);await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
    init="try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','dark');localStorage.setItem('unuvia_cookies','1')}catch(e){}"
    if hint: init+="try{localStorage.setItem('sb-proyecto-auth-token',JSON.stringify({access_token:'x',refresh_token:'y',user:{id:'u1'}}))}catch(e){}"
    if offline_cache: init+="try{localStorage.setItem('unuvia_off_u1',JSON.stringify({t:Date.now(),user:'Prof',curId:'c1',classes:[{id:'c1',name:'1º FPB',emoji:'📚',color:'#008cff',role:'Profesor',code:'MT-1',data:{events:[],tasks:[],sched:[],work:[],members:[],messages:[],photos:[],posts:[],topics:[],todo:[]}}]}))}catch(e){}"
    if noSess: init+="window.__noSess=true;"
    if nullUser: init+="window.__nullUser=true;"
    if gsFail: init+="window.__gsFail=%d;"%gsFail
    await pg.add_init_script((FAKE_SESSION if fake else "")+init)
    return b,pg,errs
async def state(pg):
    return await pg.evaluate("""()=>{const vis=e=>{if(!e)return false;const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'};
      return {hasSess:document.documentElement.classList.contains('has-sess'),launchVisible:vis(document.getElementById('startLogin')),retry:vis(document.getElementById('bootRetry')),inApp:document.body.classList.contains('in-app'),ro:document.body.classList.contains('offline-ro')}}""")
async def main():
    ok=0;bad=0
    def chk(n,c,x=''):
        nonlocal ok,bad
        if c: ok+=1;print('  ✓',n)
        else: bad+=1;print('  ✗',n,x)
    async with async_playwright() as p:
        print("0) Sesión iniciada y la carga de datos lanza errores: la app entra sola, sin LAUNCH")
        b,pg,errs=await new(p)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        s=await state(pg);print('   ',s)
        chk("no se ve LAUNCH (entra en la app)",not s['launchVisible'] and (s['inApp'] or s['retry']))
        await b.close()
        print("1) Sesión iniciada pero la app no consigue entrar (antes salía «LAUNCH»)")
        b,pg,errs=await new(p,nullUser=True)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        s=await state(pg);print('   ',s)
        chk("no se ve el botón LAUNCH",not s['launchVisible'])
        chk("sale el aviso «No se ha podido conectar» con Reintentar",s['retry'])
        txt=await pg.evaluate("document.getElementById('bootRetry')?document.getElementById('bootRetry').textContent:''")
        chk("el aviso dice que la sesión sigue iniciada",'sesión sigue iniciada' in txt)
        await pg.evaluate("document.querySelector('#bootRetry .mini-btn').click()");await pg.wait_for_timeout(800)
        chk("«Entrar con otra cuenta» cierra la sesión guardada (signOut + recarga)",await pg.evaluate("localStorage.getItem('__so')==='1'"))
        await b.close()
        print("1b) getSession falla siempre (bloqueo interno del navegador) con sesión guardada")
        b,pg,errs=await new(p,gsFail=9)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(6000)
        s=await state(pg);print('   ',s)
        chk("no se ve LAUNCH y sale el aviso de reintentar",not s['launchVisible'] and s['retry'])
        await b.close()
        print("1c) getSession falla 2 veces y a la tercera funciona")
        b,pg,errs=await new(p,gsFail=2)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(6000)
        s=await state(pg);print('   ',s)
        chk("reintenta solo y entra en la app sin LAUNCH ni aviso",s['inApp'] and not s['launchVisible'] and not s['retry'])
        await b.close()
        print("2) Sesión iniciada y copia sin conexión disponible → entra en modo lectura")
        b,pg,errs=await new(p,offline_cache=True,gsFail=9)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        s=await state(pg);print('   ',s)
        chk("entra en la app (sin LAUNCH ni aviso) en modo solo lectura",s['inApp'] and s['ro'] and not s['launchVisible'] and not s['retry'])
        await b.close()
        print("3) Sin ninguna sesión → sí aparece LAUNCH (normal)")
        b,pg,errs=await new(p,hint=False,fake=False)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(3500)
        s=await state(pg);print('   ',s)
        chk("sin sesión se ve LAUNCH y no el aviso",s['launchVisible'] and not s['retry'] and not s['hasSess'])
        await b.close()
        print("4) Sesión guardada pero caducada (getSession devuelve nada) → LAUNCH")
        b,pg,errs=await new(p,noSess=True)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(3500)
        s=await state(pg);print('   ',s)
        chk("con sesión caducada se quita la marca y se ve LAUNCH",s['launchVisible'] and not s['retry'] and not s['hasSess'])
        await b.close()
        print("5) No carga la librería de Supabase (CDN caído) pero hay sesión guardada")
        b,pg,errs=await new(p,fake=False)
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(4500)
        s=await state(pg);print('   ',s)
        chk("no se ve LAUNCH y sale el aviso de reintentar",not s['launchVisible'] and s['retry'])
        await b.close()
        print("6) La carga NO termina nunca (red muy lenta): a los 30 s sale el aviso, nunca LAUNCH")
        b,pg,errs=await new(p)
        await pg.add_init_script("(()=>{const nv=()=>new Proxy(function(){},{get:(t,k)=>k==='then'?(()=>{}):nv(),apply:()=>nv()});window.__fakeSb.from=nv;window.__fakeSb.rpc=nv;window.__fakeSb.storage={from:nv}})()")
        await pg.clock.install()
        await pg.goto("http://localhost:8766/")
        await pg.clock.run_for(12000);await pg.wait_for_timeout(300)
        s=await state(pg);print('   a los 12 s:',s)
        chk("a los 12 s (el splash antes se quitaba a los 10) NO se ve LAUNCH",not s['launchVisible'])
        await pg.clock.run_for(20000);await pg.wait_for_timeout(300)
        s=await state(pg);print('   a los 32 s:',s)
        chk("a los 32 s sale el aviso de reintentar y sigue sin verse LAUNCH",s['retry'] and not s['launchVisible'])
        await b.close()
    print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
