import asyncio,json
from playwright.async_api import async_playwright
src=open('/home/claude/test_ia.py').read()
FAKE=src.split('FAKE=r"""')[1].split('"""')[0]
async def run(p,W,H):
    b=await p.chromium.launch(args=["--no-sandbox"])
    ctx=await b.new_context(viewport={"width":W,"height":H},device_scale_factor=1,is_mobile=W<700,has_touch=W<700)
    pg=await ctx.new_page(); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)[:200]))
    async def patch(route):
        r=await route.fetch(); t=await r.text()
        await route.fulfill(response=r,body=t.replace('sb=window.supabase?','sb=window.__fakeSb?window.__fakeSb:window.supabase?',1))
    await pg.route("**/app.js*",patch);await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
    await pg.add_init_script(FAKE+"try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','dark')}catch(e){}")
    await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(1400)
    await pg.evaluate("acceptCookies();launchApp(document.getElementById('startLogin'))");await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelector('input[value=local]').click();document.getElementById('localName').value='Marga';document.getElementById('localLoginButton').click()");await pg.wait_for_timeout(1400)
    await pg.evaluate("settings.toured=true;addClass({id:'c1',name:'1º FPB',code:'MT-1',role:'Profesor',emoji:'💻',color:'#008cff'});0");await pg.wait_for_timeout(500)
    return b,pg,errs
async def main():
    ok=0;bad=0
    def chk(n,c,x=''):
        nonlocal ok,bad
        if c: ok+=1;print('  ✓',n)
        else: bad+=1;print('  ✗',n,x)
    async with async_playwright() as p:
        for (W,H,name) in [(390,844,'móvil'),(1440,900,'PC')]:
            print(f"Acceso directo del asistente ({name})")
            b,pg,errs=await run(p,W,H);E=pg.evaluate
            await E("CFG.features={};0");await pg.wait_for_timeout(3500)
            chk("con Gemini apagado no se ve el acceso directo",await E("(()=>{const e=document.getElementById('tabAI');return !e||getComputedStyle(e).display==='none'})()"))
            await E("CFG.features={gemini:true};0");await pg.wait_for_timeout(3600)
            vis=await E("(()=>{const e=document.getElementById('tabAI');if(!e)return null;const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return {w:r.width,h:r.height,disp:cs.display,last:e.parentElement.lastElementChild===e,prev:e.previousElementSibling.title,txt:e.textContent.trim()}})()")
            chk("con Gemini encendido y profesor: aparece al final de la barra, justo después de Chat",bool(vis) and vis['disp']!='none' and vis['w']>20 and vis['last'] and vis['prev']=='Chat',vis)
            if W>700: chk("en PC se lee «Asistente IA» en el menú lateral",bool(vis) and 'Asistente IA' in vis['txt'])
            else: chk("en el móvil cabe en la barra sin cortarse",await E("(()=>{const e=document.getElementById('tabAI').getBoundingClientRect();return e.right<=innerWidth+1&&e.left>=0})()"))
            await E("document.getElementById('tabAI').click();0");await pg.wait_for_timeout(600)
            chk("al tocarlo se abre el asistente con las 7 tareas",await E("document.querySelectorAll('.iax-card').length")==7)
            chk("las tareas llevan iconos SVG (nada de emoji)",await E("(()=>{const c=[...document.querySelectorAll('.iax-card .iax-ic')];return c.length===7&&c.every(x=>!!x.querySelector('svg')&&!/[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}]/u.test(x.textContent))})()"))
            await E("closeModal();role='Alumno';renderAll();0");await pg.wait_for_timeout(3600)
            chk("un alumno no lo ve",await E("(()=>{const e=document.getElementById('tabAI');return !e||getComputedStyle(e).display==='none'})()"))
            if W>700:
                await E("role='Profesor';renderAll();goTab('Herramientas');0");await pg.wait_for_timeout(3600)
                chk("en Herramientas los iconos de «Crear con IA» son SVG y distintos entre sí",await E("(()=>{const t=[...document.querySelectorAll('.tx-gai .tx-t .tx-i')];const h=t.map(x=>x.innerHTML);return t.length===8&&t.every(x=>!!x.querySelector('svg'))&&new Set(h).size===8})()"))
                ic=await E("(()=>{const m={};for(const k of ['timer','ruleta','board','groups','exams','bank','points','report','dm','buzon','lib','cards']){const t=TOOLS[k];m[k]=t&&t[2]}return m})()")
                dup={}
                for k,v in ic.items(): dup.setdefault(v,[]).append(k)
                rep={v:k for v,k in dup.items() if len(k)>1}
                chk("las herramientas de la clase no repiten icono",not rep,rep)
                await E("modal('photo');0");await pg.wait_for_timeout(500)
                await E("document.querySelector('#modalFields input').focus();0");await pg.wait_for_timeout(300)
                chk("un campo de texto con foco ya no lleva el segundo contorno (outline)",await E("getComputedStyle(document.activeElement).outlineStyle")=='none',await E("getComputedStyle(document.activeElement).outline"))
            await b.close()
            print("  errores JS:",errs[:2])
    print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
