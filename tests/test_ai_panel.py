import asyncio,json
from playwright.async_api import async_playwright
FAKE=r"""
(()=>{const chain=()=>new Proxy(function(){},{get:(t,p)=>p==='then'?(r=>r({data:[],error:null})):chain(),apply:()=>chain()});
window.__rpc=[];window.__listErr=false;
const U=[{id:'t1',name:'Marga Profe',email:'marga@centro.es',account_type:'teacher',teacher_verified:true,created_at:'2026-09-01'},
 {id:'t2',name:'Pablo Docente',email:'pablo@centro.es',account_type:'teacher',teacher_verified:true,created_at:'2026-09-02'},
 {id:'s1',name:'Lucía Alumna',email:'lucia@centro.es',account_type:'student',teacher_verified:false,created_at:'2026-09-03'},
 {id:'a1',name:'Unuvia Support',email:'unuviasupport@gmail.com',account_type:'teacher',teacher_verified:false,created_at:'2026-08-01'}];
window.__ai=new Set(['t2']);
window.__fakeSb={auth:{getSession:async()=>({data:{session:null}}),onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),signOut:async()=>{},getUser:async()=>({data:{user:null}})},
 from:()=>chain(),channel:()=>{const c={on:()=>c,subscribe:()=>c};return c},removeChannel(){},storage:{from:()=>chain()},functions:{invoke:async()=>({data:null,error:null})},
 rpc:(n,a)=>{window.__rpc.push([n,a||null]);
  if(n==='admin_users')return Promise.resolve({data:U,error:null});
  if(n==='admin_ai_list')return Promise.resolve(window.__listErr?{data:null,error:{message:'function admin_ai_list does not exist'}}:{data:[...window.__ai].map(x=>({uid:x})),error:null});
  if(n==='admin_ai_set'){if(window.__setErr)return Promise.resolve({error:{message:'x'}});a.p_on?window.__ai.add(a.p_user):window.__ai.delete(a.p_user);return Promise.resolve({error:null})}
  return chain()}};})();
"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":1300,"height":900})
        pg=await ctx.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)[:200]))
        async def patch(route):
            r=await route.fetch(); t=await r.text()
            await route.fulfill(response=r,body=t.replace('sb=window.supabase?','sb=window.__fakeSb?window.__fakeSb:window.supabase?',1))
        await pg.route("**/app.js*",patch);await pg.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
        await pg.add_init_script(FAKE+"try{localStorage.setItem('unuvia_perf','full');localStorage.setItem('unuvia_perf_v','3');localStorage.setItem('unuvia_theme','dark')}catch(e){}")
        await pg.goto("http://localhost:8766/");await pg.wait_for_timeout(1500)
        await pg.evaluate("acceptCookies();launchApp(document.getElementById('startLogin'))");await pg.wait_for_timeout(1300)
        await pg.evaluate("document.querySelector('input[value=local]').click();document.getElementById('localName').value='Admin';document.getElementById('localLoginButton').click()");await pg.wait_for_timeout(1500)
        ok=0;bad=0
        def chk(n,c,x=''):
            nonlocal ok,bad
            if c: ok+=1;print('  ✓',n)
            else: bad+=1;print('  ✗',n,x)
        E=lambda s: pg.evaluate(s)
        await E("window.confirm=()=>true;authEmail='unuviasupport@gmail.com';admOpen();0");await pg.wait_for_timeout(800)
        await E("admpGo('usuarios');0");await pg.wait_for_timeout(1200)
        txt=await E("document.getElementById('admpBody').textContent")
        chk("la lista de usuarios carga y se pide también quién tiene la IA",'Marga Profe' in txt and any(r[0]=='admin_ai_list' for r in await E("window.__rpc")))
        chk("Pablo ya tiene la IA: sale la etiqueta «✨ IA» en su fila",'✨ IA' in await E("[...document.querySelectorAll('.admp-u')].find(e=>e.textContent.includes('Pablo')).textContent"))
        chk("Marga (verificada, sin IA) no tiene la etiqueta",'✨ IA' not in await E("[...document.querySelectorAll('.admp-u')].find(e=>e.textContent.includes('Marga')).textContent"))
        # abrir a Marga
        await E("admpOpen('t1');0");await pg.wait_for_timeout(300)
        acts=await E("document.querySelector('.admp-u.on .admp-acts').textContent")
        chk("Marga: aparece «✨ Activar IA»",'Activar IA' in acts,acts[:120])
        await pg.screenshot(path='/home/claude/panel_ia.png')
        await E("admpAi('t1',true);0");await pg.wait_for_timeout(500)
        last=[r for r in await E("window.__rpc") if r[0]=='admin_ai_set'][-1]
        chk("al activar llama a admin_ai_set con el usuario y true",last[1]=={'p_user':'t1','p_on':True},json.dumps(last))
        chk("tras activar sale «✨ IA» en la fila y el botón pasa a «Quitar IA»",await E("(()=>{const r=[...document.querySelectorAll('.admp-u')].find(e=>e.textContent.includes('Marga'));return r.textContent.includes('✨ IA')&&r.textContent.includes('Quitar IA')})()"))
        await E("admpAi('t1',false);0");await pg.wait_for_timeout(500)
        chk("quitar la IA funciona y vuelve el botón «Activar IA»",await E("(()=>{const r=[...document.querySelectorAll('.admp-u')].find(e=>e.textContent.includes('Marga'));return !r.textContent.includes('✨ IA')&&r.textContent.includes('Activar IA')})()"))
        await E("admpOpen('t1');admpOpen('s1');0");await pg.wait_for_timeout(300)
        chk("una alumna (no verificada) NO tiene botón de IA",'Activar IA' not in await E("document.querySelector('.admp-u.on .admp-acts').textContent"))
        await E("admpOpen('a1');0");await pg.wait_for_timeout(300)
        chk("el administrador (unuviasupport) tiene la IA siempre activada: sin botón y con la etiqueta «✨ IA»",('siempre activada' in await E("document.querySelector('.admp-u.on .admp-acts').textContent")) and ('Activar IA' not in await E("document.querySelector('.admp-u.on .admp-acts').textContent")) and ('✨ IA' in await E("document.querySelector('.admp-u.on').textContent")))
        await E("window.__setErr=true;admpAi('t1',true);0");await pg.wait_for_timeout(500)
        chk("si el servidor falla: mensaje claro y NO cambia nada",'ai_panel.sql' in await E("document.getElementById('toast').textContent") and not await E("ADMP.ai.has('t1')"))
        # sin el SQL instalado
        await E("window.__setErr=false;window.__listErr=true;ADMP.ai=null;ADMP.aiErr='';ADMP.users=null;admpLoadUsers();0");await pg.wait_for_timeout(900)
        await E("admpOpen('t1');0");await pg.wait_for_timeout(300)
        chk("sin el SQL: el panel avisa de ejecutar «ai_panel.sql» (sin romperse)",'ai_panel.sql' in await E("document.querySelector('.admp-u.on .admp-acts').textContent"))
        print("errores JS:",errs[:3]);print(f"\n{ok} correctas, {bad} fallos")
        await b.close()
asyncio.run(main())
