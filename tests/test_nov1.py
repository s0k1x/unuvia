import asyncio,json,base64,sys
from playwright.async_api import async_playwright
FAKE=r"""
(()=>{const chain=()=>new Proxy(function(){},{get:(t,p)=>p==='then'?(r=>r({data:[],error:null})):chain(),apply:()=>chain()});
window.__rpc=[];window.__ins=[];window.__calls=[];window.__rpcRes={};window.__down=[];
const DOC={examen:()=>({kind:'examen',titulo:'Examen de fracciones',instrucciones:'Lee bien.',minutos:30,total:10,preguntas:[
 {tipo:'test',enunciado:'1/2 + 1/2 = ?',opciones:['1','2','1/4','0'],correcta:0,puntos:2},
 {tipo:'vf',enunciado:'1/3 es mayor que 1/2.',verdadero:false,puntos:2},
 {tipo:'corta',enunciado:'Nombre del número de abajo de una fracción',solucion:'denominador',puntos:2},
 {tipo:'desarrollo',enunciado:'Explica qué es una fracción.',solucion:'Parte de un todo',criterios:'claridad',puntos:4}]}),
 rubrica:()=>({kind:'rubrica',titulo:'Exposición oral',niveles:['Insuf.','Suf.','Bien','Excel.'],criterios:[{nombre:'Contenido',peso:40,descriptores:['a','b','c','d']},{nombre:'Expresión',peso:35,descriptores:['a','b','c','d']},{nombre:'Tiempo',peso:25,descriptores:['a','b','c','d']}]}),
 ficha:()=>({kind:'ficha',titulo:'Ficha',instrucciones:'x',ejercicios:[{tipo:'corta',enunciado:'a?',solucion:'a'},{tipo:'corta',enunciado:'b?',solucion:'b'}]})};
window.__fakeSb={auth:{getSession:async()=>({data:{session:null}}),onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),signOut:async()=>{},getUser:async()=>({data:{user:null}})},
 from:t=>new Proxy(chain(),{get:(tg,k)=>k==='insert'?(row)=>{window.__ins.push([t,row]);return window.__insErr?{then:r=>r({error:{message:'relation does not exist'}})}:chain()}:tg[k]}),
 rpc:(n,a)=>{window.__rpc.push([n,a||null]);const r=window.__rpcRes[n];return Promise.resolve(r?(typeof r==='function'?r(a):r):{data:null,error:null})},
 channel:()=>{const c={on:()=>c,subscribe:()=>c};return c},removeChannel(){},storage:{from:()=>chain()},
 functions:{invoke:async(n,o)=>{window.__calls.push([n,o]);const t=o.body.task;return {data:{ok:true,task:t,doc:DOC[t](),marca:true,remaining:20},error:null}}}};})();
"""
SETUP="""()=>{settings.toured=true;
 addClass({id:'c1',name:'1º FPB Informática',code:'MT-4827',role:'Profesor',emoji:'💻',color:'#008cff',course:'1º FPB'});
 CFG.features={gemini:true};
 const y=(new Date).getMonth()>=7?(new Date).getFullYear():(new Date).getFullYear()-1;
 data.members=[{u:'u1',n:'Marga Profe',r:'Profesor'},{u:'u2',n:'Lucía Pérez',r:'Alumno'},{u:'u3',n:'Pablo Ruiz',r:'Alumno'},{u:'u4',n:'Ana Gómez',r:'Alumno'}];
 const T1=y+'-10-15',T2=(y+1)+'-02-10';
 const mk=(id,type,title,due,subs)=>({id,type,title,desc:'',topic:'',due,pts:10,link:'',ts:Date.now(),subs,files:[],opts:[],assg:[],rub:[]});
 data.work=[
  mk('w1','tarea','Tarea fracciones',T1,{'Lucía Pérez':{st:'entregada',grade:8,ret:true,ts:1},'Pablo Ruiz':{st:'entregada',grade:4,ret:true,ts:1}}),
  mk('w2','tarea','Examen tema 1',T1,{'Lucía Pérez':{st:'entregada',grade:6,ret:true,ts:1},'Pablo Ruiz':{st:'entregada',grade:7,ret:true,ts:1}}),
  mk('w3','pregunta','Debate en clase',T2,{'Lucía Pérez':{st:'entregada',grade:10,ret:true,ts:1}})];
 renderAll();0}"""
