import json,math
from shapely.geometry import Polygon,Point,LineString
D=json.load(open('/home/claude/farnesio/data.json'));G=json.load(open('geo.json'))
out={}
for f in ('T','AT'):
  F=D['floors'][f]; car=G[f]['lines'].get('c',[])
  segs=[]
  for l in car:
    for i in range(0,len(l)-2,2): segs.append((l[i],l[i+1],l[i+2],l[i+3]))
  ters=[Polygon(list(zip(t[0::2],t[1::2]))) for U in F['units'].values() for t in U['ter']]
  res={}
  for name,U in F['units'].items():
    ops=[]
    for (x1,y1,x2,y2,nx,ny) in U['fac']:
      L=math.hypot(x2-x1,y2-y1); dx,dy=(x2-x1)/L,(y2-y1)/L
      iv=[]
      for (a,b,c,d) in segs:
        # parallel and close to facade line
        sl=math.hypot(c-a,d-b)
        if sl<.05:continue
        if abs((c-a)/sl*dx+(d-b)/sl*dy)<.97:continue
        def proj(px,py):return ((px-x1)*dx+(py-y1)*dy, (px-x1)*nx+(py-y1)*ny)
        t1,o1=proj(a,b);t2,o2=proj(c,d)
        if not(-.45<o1<.25 and -.45<o2<.25):continue
        lo,hi=sorted((t1,t2)); lo=max(lo,0);hi=min(hi,L)
        if hi-lo<.05:continue
        iv.append([lo,hi])
      iv.sort();mer=[]
      for a,b in iv:
        if mer and a<=mer[-1][1]+.12: mer[-1][1]=max(mer[-1][1],b)
        else: mer.append([a,b])
      for a,b in mer:
        w=b-a
        if w<.45 or w>4.5:continue
        m=(a+b)/2; px,py=x1+dx*m+nx*.8,y1+dy*m+ny*.8
        door=any(t.contains(Point(px,py)) for t in ters)
        ops.append([round(x1+dx*a,2),round(y1+dy*a,2),round(x1+dx*b,2),round(y1+dy*b,2),nx,ny,1 if door else 0])
    res[name]=ops
  out[f]=res
  print(f,sum(len(v) for v in out[f].values()),{k:len(v) for k,v in res.items()})
for f in out:
  for n,v in out[f].items(): D['floors'][f]['units'][n]['ops']=v
json.dump(D,open('/home/claude/farnesio/data.json','w'),separators=(',',':'),ensure_ascii=False)
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(18,10),dpi=60)
for e in D['floors']['T']['env']:ax.fill(e[0::2],e[1::2],color='#eee')
for l in G['T']['lines']['c']:ax.plot(l[0::2],l[1::2],'c',lw=.3)
for n,v in out['T'].items():
  for o in v: ax.plot([o[0],o[2]],[o[1],o[3]],'r' if o[6] else 'b',lw=3)
ax.set_aspect('equal');plt.savefig('ops.png',bbox_inches='tight')
