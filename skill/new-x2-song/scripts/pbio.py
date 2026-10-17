import re
def rv(b,i):
    r=s=0
    while True:
        c=b[i];i+=1;r|=(c&0x7f)<<s;s+=7
        if c<0x80:return r,i
def wv(n):
    o=bytearray()
    while True:
        c=n&0x7f;n>>=7
        if n:o.append(c|0x80)
        else:o.append(c);return bytes(o)
def parse(b):
    i=0;out=[]
    while i<len(b):
        t,i=rv(b,i);f,w=t>>3,t&7
        if w==0:
            s=i;_,i=rv(b,i);out.append((f,w,b[s:i]))
        elif w==1:out.append((f,w,b[i:i+8]));i+=8
        elif w==5:out.append((f,w,b[i:i+4]));i+=4
        elif w==2:
            l,i=rv(b,i);out.append((f,w,b[i:i+l]));i+=l
        else:raise ValueError(w)
    return out
def serialize(es):
    o=bytearray()
    for f,w,r in es:
        o+=wv(f<<3|w)
        if w==2:o+=wv(len(r))
        o+=r
    return bytes(o)
def nth(es,f,k):
    c=0
    for idx,e in enumerate(es):
        if e[0]==f:
            if c==k:return idx
            c+=1
    raise KeyError((f,k))
def get_path(b,path):
    for f,k in path:
        es=parse(b);b=es[nth(es,f,k)][2]
    return b
def set_path(b,path,val):
    if not path:return val
    es=parse(b);f,k=path[0];j=nth(es,f,k)
    es[j]=(es[j][0],es[j][1],set_path(es[j][2],path[1:],val))
    return serialize(es)
def rtf_text(r):
    s=r.decode('utf-8','replace')
    m=re.search(r'\\(?:uc0|strokec3) ?(.*)\}\s*$',s,re.S)
    body=m.group(1) if m else s
    body=re.sub(r'\\u(\d+) ?',lambda m:chr(int(m.group(1))),body)
    return body.replace('\\\n',' / ')
