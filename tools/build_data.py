import json,re
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
g=json.load(open('geo.json'));pb=json.load(open('pb.json'));units=json.load(open('units.json'))
def P(flat):return Polygon(list(zip(flat[0::2],flat[1::2]))).buffer(0)
def flat(poly):
  if poly.geom_type!='Polygon':poly=max(poly.geoms,key=lambda g:g.area)
  return [round(c,2) for x,y in list(poly.exterior.coords)[:-1] for c in (x,y)]
def nice(n):
  n=re.sub(r'^\d+-','',n)
  M={'Salón Cocina':'Salón-cocina','Arm Vest':'Armario','Baño D1':'Baño en suite','Dormitorio 01':'Dormitorio 1','Dormitorio 02':'Dormitorio 2','Dormitorio 03':'Dormitorio 3','Arm D1':'Armario','Arm':'Armario','Aseo 02':'Aseo','Escalera común':'Escalera','Distribuidor común':'Rellano'}
  return M.get(n,n)
out={'floors':{},'pb':{},'units':units}
for f in ('T','AT'):
  F=g[f];U={}
  vivpolys=[];allpolys=[]
  for name,ps in F['units'].items():
    for p in ps:
      pp=P(p['pts']);allpolys.append(pp)
      if not p['t']:vivpolys.append(pp)
  env=unary_union([p.buffer(.06,join_style=2) for p in vivpolys]).buffer(-.06,join_style=2)
  envAll=unary_union([p.buffer(.08,join_style=2) for p in allpolys]).buffer(-.08,join_style=2)
  bnd=env.boundary
  for name,ps in F['units'].items():
    viv=[P(p['pts']) for p in ps if not p['t']];ter=[P(p['pts']) for p in ps if p['t']]
    fac=[]
    for v in viv:
      cs=list(v.exterior.coords)
      for (x1,y1),(x2,y2) in zip(cs,cs[1:]):
        L=((x2-x1)**2+(y2-y1)**2)**.5
        if L<.8:continue
        mx,my=(x1+x2)/2,(y1+y2)/2
        if bnd.distance(Point(mx,my))>.2:continue
        nx,ny=(y2-y1)/L,-(x2-x1)/L
        if env.buffer(.01).contains(Point(mx+nx*.4,my+ny*.4)):nx,ny=-nx,-ny
        if env.buffer(.01).contains(Point(mx+nx*.4,my+ny*.4)):continue
        if f=='T' and ((nx<-.9 and mx<55.2) or (ny>.9 and my>34.5)):continue
        fac.append([round(x1,2),round(y1,2),round(x2,2),round(y2,2),round(nx,3),round(ny,3)])
    terIn=[]
    for t in ter:
      ti=t.buffer(-.12,join_style=2)
      terIn.append(flat(ti) if not ti.is_empty else [])
    U[name]=dict(viv=[flat(v) for v in viv],ter=[flat(t) for t in ter],terIn=terIn,fac=fac)
  roomU=unary_union([P(r['pts']).buffer(0) for r in F['rooms'] if not r['n'].startswith('12-')])
  walls=env.difference(roomU.buffer(.005,join_style=2)).buffer(-.004,join_style=2).buffer(.004,join_style=2)
  W=[]
  for w in ([walls] if walls.geom_type=='Polygon' else list(walls.geoms)):
    if w.area<.05:continue
    w=w.simplify(.01)
    W.append([[round(c,2) for x,y in list(w.exterior.coords)[:-1] for c in (x,y)]]+[[round(c,2) for x,y in list(i.coords)[:-1] for c in (x,y)] for i in w.interiors])
  print(f,'walls',len(W),round(walls.area,1))
  rooms=[dict(u=r['u'],n=nice(r['n']),a=float(re.sub('[^0-9.]','',r['a'])),lx=r['lx'],ly=r['ly'],pts=r['pts'][:-2]) for r in F['rooms']]
  def geoms(e):return [e] if e.geom_type=='Polygon' else list(e.geoms)
  out['floors'][f]=dict(units=U,rooms=rooms,walls=W,lines={k:F['lines'].get(k,[]) for k in ('w','c','f')},
    env=[flat(p) for p in geoms(env) if p.area>5],envAll=[flat(p) for p in geoms(envAll) if p.area>5])
  print(f,{k:len(v['fac']) for k,v in U.items()})
# pilotis under footprint
foot=unary_union([P(x) for x in out['floors']['T']['env']])
pil=[p for p in pb['pil'] if foot.buffer(.3).contains(Point(p))]
out['pb']=dict(rooms=[dict(n=r['n'].strip('. '),a=r['a'],pts=r['pts'][:-2]) for r in g['PB']['rooms']],pil=pil,pool=[78.05,20.3,86.15,25.55],plot=[54.4,-0.4,112.8,35.0])
print('pil',len(pil))
s=json.dumps(out,separators=(',',':'),ensure_ascii=False)
open('/home/claude/farnesio/data.json','w').write(s);print(len(s))
