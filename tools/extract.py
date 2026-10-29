import ezdxf,sys,collections,json,math
from ezdxf import disassemble
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
d=ezdxf.readfile(sys.argv[1]);m=d.modelspace()
OFF={'PB':400,'T':600,'AT':800,'S1':200}
RANGE={'PB':(440,530),'T':(640,730),'AT':(840,930),'S1':(240,320)}
Y0=72.0
CAT={'1-01-MUROS':'w','1-02-CARPINTERIA':'c','1-11-MOBILIARIO':'f','1-14-COCINA':'f','1-13-SANITARIOS':'f',
     '3-03-PILARES':'w','1-09-PATINILLO':'w','1-03-PROYECCION_01':'p','1-10-VEGETACIÓN':None,'8-01-MINUSVALIDOS':None,'0-SUPERFICIES':None}
def which(x):
  for k,(a,b) in RANGE.items():
    if a<x<b:return k
def anchor(e):
  t=e.dxftype()
  try:
    if t=='LINE':return e.dxf.start.x
    if t=='LWPOLYLINE':return e.get_points()[0][0]
    if t in('INSERT','CIRCLE','ARC','TEXT','MTEXT'):return (e.dxf.insert if t in('INSERT','TEXT','MTEXT') else e.dxf.center).x
    if t=='HATCH':
      for p in e.paths:
        v=getattr(p,'vertices',None)
        if v: return v[0][0]
        for ed in getattr(p,'edges',[]):
          s=getattr(ed,'start',None) or getattr(ed,'center',None)
          if s is not None: return s[0]
    if t=='MLINE':return e.start_location().x
  except Exception: return None
def R(v):return round(v,2)
out={f:{'lines':collections.defaultdict(list),'poche':[],'rooms':[],'units':{}} for f in OFF}
def addpath(f,cat,pts):
  o=OFF[f];pts=[(R(x-o),R(y-Y0)) for x,y in pts]
  if any(not(45<x<122 and -6<y<42) for x,y in pts): return
  if len(pts)>1: out[f]['lines'][cat].append([c for p in pts for c in p])
def handle(f,cat,e,depth=0):
  t=e.dxftype()
  if t=='INSERT':
    if depth>4:return
    try:
      for v in e.virtual_entities(): handle(f,cat,v,depth+1)
    except Exception:pass
    return
  if t=='LINE':addpath(f,cat,[(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)])
  elif t in('LWPOLYLINE','POLYLINE'):
    try:
      pts=[(p.x,p.y) for p in e.flattening(0.05)] if hasattr(e,'flattening') else []
    except Exception: pts=[]
    if not pts:
      pts=[(p[0],p[1]) for p in (e.get_points() if t=='LWPOLYLINE' else e.points())]
    if e.closed if t=='LWPOLYLINE' else e.is_closed: pts.append(pts[0])
    addpath(f,cat,pts)
  elif t in('ARC','CIRCLE','ELLIPSE','SPLINE'):
    try:addpath(f,cat,[(p.x,p.y) for p in e.flattening(0.05)])
    except Exception:pass
  elif t=='MLINE':
    try:
      for v in e.virtual_entities(): handle(f,cat,v,depth+1)
    except Exception:pass
for e in m:
  lay=e.dxf.layer
  if lay not in CAT and lay!='2-01-RAYADO_PLANTA':continue
  x=anchor(e)
  if x is None:continue
  f=which(x)
  if not f:continue
  if lay=='2-01-RAYADO_PLANTA':
    if e.dxftype()=='HATCH':
      for p in e.paths:
        try:
          from ezdxf.render.hatching import hatch_paths
        except Exception:pass
      try:
        for path in ezdxf.path.from_hatch(e):
          pts=[(p.x-OFF[f],p.y-Y0) for p in path.flattening(0.05)]
          if len(pts)>2: out[f]['poche'].append([R(c) for p in pts for c in p])
      except Exception as ex: pass
    continue
  cat=CAT[lay]
  if cat:handle(f,cat,e)
labels=json.load(open('labels.json'))
for e in m.query('LWPOLYLINE[layer=="A-04-SUP_UTILES"]'):
  pts=[(x,y) for x,y,*_ in e.get_points()];f=which(pts[0][0])
  if f not in out:continue
  P=Polygon(pts).buffer(0)
  if P.is_empty:continue
  if P.geom_type!='Polygon':P=max(P.geoms,key=lambda g:g.area)
  ls=[l for l in labels if l['plan']==f and P.contains(Point(l['x'],l['y']))]
  if not ls:continue
  l=ls[0];o=OFF[f]
  out[f]['rooms'].append(dict(u=l['VIVIENDA'],n=l['ESTANCIA'],a=l['SUPERFICIE'],lx=R(l['x']-o),ly=R(l['y']-Y0),
     pts=[R(c) for x,y in P.exterior.coords for c in (x-o,y-Y0)]))
U=collections.defaultdict(list)
for e in m.query('LWPOLYLINE[layer=="A-05-SUP_CONSTRUIDA"]'):
  pts=[(x,y) for x,y,*_ in e.get_points()];f=which(pts[0][0])
  if f not in('T','AT'):continue
  P=Polygon(pts).buffer(0)
  inside=collections.Counter(l['VIVIENDA'] for l in labels if l['plan']==f and P.contains(Point(l['x'],l['y'])))
  if not inside:continue
  v=inside.most_common(1)[0][0]
  ister=any(l['ESTANCIA'].startswith('12-Terraza') for l in labels if l['plan']==f and P.contains(Point(l['x'],l['y']))) and len(inside)==1 and sum(inside.values())==1
  o=OFF[f]
  U[(f,v)].append(dict(t=ister,pts=[R(c) for x,y in P.exterior.coords for c in (x-o,y-Y0)]))
for (f,v),ps in U.items(): out[f]['units'][v]=ps
for f in out: out[f]['lines']=dict(out[f]['lines'])
json.dump(out,open('geo.json','w'),separators=(',',':'))
for f in out: print(f,{k:len(v) for k,v in out[f]['lines'].items()},len(out[f]['poche']),len(out[f]['rooms']),len(out[f]['units']))
