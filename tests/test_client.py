import asyncio,json,re
from playwright.async_api import async_playwright
FAKE="""
(()=>{const chain=()=>new Proxy(function(){},{get:(t,p)=>p==='then'?(r=>r({data:[],error:null})):chain(),apply:()=>chain()});
window.__calls=[];window.__mode='ok';window.__delay=0;
window.__fakeSb={auth:{getSession:async()=>({data:{session:null}}),onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),signOut:async()=>{},getUser:async()=>({data:{user:null}})},
 from:()=>chain(),rpc:()=>chain(),channel:()=>{const c={on:()=>c,subscribe:()=>c};return c},removeChannel(){},storage:{from:()=>chain()},
 functions:{invoke:async(n,o)=>{window.__calls.push([n,o]);if(window.__delay)await new Promise(r=>setTimeout(r,window.__delay));
   const M=window.__mode;
   if(M==='ok')return {data:{ok:true,remaining:27,items:[{tipo:'test',pregunta:'¿Cuánto es 1/2 + 1/2?',opciones:['1','2','1/4','0'],correcta:0,explicacion:'Suman un entero.'},{tipo:'vf',pregunta:'1/2 es mayor que 1/3.',correcta:true,explicacion:'Sí.'},{tipo:'corta',pregunta:'Numerador de 3/4',respuestas:['3'],explicacion:'Arriba.'}]},error:null};
   const ctx=(s,msg)=>({status:s,json:async()=>({error:msg})});
   if(M==='403')return {data:null,error:{context:ctx(403,'Tu cuenta no tiene activada la IA. Pídeselo al administrador de Unuvia.')}};
   if(M==='429')return {data:null,error:{context:ctx(429,'Has llegado al límite de hoy. Mañana podrás seguir.')}};
   if(M==='404')return {data:null,error:{context:{status:404,json:async()=>{throw new Error('x')}}}};
   if(M==='empty')return {data:{ok:true,items:[]},error:null};
   if(M==='throw')throw new Error('red');}}};})();
"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=1,is_mobile=True,has_touch=True)
        pg=await ctx.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)[:200]))
        async def patch(route):
            r=await route.fetch(); t=await r.text()
            assert 'sb=window.supabase?' in t
            await route.fulfill(response=r,body=t.replace('sb=window.supabase?','sb=window.__fakeSb?window.__fakeSb:window.supabase?',1))
        await pg.route("**/app.js*",patch)
        await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
        await pg.add_init_script(FAKE+"try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','dark')}catch(e){}")
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(1500)
        await pg.evaluate("acceptCookies();launchApp(document.getElementById('startLogin'))");await pg.wait_for_timeout(1300)
        await pg.evaluate("document.querySelector('input[value=local]').click();document.getElementById('localName').value='Marga';document.getElementById('localLoginButton').click()");await pg.wait_for_timeout(1500)
        await pg.evaluate("settings.toured=true;addClass({id:'c1',name:'2º FPB',code:'MT-1',role:'Profesor',emoji:'📚',color:'#008cff'});B23_OK=true;BX_OK=false;toolOpen('bank');BK.view='ai';bankPaint()")
        await pg.wait_for_timeout(900)
        ok=0;bad=0
        def chk(name,cond,extra=''):
            nonlocal ok,bad
            if cond: ok+=1;print('  ✓',name)
            else: bad+=1;print('  ✗',name,extra)
        has=lambda: pg.evaluate("!!document.querySelector('.ai-gem')")
        hero=lambda: pg.evaluate("document.querySelector('.ai-hero small').textContent")
        print("Apagado por defecto")
        print("   rol:",await pg.evaluate("role"),"· geminiOn:",await pg.evaluate("geminiOn()"))
        chk("sin interruptor → no aparece la tarjeta de Gemini",not await has())
        chk("sin interruptor → el texto sigue diciendo que no se envía nada a ninguna IA","no envía nada a ninguna IA" in await hero(),await hero())
        print("Encendido por el administrador")
        await pg.evaluate("CFG.features={gemini:true};bankPaint()")
        chk("con interruptor + profesor → aparece la tarjeta",await has())
        h=await hero(); chk("el texto avisa de que se envía a Google solo al pulsar",("Google" in h) and ("solo si pulsas" in h),h)
        await pg.evaluate("role='Alumno';bankPaint()")
        chk("con interruptor pero rol Alumno → NO aparece",not await has())
        await pg.evaluate("role='Profesor';bankPaint()")
        print("Generar")
        await pg.evaluate("AI.topic='';AI.base='';bankPaint()")
        await pg.evaluate("document.querySelector('.ai-gem .add').click()");await pg.wait_for_timeout(300)
        chk("sin tema ni apuntes → no llama a la función",await pg.evaluate("window.__calls.length")==0)
        await pg.evaluate("AI.topic='Fracciones';AI.level='1º FPB';AI.n=6;bankPaint()")
        await pg.evaluate("window.__delay=600;document.querySelector('.ai-gem .add').click()");await pg.wait_for_timeout(200)
        busy=await pg.evaluate("(()=>{const b=document.querySelector('.ai-gem .add');return [b.disabled,b.textContent]})()")
        chk("mientras espera: botón desactivado y «Generando…»",busy==[True,'Generando…'],busy)
        await pg.evaluate("document.querySelector('.ai-gem .add').click()");await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(900)
        calls=await pg.evaluate("window.__calls")
        chk("un clic doble solo hace una llamada",len(calls)==1,len(calls))
        body=calls[0][1]['body'] if calls else {}
        chk("envía solo tarea, tema, nivel, cantidad, tipos, apuntes e idioma (nada de alumnos ni de la clase)",set(body)=={'task','topic','level','n','types','base','lang'} and body['task']=='questions' and body['topic']=='Fracciones' and body['n']==6,json.dumps(body))
        nq=await pg.evaluate("document.querySelectorAll('.ai-q').length")
        chk("las preguntas pasan por la revisión de siempre (3 tarjetas para revisar)",nq==3,nq)
        chk("se puede guardar (botón «Guardar 3 en el banco»)",await pg.evaluate("/Guardar 3/.test(document.querySelector('.ai-go:last-of-type')?.textContent||document.body.textContent)"))
        chk("muestra cuántos usos quedan",await pg.evaluate("/te quedan 27/.test(document.getElementById('toast').textContent)"))
        await pg.screenshot(path='/home/claude/gem_ok.png')
        print("Errores (mensajes claros y botón vuelve a estar disponible)")
        for mode,frag in [('403','no tiene activada la IA'),('429','límite de hoy'),('404','todavía no está activada'),('empty','no ha devuelto preguntas'),('throw','Avisa al administrador')]:
            await pg.evaluate(f"window.__mode='{mode}';window.__delay=0;window.__calls=[];AI.items=null;AI.errs=[];bankPaint();document.querySelector('.ai-gem .add').click()");await pg.wait_for_timeout(500)
            t=await pg.evaluate("document.getElementById('toast').textContent"); en=await pg.evaluate("!document.querySelector('.ai-gem .add').disabled")
            chk(f"{mode}: «{frag}» y botón disponible",frag in t and en,(t,en))
        print("Panel del administrador")
        await pg.evaluate("CFG.features={};0");html=await pg.evaluate("admpFunc()")
        chk("hay interruptor «Gemini» y está apagado",('Gemini: preguntas con IA' in html) and not re.search(r'Gemini: preguntas con IA.*?type="checkbox"\s+checked',html,re.S))
        await pg.evaluate("window.__sets=[];admSet=(k,v)=>{window.__sets.push([k,v])};0")
        await pg.evaluate("void admFeat('gemini',true)");await pg.wait_for_timeout(300)
        chk("al activar pide confirmación y avisa de la política de privacidad y de la edad",await pg.evaluate("!document.getElementById('ask').classList.contains('hidden')&&/pol[ií]tica de privacidad/.test(document.getElementById('askD').textContent)&&/18 a/.test(document.getElementById('askD').textContent)"))
        await pg.evaluate("document.getElementById('askNo').click()");await pg.wait_for_timeout(200)
        chk("«Todavía no» → no se guarda nada",await pg.evaluate("window.__sets.length")==0)
        await pg.evaluate("void admFeat('gemini',true)");await pg.wait_for_timeout(200);await pg.evaluate("document.getElementById('askOk').click()");await pg.wait_for_timeout(200)
        chk("«Activar» → se guarda features.gemini=true",json.dumps(await pg.evaluate("window.__sets"))=='[["features", {"live": true, "tools": true, "shop": true, "gemini": true}]]',await pg.evaluate("JSON.stringify(window.__sets)"))
        await pg.evaluate("void admFeat('gemini',false)");await pg.wait_for_timeout(200)
        chk("apagarlo no pide confirmación",await pg.evaluate("document.getElementById('ask').classList.contains('hidden')"))
        print("errores JS:",errs[:3]); print(f"\n{ok} correctas, {bad} fallos")
        await b.close()
asyncio.run(main())
