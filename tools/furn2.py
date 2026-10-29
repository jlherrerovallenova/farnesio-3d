import json,math,collections
from shapely.geometry import LineString,Polygon,Point,MultiPoint,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import affinity
G=json.load(open('geo.json'));D=json.load(open('/home/claude/farnesio/data.json'))
R2=lambda v:round(v,3)
def obb(geom_pts):
  mr=MultiPoint(geom_pts).minimum_rotated_rectangle
  if mr.geom_type!='Polygon': mr=mr.buffer(.02,cap_style=2)
  cs=list(mr.exterior.coords)[:4]
  e1=math.dist(cs[0],cs[1]);e2=math.dist(cs[1],cs[2])
  if e1>=e2:L,W,a=e1,e2,math.atan2(cs[1][1]-cs[0][1],cs[1][0]-cs[0][0])
  else:L,W,a=e2,e1,math.atan2(cs[2][1]-cs[1][1],cs[2][0]-cs[1][0])
  return mr.centroid.x,mr.centroid.y,L,W,a
def flat(p):return [R2(c) for x,y in list(p.exterior.coords)[:-1] for c in (x,y)]
OUT={}
for f in ('T','AT'):
  F=D['floors'][f]
  rooms=[(r,Polygon(list(zip(r['pts'][0::2],r['pts'][1::2]))).buffer(0)) for r in F['rooms']]
  def roomAt(x,y):
    p=Point(x,y)
    for r,P in rooms:
      if P.contains(p):return r,P
    best=min(rooms,key=lambda rp:rp[1].distance(p))
    if best[1].distance(p)<.7 and not best[0]['n'].startswith('Escalera'):return best
    return None,None
  paths=[l for l in G[f]['lines']['f'] if len(l)>=4]
  lines=[LineString(list(zip(l[0::2],l[1::2]))) for l in paths]
  keep=[i for i,l in enumerate(lines) if l.length>.01]
  U=unary_union([lines[i].buffer(.025,cap_style=2) for i in keep])
  comps=[U] if U.geom_type=='Polygon' else list(U.geoms)
  tree=STRtree([lines[i] for i in keep])
  items=[];bathpaths=[]
  for c in comps:
    idx=[keep[j] for j in tree.query(c)]; idx=[i for i in idx if c.intersects(lines[i])]
    pts=[p for i in idx for p in lines[i].coords]
    if len(pts)<3:continue
    cx,cy,L,W,a=obb(pts); n=len(idx)
    r,P=roomAt(cx,cy)
    if r is None:continue
    rn=r['n']; u=r['u']
    foot=Polygon(c.exterior).simplify(.02)
    it=dict(u=u,room=rn,x=R2(cx),y=R2(cy),L=R2(L),W=R2(W),a=R2(a))
    # which long side faces the nearest wall: sign of the W-axis direction pointing to the wall
    nx,ny=-math.sin(a),math.cos(a)
    d1=P.exterior.distance(Point(cx+nx*W/2,cy+ny*W/2)); d2=P.exterior.distance(Point(cx-nx*W/2,cy-ny*W/2))
    it['wall']=1 if d1<=d2 else -1
    ex,ey=math.cos(a),math.sin(a)
    e1=P.exterior.distance(Point(cx+ex*L/2,cy+ey*L/2)); e2=P.exterior.distance(Point(cx-ex*L/2,cy-ey*L/2))
    it['endwall']=1 if e1<=e2 else -1
    if rn in ('Baño','Baño en suite','Aseo'):
      bathpaths+=idx; continue
    if rn.startswith('Dormitorio'):
      if L>=3.2 and W>=1.6: it['t']='twin'
      elif L>=2.2 and W>=1.8: it['t']='double'
      elif L>=1.7 and W>=1.3: it['t']='bed'   # double bed without nightstands
      elif L>=1.8 and .75<=W<1.3: it['t']='single'
      elif L>=1.0 and W<=.75: it['t']='desk'
      elif L>.35: it['t']='box'
      else: continue
    elif rn=='Terraza':
      if L<.35:continue
      it['t']='terrace_set' if (L>=1.0 and W>=.9) else ('lounger' if L>=1.6 else 'box_low')
    else: # living / kitchen
      if n>=90 or (n>=30 and L>=1.6 and W<=.8): it['t']='kitchen'; it['foot']=flat(foot)
      elif L>=2.3 and W>=1.9: it['t']='lounge'
      elif 1.7<=L<=3.4 and .7<=W<1.2: it['t']='sofa'
      elif 1.0<=L<2.6 and .85<=W<=1.9: it['t']='dining'
      elif L<1.05 and W>=.55: it['t']='armchair'
      elif L>=1.2 and W<=.5: it['t']='tv'
      elif L>.35: it['t']='box'
      else: continue
    items.append(it)
  # bathrooms: separate closed rings as fixtures
  rings=[]
  for i in set(bathpaths):
    l=paths[i]
    if len(l)>=8 and abs(l[0]-l[-2])<.01 and abs(l[1]-l[-1])<.01:
      P=Polygon(list(zip(l[0::2],l[1::2]))).buffer(0)
      if P.area>.06 and P.geom_type=='Polygon':rings.append(P)
  rings.sort(key=lambda p:-p.area); outer=[]
  for P in rings:
    if any(Q.buffer(.02).contains(P) for Q in outer):continue
    outer.append(P)
  for P in outer:
    cx,cy,L,W,a=obb(list(P.exterior.coords)); r,RP=roomAt(cx,cy)
    if r is None:continue
    if L>=1.5 and W>=.6: t='bath' 
    elif L>=.75 and W>=.7: t='shower'
    elif .5<=L<=.8 and .3<=W<=.45: t='toilet'
    elif .35<=L<=1.3 and W<=.6: t='sink'
    else: t='ceramic'
    nx,ny=-math.sin(a),math.cos(a)
    d1=RP.exterior.distance(Point(cx+nx*W/2,cy+ny*W/2)); d2=RP.exterior.distance(Point(cx-nx*W/2,cy-ny*W/2))
    ex,ey=math.cos(a),math.sin(a)
    e1=RP.exterior.distance(Point(cx+ex*L/2,cy+ey*L/2)); e2=RP.exterior.distance(Point(cx-ex*L/2,cy-ey*L/2))
    items.append(dict(u=r['u'],room=r['n'],t=t,x=R2(cx),y=R2(cy),L=R2(L),W=R2(W),a=R2(a),wall=1 if d1<=d2 else -1,endwall=1 if e1<=e2 else -1,foot=flat(P.simplify(.01))))
  OUT[f]=items
  print(f,collections.Counter(i['t'] for i in items))
D['furn']=OUT
json.dump(D,open('/home/claude/farnesio/data.json','w'),separators=(',',':'),ensure_ascii=False)
