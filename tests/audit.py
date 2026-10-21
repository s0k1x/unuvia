import asyncio,sys,json
from playwright.async_api import async_playwright
PORT=sys.argv[1]; THEMES=sys.argv[2].split(','); VPS=[tuple(map(int,v.split('x'))) for v in sys.argv[3].split(',')]
VIEWS=['Inicio','Herramientas','Calendario','Trabajo','Horario','Ahora','Notas','Personas','Chat']
SEED="""()=>{settings.toured=true;
 addClass({id:'c1',name:'2º FPB — Comunicación y representación de la información',code:'MT-4827',role:'Administrador',emoji:'📚',color:'#008cff'});
 const d=n=>new Date(Date.now()+n*864e5).toISOString().slice(0,10);
 data.events.push({id:'e1',i:'📝',t:'Examen del tema 2: Comunicación y representación de la información',s:'Aula 3, primera hora',d:d(2)},{id:'e2',i:'📅',t:'Entrega',s:'',d:d(0)});
 data.tasks.push({id:'t1',t:'Repasar apuntes de matemáticas y lengua',d:d(1),done:false});
 [['Matemáticas','08:15','3'],['Lengua castellana y literatura','09:15','12'],['Inglés','10:15','7']].forEach((x,i)=>data.sched.push({id:'s'+i,t:x[0],day:(new Date().getDay()+6)%7,h:x[1],r:x[2]}));
 data.work.push({id:'w1',type:'tarea',title:'Trabajo sobre la comunicación visual',desc:'',topic:'',due:d(3),pts:10,link:'',ts:Date.now()-864e5,subs:{},files:[],opts:[],assg:[],rub:[]});
 renderAll();}"""
async def main():
    res=[]
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--no-sandbox"])
        for (w,h) in VPS:
            for th in THEMES:
                ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=1,is_mobile=w<700,has_touch=w<700)
                pg=await ctx.new_page(); errs=[]
                pg.on("pageerror",lambda e:errs.append(str(e)[:160]))
                await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
                await pg.add_init_script("try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','dark')}catch(e){}")
                await pg.goto(f"http://localhost:{PORT}/");await pg.wait_for_timeout(900)
                await pg.evaluate("acceptCookies();launchApp(document.getElementById('startLogin'))");await pg.wait_for_timeout(1100)
                await pg.evaluate("document.querySelector('input[value=local]').click();document.getElementById('localName').value='Lucía';document.getElementById('localLoginButton').click()");await pg.wait_for_timeout(1200)
                await pg.evaluate(SEED)
                if th!='normal': await pg.evaluate(f"applySeason('{th}')")
                await pg.wait_for_timeout(1500)
                await pg.evaluate("acceptCookies();document.querySelectorAll('#tour,.tour').forEach(t=>t.classList.add('hidden'))")
                for v in VIEWS:
                    await pg.evaluate(f"goTab('{v}')");await pg.wait_for_timeout(450)
                    r=await pg.evaluate("""()=>{const W=innerWidth,out=[];
                      const scrollable=e=>{for(let p=e.parentElement;p&&p!==document.body;p=p.parentElement){const o=getComputedStyle(p).overflowX;if((o==='auto'||o==='scroll'||o==='hidden')&&p.scrollWidth>=p.clientWidth)return true}return false};
                      document.querySelectorAll('.view.active *, #classView .hero *, #classView .ib-tabs *').forEach(e=>{const r=e.getBoundingClientRect();if(r.width>0&&r.height>0&&(r.right>W+3||r.left<-3)){const cs=getComputedStyle(e);if(cs.position==='fixed'||cs.visibility==='hidden'||+cs.opacity<0.05||e.closest('.cp-btn,.chat,.wa-top')||scrollable(e))return;out.push((e.tagName+'.'+String(e.className).split(' ')[0]).slice(0,40)+' x='+Math.round(r.left)+'..'+Math.round(r.right))}});
                      return {doc:document.documentElement.scrollWidth>W+1?document.documentElement.scrollWidth:0,over:[...new Set(out)].slice(0,4)}}""")
                    if r['doc'] or r['over']: res.append((w,th,v,r))
                if errs: res.append((w,th,'ERRORES JS',errs[:2]))
                await ctx.close()
        await b.close()
    print(f"problemas encontrados: {len(res)}")
    for x in res: print(' ',x)
asyncio.run(main())