async def boot(p,W=1280,H=800):
    b=await p.chromium.launch(args=["--no-sandbox"])
    ctx=await b.new_context(viewport={"width":W,"height":H},device_scale_factor=1,is_mobile=W<700,has_touch=W<700,accept_downloads=True)
    pg=await ctx.new_page(); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)[:200]))
    async def patch(route):
        r=await route.fetch(); t=await r.text()
        await route.fulfill(response=r,body=t.replace('sb=window.supabase?','sb=window.__fakeSb?window.__fakeSb:window.supabase?',1))
    await pg.route("**/app.js*",patch);await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
    await pg.add_init_script(FAKE+"try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','dark')}catch(e){}")
    return b,pg,errs
async def login(pg):
    await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(1400)
    await pg.evaluate("acceptCookies();launchApp(document.getElementById('startLogin'))");await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelector('input[value=local]').click();document.getElementById('localName').value='Marga Profe';document.getElementById('localLoginButton').click()");await pg.wait_for_timeout(1400)
    await pg.evaluate(SETUP);await pg.wait_for_timeout(500)
    await pg.evaluate("document.querySelectorAll('button').forEach(b=>/^Aceptar$/.test(b.textContent.trim())&&b.click())");await pg.wait_for_timeout(400)
ok=bad=0
def chk(n,c,x=''):
    global ok,bad
    if c: ok+=1;print('  ✓',n)
    else: bad+=1;print('  ✗',n,x)
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p);await login(pg);E=pg.evaluate
        print("MODERACIÓN")
        bad_txt=["Ana,fran Y Zaira orgia en casa de mario","violar a Fran","tengo ganas de violar a alguien","sexo anal","que te jodan","te voy a violar","pasa pack","mandame fotos desnuda","hijo de puta","te voy a matar","enseñame las tetas","Eres un imbécil","vete a la mierda"]
        good_txt=["La célula es la unidad básica de la vida","El sexo biológico se determina por los cromosomas","Los romanos conquistaron Hispania","No sé cómo matar el tiempo","Análisis de datos de la clase","Tema XXX del temario","La violación de la norma tiene sanción","Sin pollo no hay paella","Hoy toca pasar lista y repasar","Se reparte el pack de ejercicios"]
        flag=await E("(a)=>{const P=MODE.prep([]);return a.map(t=>MODE.scan(t,P).length>0)}",bad_txt)
        chk("detecta lo de tu captura y lo que faltaba ("+str(sum(flag))+" de "+str(len(bad_txt))+")",all(flag),[t for t,f in zip(bad_txt,flag) if not f])
        okf=await E("(a)=>{const P=MODE.prep([]);return a.map(t=>MODE.scan(t,P).length>0)}",good_txt)
        chk("NO marca frases normales de clase (0 falsos positivos de "+str(len(good_txt))+")",not any(okf),[t for t,f in zip(good_txt,okf) if f])
        chk("una clase nueva ya tiene la moderación en «Ocultar» por defecto",await E("modCfg().level")=="hide")
        await E("""data.events=[{id:'e1',i:'📅',t:'Orgia en casa de mario',s:'Fiesta tras el examen',d:'2099-01-01'}];data.sched=[{id:'s1',t:'Clase de follar',day:0,h:'08:30',r:'A1'}];renderAll();goTab('Horario');0""");await pg.wait_for_timeout(600)
        t=await E("document.getElementById('classView').innerText")
        chk("el filtro tapa el horario (antes no lo hacía)",'follar' not in t and 'Clase de' in t,t[:0])
        await E("goTab('Inicio');0");await pg.wait_for_timeout(500)
        t=await E("document.getElementById('classView').innerText")
        chk("el filtro tapa los eventos de Inicio",'Orgia' not in t and 'Fiesta' in t)
        await E("data.members.push({u:'u9',n:'Puto Amo',r:'Alumno'});renderAll();goTab('Personas');0");await pg.wait_for_timeout(600)
        chk("el filtro tapa nombres de personas",'Puto' not in await E("document.getElementById('classView').innerText"))
        await E("data.posts=[{id:'p1',n:'Pablo Ruiz',au:'u3',t:'hola a todos',ts:Date.now(),pin:false,poll:null,img:null,comments:[]}];data.messages=[{id:'m1',n:'Pablo Ruiz',au:'u3',t:'jaja',ts:Date.now(),type:'text'}];renderAll();0")
        await E("postMenu('p1');0");await pg.wait_for_timeout(400)
        chk("en los anuncios de otras personas sale «Reportar»",'Reportar' in await E("document.body.innerText"))
        await pg.keyboard.press("Escape");await E("document.querySelectorAll('.ctxm,.menu,#ctxMenu').forEach(e=>e.remove());0")
        await E("data.posts[0].n=user;data.posts[0].au=authUid;postMenu('p1');0");await pg.wait_for_timeout(400)
        chk("en los tuyos NO sale «Reportar»",'Reportar' not in await E("[...document.querySelectorAll('.hmenu,.ctxm,.menu,#ctxMenu,[role=menu]')].map(e=>e.innerText).join(' ')||''"))
        await E("data.posts[0].n='Pablo Ruiz';data.posts[0].au='u3';document.querySelectorAll('[role=menu]').forEach(e=>e.remove());reportOpen('post','p1');0");await pg.wait_for_timeout(300)
        chk("el aviso pide un motivo antes de enviar",await E("document.querySelector('.rp-go').disabled")==True)
        await E("document.querySelector('.rp-r .chip').click();0");await E("reportSend();0");await pg.wait_for_timeout(400)
        r=await E("window.__rpc.filter(x=>x[0]==='report_item')")
        chk("«Enviar aviso» llama a report_item con clase, autor y texto",len(r)==1 and r[0][1]['p_class']=='c1' and r[0][1]['p_kind']=='post' and r[0][1]['p_author']=='Pablo Ruiz' and r[0][1]['p_snippet']=='hola a todos' and r[0][1]['p_reason']=='Insultos o acoso',r)
        await E("window.__rpcRes.reports_list={data:[{id:'r1',class_id:'c1',author:'Pablo Ruiz',author_id:'u3',reason:'Insultos o acoso',snippet:'eres un imbecil de mierda',created_at:new Date().toISOString(),status:'open'}],error:null};toolOpen('mod');0");await pg.wait_for_timeout(1200)
        chk("la cola del profesor muestra el aviso con el texto tapado",await E("(()=>{const t=document.querySelector('.rq-t');return !!t&&!/mierda/.test(t.textContent)&&t.textContent.length>5})()"))
        await E("document.querySelector('.rq-a .mini-btn').click();0")
        chk("«Ver el texto completo» lo enseña y se puede volver a tapar",await E("document.querySelector('.rq-t').textContent")=='eres un imbecil de mierda')
        await E("document.querySelector('.rq-a .add').click();0");await pg.wait_for_timeout(500)
        chk("«Hecho» llama a report_resolve y quita el aviso",await E("window.__rpc.some(x=>x[0]==='report_resolve'&&x[1].p_status==='actioned')&&!document.querySelector('.rq-it')"))
        await E("closeModal();window.__rpcRes.reports_list={data:null,error:{message:'Could not find the function public.reports_list'}};toolOpen('mod');0");await pg.wait_for_timeout(1000)
        chk("sin el SQL avisa de ejecutar 2_moderacion.sql (sin romperse)",'2_moderacion.sql' in await E("document.getElementById('modalFields').innerText"))
        await E("closeModal();0")
        print("errores JS:",errs[:3]);await b.close()
    print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
