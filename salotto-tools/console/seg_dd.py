import sys; sys.path.insert(0,'/tmp/claude-0/s/st3')
from seglib import *
im,s=load('da59d0fd'); box=(660,270,790,470)
x0,y0,x1,y1=[int(v*s) for v in box]; c=im[y0:y1,x0:x1].copy(); h,w=c.shape[:2]
def P(x,y): return (int((x*s-x0)),int((y*s-y0)))
fgm=np.zeros((h,w),np.uint8)
def rrect(xa,ya,xb,yb,r):
    for (cx,cy) in ((xa+r,ya+r),(xb-r,ya+r),(xa+r,yb-r),(xb-r,yb-r)): cv2.circle(fgm,P(cx,cy),int(r*s),255,-1)
    cv2.rectangle(fgm,P(xa+r,ya),P(xb-r,yb),255,-1); cv2.rectangle(fgm,P(xa,ya+r),P(xb,yb-r),255,-1)
rrect(680,318,761.5,381,12)
cv2.rectangle(fgm,P(703,376),P(751,424),255,-1)
cv2.rectangle(fgm,P(708,420),P(748,446),255,-1)
cv2.ellipse(fgm,P(722,436),(int(16*s),int(9*s)),0,0,360,255,-1); cv2.ellipse(fgm,P(738,438),(int(13*s),int(8*s)),0,0,360,255,-1)
cv2.circle(fgm,P(667,372),int(8*s),255,-1); cv2.circle(fgm,P(766,366),int(7*s),255,-1)
cv2.line(fgm,P(667,372),P(703,392),255,int(9*s)); cv2.line(fgm,P(766,366),P(751,390),255,int(8*s))
cv2.fillPoly(fgm,[np.array([P(706,279),P(712,279),P(676,402),P(667,404)],np.int32)],255)
k=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*int(r*s)+1,2*int(r*s)+1))
sure=cv2.erode(fgm,k(3)); prob=cv2.dilate(fgm,k(4)); bgsure=cv2.dilate(fgm,k(8))==0
mask=np.full((h,w),cv2.GC_PR_BGD,np.uint8); mask[prob>0]=cv2.GC_PR_FGD; mask[sure>0]=cv2.GC_FGD; mask[bgsure]=cv2.GC_BGD
small=cv2.resize(c,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_AREA); ms=cv2.resize(mask,(small.shape[1],small.shape[0]),interpolation=cv2.INTER_NEAREST)
bgd=np.zeros((1,65)); fgd=np.zeros((1,65)); cv2.grabCut(small,ms,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
out=((ms==cv2.GC_FGD)|(ms==cv2.GC_PR_FGD)).astype(np.uint8)*255; out=cv2.resize(out,(w,h)); out=cv2.GaussianBlur(out,(0,0),1.2); out=(out>127).astype(np.uint8)*255
cv2.imwrite('work/mask_dd.png',out); cv2.imwrite('work/crop_dd.png',c); overlay(c,out,'work/seg_dd.jpg',0.6); cv2.imwrite('work/dd_init.png',fgm)
print(c.shape,(out>0).mean())
