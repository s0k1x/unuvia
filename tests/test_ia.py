import asyncio,json,re,subprocess,os,sys
from playwright.async_api import async_playwright
FAKE=r"""
(()=>{const chain=()=>new Proxy(function(){},{get:(t,p)=>p==='then'?(r=>r({data:[],error:null})):chain(),apply:()=>chain()});
window.__calls=[];window.__mode='ok';window.__long=false;
const ej=(n)=>{const E=[
 {tipo:'completar',enunciado:'El numerador está _____ de la fracción.',solucion:'arriba'},
 {tipo:'test',enunciado:'¿Cuánto es 1/2 en decimal?',opciones:['0,5','2','1','0,2'],correcta:0},
 {tipo:'vf',enunciado:'1/3 es mayor que 1/2.',verdadero:false},
 {tipo:'corta',enunciado:'¿Cuál es el denominador de 3/4?',solucion:'4'},
 {tipo:'relacionar',enunciado:'Une cada fracción con su decimal.',pares:[{a:'1/2',b:'0,5'},{a:'1/4',b:'0,25'},{a:'3/4',b:'0,75'},{a:'1/5',b:'0,2'}]},
 {tipo:'desarrollo',enunciado:'Explica con tus palabras qué es una fracción y pon un ejemplo de la vida diaria.',solucion:'Una parte de un todo; por ejemplo, media pizza.'},
 {tipo:'problema',enunciado:'Ana come 1/4 de una pizza y Luis 2/4. ¿Qué parte de la pizza queda?',solucion:'Queda 1/4. (1/4 + 2/4 = 3/4; 1 - 3/4 = 1/4)'}];
 const out=[];for(let i=0;i<n;i++)out.push(JSON.parse(JSON.stringify(E[i%E.length])));return out};
const DOCS={
 ficha:()=>({kind:'ficha',titulo:'Las fracciones',instrucciones:'Resuelve los ejercicios con calma.',ejercicios:ej(window.__long?18:7)}),
 examen:()=>({kind:'examen',titulo:'Examen: Las fracciones',instrucciones:'Lee bien cada pregunta.',minutos:50,total:10,preguntas:ej(window.__long?20:7).map((x,i)=>Object.assign(x,{puntos:i%3===0?2:1,criterios:(x.tipo==='desarrollo'||x.tipo==='problema')?'Define y pone un ejemplo':undefined}))}),
 resumen:()=>({kind:'resumen',titulo:'La célula',resumen:'La célula es la unidad básica de los seres vivos.',puntos_clave:['Tiene membrana','Tiene núcleo','Produce energía'],secciones:[{titulo:'Partes',puntos:['Membrana','Núcleo','Citoplasma']}],glosario:[{termino:'ADN',definicion:'Material genético'}],preguntas_repaso:['¿Qué es una célula?']}),
 rubrica:()=>({kind:'rubrica',titulo:'Rúbrica: exposición oral',niveles:['Insuficiente','Suficiente','Notable','Sobresaliente'],criterios:[{nombre:'Contenido',peso:40,descriptores:['Faltan ideas','Ideas básicas','Ideas claras','Ideas claras y bien conectadas']},{nombre:'Voz',peso:30,descriptores:['No se oye','Se oye poco','Se oye bien','Voz clara y expresiva']},{nombre:'Tiempo',peso:30,descriptores:['Muy corto','Ajustado','Adecuado','Perfecto']}]}),
 tarjetas:()=>({kind:'tarjetas',tarjetas:[{pregunta:'Capital de Francia',respuesta:'París'},{pregunta:'Capital de Italia',respuesta:'Roma'},{pregunta:'Capital de España',respuesta:'Madrid'}]}),
 anuncio:()=>({kind:'anuncio',texto:'Mañana salimos de excursión al museo. Traed bocadillo y una botella de agua.'})};
window.__fakeSb={auth:{getSession:async()=>({data:{session:null}}),onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),signOut:async()=>{},getUser:async()=>({data:{user:null}})},
 from:()=>chain(),rpc:()=>chain(),channel:()=>{const c={on:()=>c,subscribe:()=>c};return c},removeChannel(){},storage:{from:()=>chain()},
 functions:{invoke:async(n,o)=>{window.__calls.push([n,o]);const M=window.__mode,task=o.body.task;
   const ctx=(s,msg)=>({status:s,json:async()=>({error:msg})});
   if(M==='403')return {data:null,error:{context:ctx(403,'Tu cuenta no tiene activada la IA. Pídeselo al administrador de Unuvia.')}};
   if(task==='questions')return {data:{ok:true,remaining:20,items:[{tipo:'vf',pregunta:'x',correcta:true,explicacion:''}]},error:null};
   return {data:{ok:true,task,doc:DOCS[task](),marca:!['tarjetas','anuncio'].includes(task),remaining:25},error:null}}}};})();
"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=1,is_mobile=True,has_touch=True,permissions=["clipboard-read","clipboard-write"])
        pg=await ctx.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)[:200]))
        async def patch(route):
            r=await route.fetch(); t=await r.text()
            await route.fulfill(response=r,body=t.replace('sb=window.supabase?','sb=window.__fakeSb?window.__fakeSb:window.supabase?',1))
        await pg.route("**/app.js*",patch);await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
        await pg.add_init_script(FAKE+"try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','light')}catch(e){}")
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(1500)
        await pg.evaluate("acceptCookies();launchApp(document.getElementById('startLogin'))");await pg.wait_for_timeout(1300)
        await pg.evaluate("document.querySelector('input[value=local]').click();document.getElementById('localName').value='Marga';document.getElementById('localLoginButton').click()");await pg.wait_for_timeout(1500)
        await pg.evaluate("settings.toured=true;addClass({id:'c1',name:'1º FPB Informática',code:'MT-1',role:'Profesor',emoji:'💻',color:'#008cff'});data.members.push({u:'u2',n:'Alumno Prueba',r:'Alumno'});renderAll();0");await pg.wait_for_timeout(800)
        ok=0;bad=0
        def chk(name,cond,extra=''):
            nonlocal ok,bad
            if cond: ok+=1;print('  ✓',name)
            else: bad+=1;print('  ✗',name,extra)
        E=lambda s: pg.evaluate(s)
        print("Apagado por defecto")
        await E("goTab('Herramientas');0");await pg.wait_for_timeout(500)
        chk("sin interruptor: no hay grupo «Crear con IA» en Herramientas",not await E("!!document.querySelector('.tx-gai')"))
        await E("modal('post');0");await pg.wait_for_timeout(300)
        chk("sin interruptor: no hay «Redactar con IA» en el anuncio",not await E("!!document.querySelector('.iax-mini')"))
        await E("closeModal();toolOpen('cards');0");await pg.wait_for_timeout(500)
        chk("sin interruptor: no hay «Crear tarjetas con Gemini»",not await E("/Crear tarjetas con Gemini/.test(document.getElementById('modalFields').textContent)"))
        await E("closeModal();0")
        print("Encendido")
        await E("CFG.features={gemini:true};renderToolsView();goTab('Herramientas');0");await pg.wait_for_timeout(600)
        chk("profesor + interruptor: aparece el grupo «Crear con IA» en Herramientas",await E("document.querySelectorAll('.tx-gai .tx-t').length===8"))
        await pg.screenshot(path='/home/claude/ia_tools.png')
        await E("iaxOpen();0");await pg.wait_for_timeout(500)
        chk("abre el asistente con 7 opciones",await E("document.querySelectorAll('.iax-card').length")==7)
        await pg.screenshot(path='/home/claude/ia_home.png')
        await E("iaxPick('ficha');0");await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/ia_form.png')
        # sin tema → no llama
        await E("iaxGo();0");await pg.wait_for_timeout(200)
        chk("ficha sin tema: no llama a la función",await E("window.__calls.length")==0)
        await E("document.getElementById('iaxTopic').value='Las fracciones';document.getElementById('iaxLevel').value='1º ESO';document.getElementById('iaxN').value='7';0")
        await E("iaxKind('vf');iaxKind('relacionar');iaxKind('problema');0")
        await E("iaxGo();0");await pg.wait_for_timeout(600)
        call=(await E("window.__calls"))[-1][1]['body']
        chk("la petición lleva solo tarea, tema, nivel, apuntes, idioma, tipos y cantidad",set(call)=={'task','topic','level','base','lang','kinds','n'} and call['task']=='ficha' and call['n']==7 and call['kinds']['relacionar'] is True,json.dumps(call))
        chk("se abre el documento imprimible",await E("!!document.querySelector('#rep.ad .ad-al')&&!!document.querySelector('#rep.ad .ad-sol')"))
        chk("tiene la marca de Unuvia (fija para imprimir y una al pie de cada hoja)",await E("!!document.querySelector('#rep > .uv-wm')&&document.querySelectorAll('#rep .uv-wm-in').length===2"))
        chk("ficha: 7 ejercicios con huecos, opciones, V/F, líneas, relacionar y caja de problema",await E("(()=>{const s=document.querySelector('.ad-al');return s.querySelectorAll('.ad-q').length===7&&!!s.querySelector('.ad-bl')&&!!s.querySelector('.ad-opts')&&!!s.querySelector('.ad-vf')&&!!s.querySelector('.ad-ln')&&!!s.querySelector('.ad-rel')&&!!s.querySelector('.ad-bx')})()"))
        chk("ficha: hoja del alumno sin soluciones (no aparece «arriba» ni la respuesta del problema)",not await E("/Queda 1\\/4|Una parte de un todo/.test(document.querySelector('.ad-al').textContent)"))
        chk("ficha: el solucionario sí las lleva",await E("/Queda 1\\/4/.test(document.querySelector('.ad-sol').textContent)&&/Solucionario/.test(document.querySelector('.ad-sol').textContent)"))
        chk("relacionar: la columna B está desordenada y la solución coincide",await E("""(()=>{const it=IAX.doc.ejercicios.find(x=>x.tipo==='relacionar'),o=adxOrd(it);const ident=o.every((v,i)=>v===i);const right=[...document.querySelectorAll('.ad-al .ad-rel ul li')].map(l=>l.textContent.replace(/^[A-Z]\\)\\s*/,''));const sol=adxAs(it);
          return !ident&&right.length===4&&it.pares.every((p,k)=>{const letter=String.fromCharCode(65+right.indexOf(p.b));return sol.includes((k+1)+' → '+letter)})})()"""))
        await pg.screenshot(path='/home/claude/ia_doc_m.png')
        await E("adxTog('sol',false);0")
        chk("quitar «Solucionario» lo oculta",await E("getComputedStyle(document.querySelector('.ad-sol')).display")=='none')
        await E("adxTog('sol',true);adxTog('al',false);0")
        chk("quitar «Hoja del alumno» la oculta",await E("getComputedStyle(document.querySelector('.ad-al')).display")=='none')
        await E("adxTog('al',true);0")
        await E("adxCopy();0");await pg.wait_for_timeout(300)
        clip=await E("navigator.clipboard.readText()")
        chk("«Copiar texto» incluye ejercicios, soluciones y la marca",('SOLUCIONES' in clip) and ('Creado con Unuvia' in clip),clip[-120:])
        await E("iaxBack();0");await pg.wait_for_timeout(400)
        chk("«Volver» regresa al formulario con lo que escribí",await E("document.getElementById('iaxTopic').value")=='Las fracciones')
        print("Examen")
        await E("iaxOpen('examen');document.getElementById('iaxTopic').value='Las fracciones';document.getElementById('iaxMin').value='45';document.getElementById('iaxTot').value='10';0");await pg.wait_for_timeout(300)
        await E("iaxGo();0");await pg.wait_for_timeout(600)
        call=(await E("window.__calls"))[-1][1]['body']
        chk("examen: envía minutos y puntos totales",call['task']=='examen' and call['minutos']==45 and call['total']==10,json.dumps(call))
        chk("examen: muestra tiempo, puntuación total y puntos por pregunta",await E("(()=>{const s=document.querySelector('.ad-al').textContent;return /Tiempo: 50 min/.test(s)&&/Puntuación total: 10 puntos/.test(s)&&/\\(2 puntos\\)/.test(s)&&/\\(1 punto\\)/.test(s)})()"))
        chk("examen: el solucionario trae los criterios",await E("/Se valora: Define y pone un ejemplo/.test(document.querySelector('.ad-sol').textContent)"))
        print("Resumen, rúbrica")
        for t,fx in [('resumen',"document.getElementById('iaxTopic').value='La célula'"),('rubrica',"document.getElementById('iaxTopic').value='Exposición oral'")]:
            await E(f"repClose();iaxOpen('{t}');{fx};0");await pg.wait_for_timeout(250)
            await E("iaxGo();0");await pg.wait_for_timeout(500)
            if t=='resumen': chk("resumen: ideas clave, glosario y para repasar",await E("(()=>{const s=document.querySelector('.ad-al').textContent;return /Ideas clave/.test(s)&&/Glosario/.test(s)&&/Para repasar/.test(s)})()"))
            else:
                chk("rúbrica: tabla con 3 criterios × 4 niveles",await E("document.querySelectorAll('.ad-rb tbody tr').length===3&&document.querySelectorAll('.ad-rb thead th').length===5"))
                await pg.screenshot(path='/home/claude/ia_rub.png')
            chk(f"{t}: lleva la marca y no tiene solucionario",await E("!!document.querySelector('#rep > .uv-wm')&&!document.querySelector('.ad-sol')"))
        print("Tarjetas y anuncio")
        await E("repClose();iaxOpen('tarjetas');document.getElementById('iaxTopic').value='Capitales';0");await pg.wait_for_timeout(250)
        await E("iaxGo();0");await pg.wait_for_timeout(500)
        chk("tarjetas: lista de 3 y NO se abre documento con marca",await E("document.querySelectorAll('.iax-cd').length")==3 and not await E("!!document.getElementById('rep')"))
        await E("iaxMakeDeck();0");await pg.wait_for_timeout(1500)
        chk("«Crear mazo»: rellena título y tarjetas «pregunta | respuesta» en el creador de mazos",await E("(()=>{const T=document.getElementById('cdT'),C=document.getElementById('cdC');return !!T&&T.value==='Capitales'&&C.value.split('\\n').length===3&&/Capital de Francia \\| París/.test(C.value)})()"))
        await E("closeModal();iaxOpen('anuncio');document.getElementById('iaxTopic').value='Excursión mañana';0");await pg.wait_for_timeout(250)
        await E("iaxTone('divertido');iaxGo();0");await pg.wait_for_timeout(500)
        chk("anuncio: el tono llega en la petición",(await E("window.__calls"))[-1][1]['body']['tono']=='divertido')
        await E("iaxUsePost();0");await pg.wait_for_timeout(500)
        chk("«Usar en un anuncio» abre el cuadro de anuncio con el texto",await E("/excursión al museo/.test((document.getElementById('f1')||{}).value||'')"))
        await E("closeModal();0")
        print("Desde otros sitios")
        await E("modal('post');0");await pg.wait_for_timeout(300)
        chk("el cuadro de anuncio tiene «Redactar con IA»",await E("!!document.querySelector('.iax-mini')"))
        await E("document.querySelector('.iax-mini').click();0");await pg.wait_for_timeout(500)
        chk("…y abre el asistente directamente en «Anuncio»",await E("!!document.getElementById('iaxTopic')&&IAX.task==='anuncio'"))
        await E("closeModal();toolOpen('cards');0");await pg.wait_for_timeout(500)
        chk("las tarjetas de estudio tienen «Crear tarjetas con Gemini»",await E("/Crear tarjetas con Gemini/.test(document.getElementById('modalFields').textContent)"))
        await E("closeModal();0")
        print("Errores y permisos")
        await E("window.__mode='403';iaxOpen('ficha');document.getElementById('iaxTopic').value='X';iaxGo();0");await pg.wait_for_timeout(600)
        chk("403: mensaje claro y el botón vuelve a estar disponible",await E("/no tiene activada la IA/.test(document.getElementById('toast').textContent)&&!document.querySelector('.iax .add').disabled"))
        await E("window.__mode='ok';role='Alumno';closeModal();renderToolsView();0");await pg.wait_for_timeout(300)
        chk("rol Alumno: no hay asistente (iaxOn=false)",not await E("iaxOn()"))
        await E("role='Profesor';0")
        print("Marca en más sitios")
        await E("closeModal();repOpen();0");await pg.wait_for_timeout(1500)
        chk("Informes por alumno: llevan también la marca fija",await E("!!document.querySelector('#rep > .uv-wm')&&!!document.querySelector('#rep .rep-f')"))
        await E("repClose();window.__saved=null;saveFile=(n,t)=>{window.__saved=[n,t]};data.messages=[{id:'m1',n:'Lucía',t:'Hola',ts:Date.now(),me:false}];exportChat();0");await pg.wait_for_timeout(300)
        sv=await E("window.__saved")
        chk("exportar el chat añade «Exportado de Unuvia»",bool(sv) and 'Exportado de Unuvia · unuvia.es' in sv[1],sv)
        print("errores JS:",errs[:3]); print(f"\n{ok} correctas, {bad} fallos")
        # --------- PDF real: marca en CADA página ---------
        await E("window.__long=true;repClose();iaxOpen('examen');document.getElementById('iaxTopic').value='Las fracciones';iaxGo();0");await pg.wait_for_timeout(700)
        await E("document.body.classList.add('printing');0")
        await pg.pdf(path='/home/claude/exam.pdf',format='A4',print_background=True,prefer_css_page_size=True)
        await b.close()
asyncio.run(main())
