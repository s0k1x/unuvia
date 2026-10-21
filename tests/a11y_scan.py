import asyncio,sys,collections
sys.argv=[sys.argv[0]]
exec(open('/home/claude/test_nov1.py').read().split("async def main():")[0])
SCAN="""()=>{const bad=[];const vis=e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.visibility!=='hidden'&&c.display!=='none'};
 const name=e=>(e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.title||e.textContent.trim()||(e.querySelector('img[alt]')||{}).alt||'');
 document.querySelectorAll('button,[role=button],a[href]').forEach(e=>{if(vis(e)&&!name(e)&&!e.closest('[aria-hidden=true]'))bad.push('SIN NOMBRE · '+e.tagName.toLowerCase()+' · '+(e.id||e.className.toString().slice(0,40)||e.outerHTML.slice(0,50)))});
 document.querySelectorAll('input,textarea,select').forEach(e=>{if(e.type==='hidden'||e.type==='file'||!vis(e))return;if(!(e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.id&&document.querySelector('label[for="'+e.id+'"]')||e.closest('label')||e.title))bad.push('CAMPO SIN ETIQUETA · '+e.tagName.toLowerCase()+' · '+(e.id||e.name||e.placeholder||e.className.toString().slice(0,30)))});
 document.querySelectorAll('img').forEach(e=>{if(vis(e)&&!e.hasAttribute('alt'))bad.push('IMG SIN ALT · '+(e.src||'').slice(-30))});
 const h=document.documentElement;if(!h.lang)bad.push('HTML SIN lang');
 document.querySelectorAll('[role=dialog],[role=alertdialog]').forEach(e=>{if(vis(e)&&!(e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')))bad.push('DIÁLOGO SIN NOMBRE · '+(e.id||e.className))});
 return bad}"""
async def main():
    async with async_playwright() as p:
        allbad=collections.Counter()
        for (W,H,tag) in [(390,844,'móvil'),(1280,800,'PC')]:
            b,pg,errs=await boot(p,W,H);E=pg.evaluate
            await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(1500)
            await E("acceptCookies();launchApp(document.getElementById('startLogin'));0");await pg.wait_for_timeout(1000)
            for x in await E(SCAN): allbad[tag+' · entrada · '+x]+=1
            await pg.reload();await login(pg)
            for v in ['Inicio','Herramientas','Calendario','Trabajo','Horario','Ahora','Notas','Personas','Chat']:
                await E(f"goTab('{v}');0");await pg.wait_for_timeout(500)
                for x in await E(SCAN): allbad[tag+' · '+v+' · '+x]+=1
            for m in ['event','task','post','settings','join','class']:
                await E(f"modal('{m}');0");await pg.wait_for_timeout(450)
                for x in await E(SCAN): allbad[tag+' · modal '+m+' · '+x]+=1
                await E("closeModal();0")
            await b.close()
        by=collections.Counter(k.split(' · ',2)[2] for k in allbad)
        print("PROBLEMAS DISTINTOS:",len(by))
        for k,n in by.most_common(40): print(f"  {n:3d} · {k}")
asyncio.run(main())
