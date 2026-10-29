import json,math
import numpy as np
from shapely.geometry import Polygon,Point,MultiPolygon
from shapely.ops import unary_union
D=json.load(open('/home/claude/farnesio/data.json'))
def P(f):return Polygon(list(zip(f[0::2],f[1::2]))).buffer(0)
def flat(p):return [round(c,3) for x,y in list(p.exterior.coords)[:-1] for c in (x,y)]
def ringflat(r):return [round(c,3) for x,y in list(r.coords)[:-1] for c in (x,y)]
def geoms(g):return [g] if g.geom_type=='Polygon' else [x for x in g.geoms if x.geom_type=='Polygon']
for f in ('T','AT'):
  F=D['floors'][f]
  envAll=unary_union([P(p) for p in F['envAll']])
  env=unary_union([P(p) for p in F['env']])
  ters=[(n,P(t)) for n,U in F['units'].items() for t in U['ter']]
  # band ring
  outer=envAll.buffer(.08,join_style=2,mitre_limit=3); inner=envAll.buffer(-.16,join_style=2,mitre_limit=3)
  ring=outer.difference(inner)
  F['band']=[[ringflat(g.exterior)]+[ringflat(i) for i in g.interiors] for g in geoms(ring) if g.area>.5]
  # facade flags: terrace in front, exterior (street) side
  for n,U in F['units'].items():
    nf=[]
    for a in U['fac']:
      x1,y1,x2,y2,nx,ny=a[:6]; mx,my=(x1+x2)/2+nx*.6,(y1+y2)/2+ny*.6
      ter=1 if any(t.contains(Point(mx,my)) for _,t in ters) else 0
      ext=1 if (ny<-.7 or nx>.7) else 0
      nf.append([x1,y1,x2,y2,nx,ny,ter,ext])
    U['fac']=nf
  # corner terraces -> round columns at the outermost corner
  cols=[]
  for n,t in ters:
    ti=t.buffer(-.25,join_style=2)
    if ti.is_empty:continue
    best=max(ti.exterior.coords,key=lambda c:env.distance(Point(c)))
    d=env.distance(Point(best))
    # spans two facade directions?
    near=[e for e in [env.exterior]+list(getattr(env,'interiors',[]))]
    sides=set()
    cs=list(env.exterior.coords)
    for (a,b),(c,d2) in zip(cs,cs[1:]):
      seg_mid=Point((a+c)/2,(b+d2)/2)
      from shapely.geometry import LineString
      L=LineString([(a,b),(c,d2)])
      if L.length>.4 and L.intersection(t.buffer(.05)).length>.4:
        sides.add((round((d2-b)/L.length),round((c-a)/L.length)))
    if len(sides)>=2: cols.append([round(best[0],2),round(best[1],2),n])
  F['cols']=cols
  print(f,'band',len(F['band']),'cols',cols)
# ----- hip roof over the attic -----
F=D['floors']['AT']
roofP=unary_union([P(p) for p in F['env']]).buffer(.35,join_style=2)
if roofP.geom_type!='Polygon':roofP=max(roofP.geoms,key=lambda g:g.area)
roofP=roofP.simplify(.05)
pts=[]
def dens(r,step=.7):
  cs=list(r.coords);out=[]
  for (a,b),(c,d) in zip(cs,cs[1:]):
    L=math.hypot(c-a,d-b);k=max(1,int(L/step))
    out+=[(a+(c-a)*i/k,b+(d-b)*i/k) for i in range(k)]
  return out
pts+=dens(roofP.exterior)
d=.45
while True:
  o=roofP.buffer(-d,join_style=2,mitre_limit=10)
  if o.is_empty:break
  for g in geoms(o): pts+=dens(g.exterior,1.0)
  d+=.45
maxd=d
from scipy.spatial import Delaunay
A=np.array(pts);tri=Delaunay(A)
slope=math.tan(math.radians(27))
dist=np.array([roofP.exterior.distance(Point(p)) for p in A])
faces=[]
for s in tri.simplices:
  c=A[s].mean(0)
  if roofP.contains(Point(c)):faces.append(s.tolist())
D['roof']={'v':[round(v,3) for p,dd in zip(A,dist) for v in (p[0],p[1],dd*slope)],'f':[i for t in faces for i in t],'h':round(maxd*slope,2)}
# chimneys: along the ridge zone, spaced
ridge=roofP.buffer(-(maxd-.9),join_style=2)
cand=[]
for g in geoms(ridge): cand+=dens(g.exterior,1.0)
cores=[P(U['viv'][0]) for n,U in F['units'].items() if 'COMUN' in n]
chim=[]
for p in cand:
  if any(c.buffer(1.5).contains(Point(p)) for c in cores):continue
  if all(math.hypot(p[0]-q[0],p[1]-q[1])>5.5 for q in chim):chim.append(p)
D['roof']['chim']=[[round(x,2),round(y,2),round(roofP.exterior.distance(Point(x,y))*slope,2)] for x,y in chim][:16]
print('roof faces',len(faces),'h',D['roof']['h'],'chim',len(D['roof']['chim']))
# ----- ground floor: portal canopies -----
x0,y0,x1,y1=D['pb']['plot']
can=[]
for r in D['pb']['rooms']:
  if 'Portal' not in r['n']:continue
  p=P(r['pts']);bx=p.bounds
  if abs(bx[1]-y0)<3: can.append([round(bx[0]-.6,2),round(y0-1.6,2),round(bx[2]+.6,2),round(y0+.4,2)])
  else: can.append([round(x1-.4,2),round(bx[1]-.6,2),round(x1+1.6,2),round(bx[3]+.6,2)])
D['pb']['canopy']=can;print('canopies',can,[ (r['n'],[round(v,1) for v in P(r['pts']).bounds]) for r in D['pb']['rooms']])
json.dump(D,open('/home/claude/farnesio/data.json','w'),separators=(',',':'),ensure_ascii=False)
