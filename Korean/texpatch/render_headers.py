import sys,io,json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
src=Image.open('tex/word_raw.png').convert('RGBA')
A=np.array(src).astype(np.float32)
# sample colors from original
items=[(342,361,5,92,'캐릭터'),(375,393,10,71,'퀘스트'),(407,425,11,71,'월드'),(439,457,6,83,'파티'),(471,489,4,136,'커뮤니케이션'),(501,521,6,83,'옵션'),(533,553,0,132,'온라인 숍')]
out=src.copy()
CLEAR=(0,338,150,559)
# background = transparent as in source corners
bgpix=tuple(int(v) for v in A[600,140])
d=ImageDraw.Draw(out); d.rectangle(CLEAR,fill=(0,0,0,0))
idx=1 # Korean font index in ttc: 0=JP,1=KR
for y0,y1,x0,x1,txt in items:
    h=y1-y0+1
    size=17
    f=ImageFont.truetype(FONT,size,index=idx)
    bb=f.getbbox(txt)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    W=150; layer=Image.new('L',(W,40),0); dl=ImageDraw.Draw(layer)
    ox=x0+3-bb[0]; oy=(40-th)//2-bb[1]+1
    dl.text((ox,oy),txt,font=f,fill=255)
    glow=layer.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2.2))
    g=np.array(glow).astype(np.float32)/255.0
    core=np.array(layer).astype(np.float32)/255.0
    rgb=np.zeros((40,W,3),np.float32); al=np.zeros((40,W),np.float32)
    ga=np.clip(g*1.6,0,1)*0.7
    glow_rgb=np.array([214,196,20],np.float32)
    core_rgb=np.array([255,252,215],np.float32)
    al=ga+core*(1-ga)
    rgb=(glow_rgb*ga[...,None]*(1-core[...,None])+core_rgb*core[...,None])/np.maximum(al[...,None],1e-4)
    tile=Image.fromarray(np.dstack([np.clip(rgb,0,255),np.clip(al*255,0,255)]).astype(np.uint8),'RGBA')
    cy=(y0+y1)//2
    out.alpha_composite(tile,(0,cy-20))
out.save('texpatch/word_new.png')
def comp(im,box):
    c=im.crop(box); bg=Image.new('RGBA',c.size,(25,22,18,255)); bg.alpha_composite(c); return bg
L=comp(src,CLEAR); R=comp(out,CLEAR)
sheet=Image.new('RGBA',(L.width*2+10,L.height),(60,60,60,255)); sheet.paste(L,(0,0)); sheet.paste(R,(L.width+10,0))
sheet.resize((sheet.width*3,sheet.height*3),Image.NEAREST).save('texpatch/compare_headers.png')
