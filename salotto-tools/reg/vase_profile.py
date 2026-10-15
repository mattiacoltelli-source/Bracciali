import os, sys
os.environ['FRAME_EXT']='1'
sys.path.insert(0,'/tmp/claude-0/s/reg')
import numpy as np, cv2
from plane import FR
from vline import ray
fr=FR(); cam='50f7be75'
img=fr.image(cam).astype(np.float32)
x0,y0,x1,y1=3200,1660,3480,1940
crop=img[y0:y1,x0:x1]; b,g,r=crop[...,0],crop[...,1],crop[...,2]
m=((r>1.9*g)&(r>1.9*b)&(r>38)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(m); k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); comp=lab==k
cv2.imwrite('/tmp/claude-0/s/vaso/redmask.png',comp.astype(np.uint8)*255)
CX,CZ=6.685,0.30
C=fr.cams[cam]['C']; d=np.array([CX-C[0],0,CZ-C[2]]); d/=np.linalg.norm(d); nrm=d  # normale del piano = direzione di vista orizzontale
rows=[]
for yy in list(range(30,70,3))+list(range(200,250,5)):
    xs=np.nonzero(comp[yy])[0]
    if len(xs)<10: continue
    L=xs.min()+x0; R_=xs.max()+x0; v=yy+y0
    pts=[]
    for u in (L,R_+1):
        P0,dd=ray(fr,cam,u,v)
        t=(nrm@(np.array([CX,0,CZ])-P0))/(nrm@dd)   # intersezione col piano (n.(p-asse)=0), y libera
        pts.append(P0+t*dd)
    w=np.linalg.norm(pts[1]-pts[0]); y=(pts[0][1]+pts[1][1])/2
    rows.append((v,L,R_,round(float(w),4),round(float(y),3),round(float(pts[0][0]+pts[1][0])/2,3)))
for r in rows: print('riga %d  L %d R %d  diametro %.4f m  quota %.3f  centro x %.3f'%r)
