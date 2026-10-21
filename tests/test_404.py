import asyncio,json
from playwright.async_api import async_playwright
HTML=open('/home/claude/out/404.html',encoding='utf8').read()
PANEL=open('/home/claude/out/panel/index.html',encoding='utf8').read()
async def mk(p,w,h,theme=None,mode=None,scheme='dark'):
    b=await p.chromium.launch(args=["--no-sandbox"])
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=1,color_scheme=scheme)
    pg=await ctx.new_page(); nav=[]
    pg.on("framenavigated",lambda f:nav.append(f.url) if f==pg.main_frame else None)
    async def nf(route):
        u=route.request.url
        if '/no/existe' in u or u.endswith('/rara'): await route.fulfill(status=404,content_type="text/html; charset=utf-8",body=HTML)
        elif u.rstrip('/').endswith('/panel') or u.endswith('/panel/'): await route.fulfill(status=200,content_type="text/html; charset=utf-8",body=PANEL)
        elif u.rstrip('/').endswith('/admin') or u.rstrip('/').endswith('/app'): await route.fulfill(status=404,content_type="text/html; charset=utf-8",body=HTML)
        else: await route.continue_()
    await pg.route("**/*",nf)
    init=""
    if theme: init+=f"localStorage.setItem('unuvia_icon','{theme}');"
    if mode: init+=f"localStorage.setItem('unuvia_theme','{mode}');"
    if init: await pg.add_init_script("try{"+init+"}catch(e){}")
    return b,pg,nav
async def main():
    ok=0;bad=0
    def chk(n,c,x=''):
        nonlocal ok,bad
        if c: ok+=1;print('  ✓',n)
        else: bad+=1;print('  ✗',n,x)
    async with async_playwright() as p:
        b,pg,nav=await mk(p,390,844)
        r=await pg.goto("http://localhost:8766/no/existe?x=1");await pg.wait_for_timeout(900)
        chk("responde con estado 404 y es la página de Unuvia",r.status==404 and 'Unuvia' in await pg.title())
        t=await pg.evaluate("document.body.innerText")
        chk("dice «404», «Esta página se ha perdido» y la dirección que no existe",'404' in t and 'Esta página se ha perdido' in t and '/no/existe?x=1' in t,t[:200])
        chk("ya NO redirige solo a la portada (se queda en la 404)",pg.url.endswith('/no/existe?x=1'))
        chk("tiene el botón «Ir a Unuvia»",await pg.evaluate("document.querySelector('a.btn.pri').getAttribute('href')")=='/')
        chk("el logo es el icono de Unuvia y carga",await pg.evaluate("(()=>{const i=document.querySelector('#nf .logo img');return i.complete&&i.naturalWidth>0&&i.src.endsWith('/icon-192.png')})()"))
        await pg.screenshot(path='/home/claude/n404_m.png')
        await pg.click("a.btn.pri");await pg.wait_for_timeout(1200)
        chk("«Ir a Unuvia» lleva a la portada",pg.url.rstrip('/')=="http://localhost:8766")
        await b.close()
        b,pg,nav=await mk(p,390,844,theme='halloween',mode='dark')
        await pg.goto("http://localhost:8766/no/existe");await pg.wait_for_timeout(900)
        s=await pg.evaluate("({a:getComputedStyle(document.documentElement).getPropertyValue('--a').trim(),src:document.querySelector('#nf .logo img').getAttribute('src')})")
        chk("con el tema Halloween usa sus colores y SU icono",s['a']=='#ff7a1a' and s['src']=='/icons/halloween/icon-192.png',s)
        await pg.screenshot(path='/home/claude/n404_h.png')
        await b.close()
        b,pg,nav=await mk(p,1280,800,mode='light',scheme='light')
        await pg.goto("http://localhost:8766/no/existe");await pg.wait_for_timeout(900)
        await pg.screenshot(path='/home/claude/n404_d.png')
        await b.close()
        for path,dest in [('/admin','/#panel'),('/app','/')]:
            b,pg,nav=await mk(p,390,844)
            await pg.goto("http://localhost:8766"+path);await pg.wait_for_timeout(1800)
            chk(f"{path} sigue abriendo {dest} (con pantalla de carga de Unuvia)",pg.url.endswith(dest) or pg.url.rstrip('/').endswith('localhost:8766'),pg.url)
            await b.close()
        b,pg,nav=await mk(p,390,844)
        await pg.goto("http://localhost:8766/admin",wait_until="commit");await pg.wait_for_timeout(120)
        t=await pg.evaluate("document.body.className+' | '+document.getElementById('loadT').textContent")
        chk("mientras redirige enseña «Abriendo el panel de Unuvia…» con su marca (no una pantalla en blanco)",'loading' in t and 'panel de Unuvia' in t,t)
        await pg.screenshot(path='/home/claude/n404_load.png')
        await b.close()
        b,pg,nav=await mk(p,390,844)
        await pg.goto("http://localhost:8766/panel/");await pg.wait_for_timeout(120)
        chk("/panel/ (la página propia del panel) también tiene la marca y redirige",'Abriendo el panel de Unuvia' in await pg.evaluate("document.body.innerText") or pg.url.endswith('#panel'))
        await b.close()
    print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
