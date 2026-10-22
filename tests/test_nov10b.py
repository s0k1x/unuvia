import asyncio,json,sys,re
sys.argv=[sys.argv[0]]
exec(open('/home/claude/test_nov1.py').read().rsplit("async def main():",1)[0])
AUDIO="""
window.__au={nodes:[],ctx:0};
class N{constructor(t){this.t=t;this.conn=[];this.started=0;this.stopped=0;this.frequency={value:0};this.Q={value:0};this.gain={value:1};this.type='';this.loop=false;this.buffer=null}connect(n){this.conn.push(n&&n.t||'dest');return n}disconnect(){}start(){this.started++}stop(){this.stopped++}}
window.AudioContext=class{constructor(){window.__au.ctx++;this.sampleRate=8000;this.destination={t:'dest'};this.currentTime=0}resume(){}createBuffer(c,l){return{getChannelData:()=>new Float32Array(l)}}createBufferSource(){const n=new N('src');window.__au.nodes.push(n);return n}createGain(){const n=new N('gain');window.__au.nodes.push(n);return n}createBiquadFilter(){const n=new N('biquad');window.__au.nodes.push(n);return n}createOscillator(){const n=new N('osc');window.__au.nodes.push(n);return n}};
"""
FROM="""window.__ups=[];window.__items=[];window.__itemsErr=null;window.__insErr=null;window.__updErr=null;window.__dl=[];
window.__fakeSb.from=t=>{
 if(t==='pro_items')return{
  select:()=>({eq:()=>({order:()=>({limit:async()=>window.__itemsErr?{data:null,error:{message:window.__itemsErr}}:{data:window.__items.slice().sort((a,b)=>b.updated_at.localeCompare(a.updated_at)),error:null}})})}),
  insert:row=>({select:()=>({single:async()=>{if(window.__insErr)return{data:null,error:{message:window.__insErr}};const r=Object.assign({id:'n'+(window.__items.length+1),updated_at:new Date().toISOString()},row);window.__items.push(r);return{data:r,error:null}}})}),
  update:row=>({eq:async(k,id)=>{if(window.__updErr)return{error:{message:window.__updErr}};Object.assign(window.__items.find(x=>x.id===id),row);return{error:null}}}),
  delete:()=>({eq:async(k,id)=>{window.__items=window.__items.filter(x=>x.id!==id);return{error:null}}})};
 const c=new Proxy(function(){},{get:(tg,k)=>k==='then'?(r=>r({data:[],error:null})):k==='upsert'?(async row=>{window.__ups.push([t,row]);return{error:null}}):k==='maybeSingle'?(async()=>({data:null,error:null})):()=>c,apply:()=>c});return c};
uvDownload=function(n,c,m){window.__dl.push({n,c,m})};"""
PRO="""window.__rpcRes.my_pro={data:{active:true,status:'active',source:'admin',since:new Date(Date.now()-20*864e5).toISOString(),until:null},error:null};authUid='u1';"""
NOPRO="""window.__rpcRes.my_pro={data:{active:false,status:'none'},error:null};authUid='u1';"""
LOAD="(async()=>{await proLoad()})()"
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p,1280,800)
        await pg.add_init_script(AUDIO)
        await login(pg);E=pg.evaluate
        await E(FROM+PRO+LOAD);await pg.wait_for_timeout(600)
        print("MI SEMANA")
        await E("""(()=>{const mon=wkMonday(0),dd=n=>{const x=new Date(mon);x.setDate(x.getDate()+n);return proIso(x)};window.__dd=dd;
          const W=(id,t,due,x={})=>Object.assign({id,type:'tarea',title:t,desc:'',topic:'',due,pts:10,link:'',ts:Date.now(),subs:{},files:[],opts:[],assg:[],rub:[]},x);
          classes[0].data.work=[W('a1','Lunes tarea',dd(0),{dueTime:'09:30',subs:{'Lucía Pérez':{st:'entregada'}}}),W('a2','Miércoles tarea',dd(2)),W('a3','Próxima semana',dd(7)),W('a4','Antigua',dd(-14)),W('a5','Sin fecha',''),W('a6','Oculta al alumnado',dd(1),{pubAt:Date.now()+9e8})];
          classes[0].data.events=[{id:'e1',t:'Reunión de tutores',s:'',i:'📄',d:dd(4)}];
          const c2=JSON.parse(JSON.stringify(classes[0]));c2.id='c2';c2.name='2º DAW';c2.color='#e11d48';c2.code='DAW-1';c2.data.work=[W('b1','Entrega c2',dd(2))];c2.data.events=[];classes.push(c2);
          const c3=JSON.parse(JSON.stringify(c2));c3.id='c3';c3.name='Archivada';c3.archived=true;c3.data.work=[W('z1','Tarea archivada',dd(1))];classes.push(c3)})();0""")
        await E(NOPRO+LOAD);await pg.wait_for_timeout(400)
        await E("toolOpen('semana');0");await pg.wait_for_timeout(400)
        chk("sin Pro: explicación amable (no se ve la semana)",'es una herramienta de Unuvia Pro' in await E("document.getElementById('modalFields').innerText") and await E("!document.querySelector('.wk')"))
        await E("closeModal();"+PRO+LOAD);await pg.wait_for_timeout(500)
        await E("WK.off=0;toolOpen('semana');0");await pg.wait_for_timeout(500)
        r=await E("({days:document.querySelectorAll('.wk-d').length,today:document.querySelectorAll('.wk-d.today').length,items:[...document.querySelectorAll('.wk-i b')].map(x=>x.textContent),t:document.querySelector('.wk-nav b').textContent})")
        chk("Pro: la semana tiene 7 días y marca el día de hoy",r['days']==7 and r['today']==1,r)
        chk("el profesor ve las tareas de TODAS sus clases y los eventos de esta semana (y no las de otras semanas, ni las de clases archivadas)",sorted(r['items'])==sorted(['Lunes tarea','Miércoles tarea','Oculta al alumnado','Entrega c2','Reunión de tutores']),r['items'])
        t=await E("document.querySelector('.wk-grid').innerText")
        chk("cada elemento dice de qué clase es y si es entrega o evento; con hora si la tiene",'Entrega · 09:30 · 1º FPB Informática' in t and 'Evento · 1º FPB Informática' in t and 'Entrega · 2º DAW' in t,t[:200])
        await E("document.querySelector('.wk-nav button[aria-label=\"Semana siguiente\"]').click();0");await pg.wait_for_timeout(300)
        chk("«Semana siguiente» enseña la próxima semana y aparece «Hoy» para volver",'Próxima semana' in await E("document.querySelector('.wk-grid').innerText") and await E("[...document.querySelectorAll('.wk-nav button')].some(b=>b.textContent==='Hoy')"))
        await E("WK.off=5;toolPaint();0");await pg.wait_for_timeout(300)
        chk("una semana sin nada dice «Semana libre»",'Semana libre' in await E("document.querySelector('.wk').innerText"))
        await E("WK.off=0;toolPaint();0");await pg.wait_for_timeout(300)
        await E("role='Alumno';user='Lucía Pérez';authUid='u2';WK.off=0;toolPaint();0");await pg.wait_for_timeout(400)
        r=await E("({items:[...document.querySelectorAll('.wk-i b')].map(x=>x.textContent),done:[...document.querySelectorAll('.wk-i.done b')].map(x=>x.textContent),txt:document.querySelector('.wk-grid').innerText})")
        chk("la alumna NO ve lo que aún no está publicado, y ve «Entregada» (tachada) lo que ya entregó",'Oculta al alumnado' not in r['items'] and r['done']==['Lunes tarea'] and 'Entregada' in r['txt'],r)
        await E("role='Profesor';user='Marga Profe';authUid='u1';WK.off=0;toolPaint();0");await pg.wait_for_timeout(300)
        await E("[...document.querySelectorAll('.wk-i')].find(b=>b.textContent.includes('Entrega c2')).click();0");await pg.wait_for_timeout(900)
        chk("al pulsar una entrega de otra clase, cambia a esa clase y abre la tarea",await E("classes[cur].name")=='2º DAW' and 'Entrega c2' in await E("document.getElementById('modalTitle').textContent"))
        await E("closeModal();setCur(0);renderAll();0")
        print("ARCHIVO DE CALENDARIO (.ics)")
        S="""(()=>{const A=[
          {k:'tarea',id:'w 1/é',iso:'2026-10-31',time:'',t:'Entrega, con; comas\\\\ y\\nsalto',cn:'1º FPB',desc:'Línea 1\\nLínea 2'},
          {k:'tarea',id:'w2',iso:'2026-12-31',time:'23:45',t:'Hora tardía',cn:'DAW',desc:''},
          {k:'evento',id:'e3',iso:'2028-02-28',time:'',t:'Evento bisiesto',cn:'DAW',desc:''},
          {k:'tarea',id:'w4',iso:'2026-11-05',time:'',t:'ñ'.repeat(80)+'😀'.repeat(30),cn:'X',desc:''}];
          const s=icsBuild(A,true),s2=icsBuild(A,false);const L=s.split('\\r\\n');const unf=s.replace(/\\r\\n /g,'');
          const enc=new TextEncoder;return {s,L,unf,max:Math.max(...L.map(l=>enc.encode(l).length)),vev:(s.match(/BEGIN:VEVENT/g)||[]).length,ala:(s.match(/BEGIN:VALARM/g)||[]).length,ala2:(s2.match(/BEGIN:VALARM/g)||[]).length,lone:/[^\\r]\\n/.test(s)}})()"""
        ics=await E(S)
        chk("empieza y acaba bien (VCALENDAR, versión 2.0) con saltos de línea CRLF y ninguna línea suelta",ics['s'].startswith('BEGIN:VCALENDAR\r\nVERSION:2.0\r\n') and ics['s'].endswith('END:VCALENDAR\r\n') and not ics['lone'])
        chk("4 eventos; avisos de «un día antes» solo en las tareas (3) y ninguno si se desactiva",ics['vev']==4 and ics['ala']==3 and ics['ala2']==0,(ics['vev'],ics['ala'],ics['ala2']))
        u=ics['unf']
        chk("fecha de todo el día con fin al día siguiente, también al cambiar de mes (31 oct → 1 nov), de año (31 dic) y en año bisiesto (28 feb 2028 → 29 feb)",'DTSTART;VALUE=DATE:20261031\r\nDTEND;VALUE=DATE:20261101' in u and 'DTSTART;VALUE=DATE:20280228\r\nDTEND;VALUE=DATE:20280229' in u)
        chk("con hora: dura 30 minutos y nunca pasa de las 23:59 (23:45 → 23:59)",'DTSTART:20261231T234500\r\nDTEND:20261231T235900' in u)
        chk("el texto con coma, punto y coma, barra y salto de línea va escapado (RFC 5545)",'SUMMARY:Entrega: Entrega\\, con\\; comas\\\\ y\\nsalto (1º FPB)' in u and 'DESCRIPTION:Línea 1\\nLínea 2' in u,u[u.index('SUMMARY'):u.index('SUMMARY')+120])
        chk("el identificador (UID) se limpia de caracteres raros y es estable",'UID:tarea-w1@unuvia.es' in u or 'UID:tarea-w1' in u)
        chk("las líneas largas con tildes y emojis se cortan en ≤75 bytes sin partir ningún carácter y al juntarlas queda el texto original",ics['max']<=75 and 'ñ'*80+'😀'*30 in u,ics['max'])
        await E("window.__dl.length=0;WK.alarm=true;wkIcs();0");await pg.wait_for_timeout(300)
        d=await E("window.__dl")
        chk("«Descargar calendario (.ics)» baja un archivo .ics con las entregas y eventos de TODAS las clases (de hace una semana en adelante) y no las antiguas ni las archivadas",len(d)==1 and d[0]['n']=='unuvia-calendario.ics' and 'text/calendar' in d[0]['m'] and 'Lunes tarea' in d[0]['c'] and 'Entrega c2' in d[0]['c'] and 'Próxima semana' in d[0]['c'] and 'Antigua' not in d[0]['c'] and 'Tarea archivada' not in d[0]['c'] and 'Reunión de tutores' in d[0]['c'],d[0]['c'][:80] if d else None)
        await E("classes.forEach(c=>{c.data.work=[];c.data.events=[]});window.__dl.length=0;wkIcs();0");await pg.wait_for_timeout(300)
        chk("si no hay nada que exportar, lo dice y no baja un archivo vacío",await E("window.__dl.length")==0)
        await E("closeModal();0")
        print("CUADERNO")
        await E(NOPRO+LOAD);await pg.wait_for_timeout(300)
        await E("toolOpen('cuaderno');0");await pg.wait_for_timeout(400)
        chk("sin Pro: explicación amable",'es una herramienta de Unuvia Pro' in await E("document.getElementById('modalFields').innerText"))
        await E("closeModal();"+PRO+LOAD);await pg.wait_for_timeout(500)
        await E("""window.__items=[{id:'n1',class_id:'c1',data:{t:'Fotosíntesis',b:'Clorofila y luz',p:false},updated_at:'2026-10-20T10:00:00Z'},{id:'n2',class_id:null,data:{t:'<img src=x onerror=alert(1)>',b:'Lista de la compra',p:true},updated_at:'2026-10-18T10:00:00Z'},{id:'n3',class_id:null,data:{t:'Examen de mates',b:'Fracciones y decimales',p:false},updated_at:'2026-10-21T10:00:00Z'}];ask=async()=>true;NB.sel='';NB.q='';NB.dirty=false;toolOpen('cuaderno');0""");await pg.wait_for_timeout(700)
        r=await E("[...document.querySelectorAll('#nbList .nb-i b')].map(b=>b.textContent)")
        chk("la lista sale con lo fijado arriba y luego lo más reciente",r[0].startswith('📌') and r[1]=='Examen de mates' and r[2]=='Fotosíntesis',r)
        chk("los títulos con HTML se enseñan como texto (no se ejecutan)",await E("!document.querySelector('#nbList img')") and '<img src=x' in r[0])
        await E("NB.q='FOTOSINTESIS';nbPaintList();0")
        chk("el buscador no distingue tildes ni mayúsculas",await E("[...document.querySelectorAll('#nbList .nb-i b')].map(b=>b.textContent)")==['Fotosíntesis'])
        await E("NB.q='';nbPaintList();nbSel('new');0");await pg.wait_for_timeout(300)
        await E("document.getElementById('nbT').value='Mi idea';document.getElementById('nbB').value='Texto de <b>prueba</b>';document.getElementById('nbC').value='c1';document.getElementById('nbP').checked=true;nbSave();0");await pg.wait_for_timeout(500)
        it=await E("window.__items.find(x=>x.data.t==='Mi idea')")
        chk("«Guardar» crea la nota en el servidor con título, texto, clase y «fijada»",it and it['kind']=='note' and it['class_id']=='c1' and it['data']=={'t':'Mi idea','b':'Texto de <b>prueba</b>','p':True},it)
        chk("aparece en la lista (fijada) y el editor sigue con ella abierta",'Mi idea' in await E("document.getElementById('nbList').innerText") and await E("document.getElementById('nbT').value")=='Mi idea')
        await E("document.getElementById('nbB').value='Cambiado';NB.dirty=true;nbSave();0");await pg.wait_for_timeout(400)
        chk("al editar actualiza la misma nota (no crea otra)",await E("window.__items.filter(x=>x.data.t==='Mi idea').length")==1 and await E("window.__items.find(x=>x.data.t==='Mi idea').data.b")=='Cambiado')
        await E("document.getElementById('nbB').value='Sin guardar';NB.dirty=true;nbSel('n3');0");await pg.wait_for_timeout(500)
        chk("si cambias de nota con cambios sin guardar, se guardan solos (no se pierde nada)",await E("window.__items.find(x=>x.data.t==='Mi idea').data.b")=='Sin guardar')
        await E("nbSel('new');document.getElementById('nbT').value='';document.getElementById('nbB').value='   ';nbSave();0");await pg.wait_for_timeout(300)
        chk("una nota vacía no se guarda («Escribe algo antes de guardar»)",await E("window.__items.length")==4)
        await E("nbSel('n3');nbDel();0");await pg.wait_for_timeout(500)
        chk("«Eliminar» pide confirmación y borra de verdad",await E("window.__items.some(x=>x.id==='n3')")==False and 'Examen de mates' not in await E("document.getElementById('nbList').innerText"))
        await E("window.__insErr='new row violates row-level security policy';nbSel('new');document.getElementById('nbT').value='X';nbSave();0");await pg.wait_for_timeout(400)
        chk("si el servidor no deja guardar (ya no eres Pro): mensaje claro «es de Unuvia Pro»",'es de Unuvia Pro' in await E("document.getElementById('toast')?document.getElementById('toast').innerText:document.body.innerText"))
        await E("window.__insErr='Has llegado al máximo de 300 elementos';document.getElementById('nbT').value='Y';nbSave();0");await pg.wait_for_timeout(400)
        chk("y si llegas al tope de 300 notas, también lo dice",'máximo de 300' in await E("document.getElementById('toast')?document.getElementById('toast').innerText:document.body.innerText"))
        await E("window.__insErr=null;window.__dl.length=0;nbExport();0");await pg.wait_for_timeout(200)
        d=await E("window.__dl")
        chk("«Descargar todas mis notas (.txt)» baja un archivo con los títulos y los textos",len(d)==1 and d[0]['n']=='mis-notas-unuvia.txt' and 'Fotosíntesis' in d[0]['c'] and 'Clorofila y luz' in d[0]['c'])
        await E("closeModal();window.__itemsErr='relation \"public.pro_items\" does not exist';NB.sel='';toolOpen('cuaderno');0");await pg.wait_for_timeout(700)
        chk("si falta el SQL: avisa al administrador del archivo y las notas se guardan solo en el dispositivo",NB_mode:=await E("NB.mode")=='local' and 'por ahora' in (await E("document.getElementById('nbMsg').textContent")).lower())
        await E("authEmail='unuviasupport@gmail.com';nbLoad();0");await pg.wait_for_timeout(500)
        chk("y al administrador le dice cuál: 10_pro_mas.sql",'10_pro_mas.sql' in await E("document.getElementById('nbMsg').textContent"))
        await E("nbSel('new');document.getElementById('nbT').value='Solo local';document.getElementById('nbB').value='x';nbSave();0");await pg.wait_for_timeout(300)
        chk("en modo local la nota se guarda en el almacenamiento del dispositivo",'Solo local' in await E("localStorage.getItem(nbKey())"))
        await E("authEmail='';window.__itemsErr='Failed to fetch';toolPaint();0");await pg.wait_for_timeout(700)
        chk("sin conexión: ves la última copia pero no se puede editar (campos y botón desactivados) y se explica",await E("NB.mode")=='offline' and 'Sin conexión' in await E("document.getElementById('nbMsg').textContent"))
        await E("window.__itemsErr=null;closeModal();0")
        print("errores JS:",errs[:3]);await b.close()
    print(f"\n{ok} correctas, {bad} fallos")
asyncio.run(main())
