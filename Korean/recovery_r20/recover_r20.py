import csv, io, os, sys, collections, json
sys.path.insert(0, os.path.dirname(__file__)); import ddonarc
src_csv, rom, out_dir = sys.argv[1:4]
raw=open(src_csv,'rb').read().decode('utf-8-sig')
rows=list(csv.reader(io.StringIO(raw,newline='')))
hdr,body=rows[0],rows[1:]
norm=lambda s: s.replace('/','\\').lower().lstrip('\\')
lookup=collections.defaultdict(lambda: collections.defaultdict(list))
for i,r in enumerate(body): lookup[norm(r[5])][norm(r[4])].append(i)
recovered={}; conflicts=[]; unmatched=[]; arc_missing=[]; gmd_nocsv=0; arcs=0; gmds=0
for dp,_,fs in os.walk(rom):
  for f in fs:
    if not f.lower().endswith('.arc'): continue
    full=os.path.join(dp,f); rel=norm(os.path.relpath(full,rom))
    arcs+=1
    if rel not in lookup: arc_missing.append(rel); continue
    for e in ddonarc.read_arc(full):
      if e['data'][:4]!=b'GMD\0': continue
      gp=norm(e['name']+'.gmd')
      if gp not in lookup[rel]: gmd_nocsv+=1; continue
      gmds+=1
      g=ddonarc.parse_gmd(e['data']); idxs=lookup[rel][gp]
      for ri,msg in enumerate(g['msgs']):
        key=g['keys'][ri] if ri<len(g['keys']) else ''
        km=[i for i in idxs if key and body[i][1]==key]
        im=[i for i in idxs if not(key and body[i][1]==key) and body[i][7]==str(ri)]
        m=next((i for i in km if body[i][7]==str(ri)),None)
        if m is None: m=km[0] if km else (im[0] if im else None)
        if m is None: unmatched.append((rel,gp,ri,key,msg)); continue
        if m in recovered and recovered[m]!=msg: conflicts.append((m,recovered[m],msg))
        recovered[m]=msg
changed=[]
for i,msg in recovered.items():
  if body[i][3]!=msg:
    changed.append(dict(row=i+2,arc=body[i][5],gmd=body[i][4],key=body[i][1],jp=body[i][2],v13_2=body[i][3],r20=msg))
    body[i][3]=msg
os.makedirs(out_dir,exist_ok=True)
s=io.StringIO(); csv.writer(s,lineterminator='\n').writerows([hdr]+body)
open(os.path.join(out_dir,'gmd_ko_r20_recovered.csv'),'wb').write(('﻿'+s.getvalue()).encode())
with open(os.path.join(out_dir,'r20_vs_v13_2_changes.csv'),'w',encoding='utf-8-sig',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=list(changed[0].keys()) if changed else ['row']); w.writeheader(); w.writerows(changed)
with open(os.path.join(out_dir,'r20_unmatched_entries.csv'),'w',encoding='utf-8-sig',newline='') as fh:
  w=csv.writer(fh); w.writerow(['arc','gmd','read_index','key','msg']); w.writerows(unmatched)
rep=dict(arcs_scanned=arcs,arcs_not_in_csv=arc_missing,gmd_matched=gmds,gmd_not_in_csv=gmd_nocsv,
  rows_recovered=len(recovered),rows_changed_vs_v13_2=len(changed),unmatched_entries=len(unmatched),conflicts=len(conflicts))
json.dump(rep,open(os.path.join(out_dir,'recovery_report.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps({k:(v if not isinstance(v,list) else len(v)) for k,v in rep.items()},ensure_ascii=False))
print('missing arcs sample',arc_missing[:10]); print('conflict sample',conflicts[:3])
