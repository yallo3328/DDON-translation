import csv,io,os,sys,collections
sys.path.insert(0,os.path.dirname(__file__)); import ddonarc
csvp,rom=sys.argv[1:3]
body=list(csv.reader(io.StringIO(open(csvp,encoding='utf-8-sig',newline='').read(),newline='')))[1:]
norm=lambda s: s.replace('/','\\').lower().lstrip('\\')
lk=collections.defaultdict(lambda: collections.defaultdict(list))
for r in body: lk[norm(r[5])][norm(r[4])].append(r)
c=collections.Counter(); bad=[]
for dp,_,fs in os.walk(rom):
  for f in fs:
    if not f.lower().endswith('.arc'): continue
    rel=norm(os.path.relpath(os.path.join(dp,f),rom))
    for e in ddonarc.read_arc(os.path.join(dp,f)):
      if e['data'][:4]!=b'GMD\0': continue
      rows=lk.get(rel,{}).get(norm(e['name']+'.gmd'))
      if not rows: continue
      g=ddonarc.parse_gmd(e['data'])
      for ri,msg in enumerate(g['msgs']):
        key=g['keys'][ri] if ri<len(g['keys']) else ''
        km=[r for r in rows if key and r[1]==key]; im=[r for r in rows if not(key and r[1]==key) and r[7]==str(ri)]
        m=next((r for r in km if r[7]==str(ri)),None) or (km[0] if km else None) or (im[0] if im else None)
        if m is None: c['no_row']+=1; continue
        if not m[3]: c['empty_csv']+=1; continue
        if m[3]==msg: c['match']+=1
        else: c['diff']+=1; len(bad)<5 and bad.append((rel,ri,m[3][:50],msg[:50]))
print(dict(c)); print(*bad,sep='\n')
