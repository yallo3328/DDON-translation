"""DDON ARC(ARC/ARCC) 읽기 + GMD 파서 (Arrowgene.Ddon.Client 구조 기준)"""
import struct, zlib
from Crypto.Cipher import Blowfish
KEY=b"ABB(DF2I8[{Y-oS_CCMy(@<}qR}WYX11M)w[5V.~CbjwM5q<F1Iab+-"
_bf=Blowfish.new(KEY, Blowfish.MODE_ECB)
GMD_CRC=None
def _swap(b):
    a=bytearray(b)
    for i in range(0,len(a)-len(a)%4,4): a[i:i+4]=a[i:i+4][::-1]
    return bytes(a)
def bf_dec(b):
    n=len(b)-len(b)%8
    return _swap(_bf.decrypt(_swap(b[:n])))+b[n:]
def read_arc(path_or_bytes):
    d=path_or_bytes if isinstance(path_or_bytes,bytes) else open(path_or_bytes,'rb').read()
    magic=d[:4]; mid,cnt=struct.unpack_from('<HH',d,4)
    assert magic in (b'ARC\0',b'ARCC') and mid==7,(magic,mid)
    cyph=magic==b'ARCC'; out=[]
    for i in range(cnt):
        e=d[8+i*80:8+i*80+80]
        if cyph: e=bf_dec(e)
        name=e[:64].split(b'\0')[0].decode('utf-8','replace')
        crc,csz,flags,off=struct.unpack_from('<IIII',e,64)
        size=flags&((1<<29)-1)
        raw=d[off:off+csz]
        if cyph: raw=bf_dec(raw)
        try: data=zlib.decompress(raw)
        except Exception:
            data=zlib.decompressobj().decompress(raw)
        out.append(dict(name=name,crc=crc,size=size,data=data))
    return out
def parse_gmd(b):
    p=4
    ver,lang=struct.unpack_from('<II',b,p); p+=8
    p+=8 # update time
    kc,sc,ks,ss,sl=struct.unpack_from('<5I',b,p); p+=20
    name=b[p:p+sl].decode('utf-8','replace'); p+=sl+1
    if kc: p+=kc*20+256*4
    def cstr():
        nonlocal p
        e=b.index(b'\0',p); s=b[p:e].decode('utf-8','replace'); p=e+1; return s
    keys=[cstr() for _ in range(kc)]
    msgs=[cstr() for _ in range(sc)]
    return dict(version=ver,lang=lang,name=name,keys=keys,msgs=msgs)
