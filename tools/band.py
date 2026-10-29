import fitz,json,math,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from shapely.geometry import LineString,Polygon
pg=fitz.open('/mnt/user-data/attachments/5da709fc-37c6-5060-9812-d1c3a3e2639a/84ca775f-1793222817186_Planta_BAJA.pdf')[0]
s=8.1/153; T=lambda p:(78.05+(p.y-492)*s, 20.3+(p.x-478)*s)
mids=[]
for p in pg.get_drawings():
  for it in p['items']:
    if it[0]=='l':
      a,b=T(it[1]),T(it[2]);L=math.dist(a,b)
      if .005<L<.3:
        mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
        if not((61<mx<75.5 and 1.1<my<33) or (66<mx<111.8 and 23.5<my<31.9)):continue
        if 77<mx<88.5 and 19<my<26.1:continue
        if mx>96 and my>31.6:continue
        mids.append((mx,my))
def walk(start,pts,maxgap):
  pts=list(pts);out=[start];cur=start
  while pts:
    j=min(range(len(pts)),key=lambda k:math.dist(cur,pts[k]))
    if math.dist(cur,pts[j])>maxgap:break
    cur=pts.pop(j);out.append(cur)
  return out
isOuter=lambda m:m[0]<68.5 or m[1]>28.5
outer=walk((67.5,1.1),[m for m in mids if isOuter(m)],1.6)
inner=walk((72.6,1.1),[m for m in mids if not isOuter(m)],1.6)
print(len(outer),outer[-1],len(inner),inner[-1])
def thin(pl,d=.3):
  o=[pl[0]]
  for p in pl[1:]:
    if math.dist(o[-1],p)>=d:o.append(p)
  return o
outer=LineString(thin(outer)).simplify(.05);inner=LineString(thin(inner)).simplify(.05)
ring=list(outer.coords)+[(112.3,outer.coords[-1][1]),(112.3,inner.coords[-1][1])]+list(inner.coords)[::-1]
band=Polygon(ring).buffer(0)
print(band.geom_type,round(band.area,1))
fig,ax=plt.subplots(figsize=(16,10),dpi=60)
ax.fill(*band.exterior.xy,color='g',alpha=.4)
ax.add_patch(plt.Rectangle((78.05,20.3),8.1,5.25,fill=False))
ax.set_aspect('equal');plt.savefig('band.png',bbox_inches='tight')
D=json.load(open('/home/claude/farnesio/data.json'))
D['pb']['band']=[round(c,3) for x,y in list(band.exterior.coords)[:-1] for c in (x,y)]
json.dump(D,open('/home/claude/farnesio/data.json','w'),separators=(',',':'),ensure_ascii=False)
