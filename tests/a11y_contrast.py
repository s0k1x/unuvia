import asyncio,sys,collections
sys.argv=[sys.argv[0]]
src=open("/home/claude/a11y_scan.py").read().rsplit("async def main():",1)[0]
exec(src)
CON="""()=>{const out=[];
 const parse=s=>{const m=s.match(/rgba?\\(([^)]+)\\)/);if(!m)return null;const p=m[1].split(',').map(x=>parseFloat(x));return{r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}};
 const lum=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)};
 const over=(f,b)=>({r:f.r*f.a+b.r*(1-f.a),g:f.g*f.a+b.g*(1-f.a),b:f.b*f.a+b.b*(1-f.a),a:1});
 const bgOf=e=>{let layers=[];for(let n=e;n&&n.nodeType===1;n=n.parentElement){const cs=getComputedStyle(n);if(cs.backgroundImage&&cs.backgroundImage!=='none')return null;const c=parse(cs.backgroundColor);if(c&&c.a>0){layers.push(c);if(c.a>=.98)break}}
  let base={r:getComputedStyle(document.documentElement).colorScheme==='dark'||document.documentElement.classList.contains('dark')?10:255,g:0,b:0,a:1};base=layers.length&&layers[layers.length-1].a>=.98?layers.pop():{r:12,g:16,b:28,a:1};
  let c=base;while(layers.length)c=over(layers.pop(),c);return c};
 const vis=e=>{const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&+cs.opacity>.3};
 const seen=new Set;
 document.querySelectorAll('#classView *,#modal *,header *,nav *').forEach(e=>{
  if(!vis(e))return;if(![...e.childNodes].some(n=>n.nodeType===3&&n.nodeValue.trim().length>1))return;
  const cs=getComputedStyle(e),fg=parse(cs.color);if(!fg)return;const bg=bgOf(e);if(!bg)return;
  const f=over(fg,bg),L1=lum(f),L2=lum(bg),ratio=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
  const size=parseFloat(cs.fontSize),bold=+cs.fontWeight>=700,large=size>=24||(size>=18.66&&bold),need=large?3:4.5;
  if(ratio<need){const key=(e.className.toString().split(' ')[0]||e.tagName)+'|'+cs.color+'|'+Math.round(ratio*10);if(seen.has(key))return;seen.add(key);out.push({c:e.className.toString().slice(0,40)||e.tagName,t:e.textContent.trim().slice(0,26),ratio:Math.round(ratio*100)/100,need,size:Math.round(size)})}});
 return out}"""
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p,1280,800);E=pg.evaluate;await login(pg)
        await E("document.body.insertAdjacentHTML('beforeend','<button id=testbad style=\"position:fixed;top:0;left:0\"></button><input id=testbad2 style=\"position:fixed;top:30px\">');0")
        r=await E(SCAN)
        print("AUTOPRUEBA del detector (debe encontrar 2):",[x for x in r if 'testbad' in x])
        await E("document.getElementById('testbad').remove();document.getElementById('testbad2').remove();0")
        res=collections.defaultdict(list)
        for theme in ['dark','light']:
            await E(f"setPref('{theme}');applyPref();0");await pg.wait_for_timeout(500)
            for v in ['Inicio','Herramientas','Trabajo','Notas','Chat','Personas']:
                await E(f"goTab('{v}');0");await pg.wait_for_timeout(450)
                for x in await E(CON): res[theme].append((v,x))
        for th in res:
            print(f"\n== tema {th}: {len(res[th])} combinaciones con poco contraste")
            seen=set()
            for v,x in sorted(res[th],key=lambda t:t[1]['ratio'])[:14]:
                k=(x['c'],x['ratio'])
                if k in seen: continue
                seen.add(k); print(f"  {x['ratio']:>5} (necesita {x['need']}) · {v:12} · .{x['c']} · «{x['t']}» · {x['size']}px")
        await b.close()
asyncio.run(main())
