import csv,io,re,collections,random,sys,json
rd=lambda p: list(csv.reader(io.StringIO(open(p,encoding='utf-8-sig',newline='').read(),newline='')))
ko=rd(sys.argv[1]); en=rd(sys.argv[2]); out=sys.argv[3]
k=lambda r:(r[0],r[1],r[4].lower(),r[5].lower(),r[7])
enm={k(r):r for r in en[1:]}
HAN=re.compile('[가-힣]'); KANA=re.compile('[぀-ヿ]'); KANJI=re.compile('[一-鿿]'); LAT=re.compile('[A-Za-z]{3,}')
TAG=re.compile(r'<[^<>]+>')
def tags(s): return collections.Counter(re.sub(r'\s+.*','',t) for t in TAG.findall(s))
# 고유 문자열 단위(중복 행 제거: GmdPath+Index+Key)
seen=set(); uniq=[]
for r in ko[1:]:
  u=(r[4].lower(),r[0],r[1],r[7])
  if u in seen: continue
  seen.add(u); uniq.append(r)
cat=collections.Counter(); issues=collections.defaultdict(list)
def area(g):
  g=g.lower()
  for a in ['quest_info','\\quest\\','\\npc\\','pw_talk','skill','item','tutorial','tguide','event','enemy','stage','ui\\']:
    if a in g: return a.strip('\\')
  return 'etc'
area_c=collections.defaultdict(collections.Counter)
for r in uniq:
  ko_t=r[3]; e=enm[k(r)][3]; a=area(r[4])
  if not ko_t.strip():
    c='empty'
  elif HAN.search(ko_t): c='korean'
  elif KANA.search(ko_t): c='japanese_left'
  elif LAT.search(ko_t): c='english_left'
  else: c='symbol_only'
  cat[c]+=1; area_c[a][c]+=1
  if c=='korean':
    if KANA.search(ko_t): issues['kana_mixed'].append(r)
    te,tk=tags(e),tags(ko_t)
    if e and te!=tk: issues['tag_mismatch'].append((r,dict(te),dict(tk)))
    lines=ko_t.replace('\r\n','\n').split('\n')
    if max(len(l) for l in lines)>50: issues['line_over_50'].append(r)
    if len(lines)>12: issues['lines_over_12'].append(r)
    if len(ko_t)>695: issues['total_over_695'].append(r)
    if ko_t.count('\n')!=e.count('\n') and e: issues['newline_count_diff'].append(r)
# 일관성: 같은 일본어 원문(짧은 용어) -> 서로 다른 번역
jp2ko=collections.defaultdict(collections.Counter)
for r in uniq:
  if r[2] and len(r[2])<=12 and HAN.search(r[3]) and '\n' not in r[2]: jp2ko[r[2]][r[3]]+=1
incons=[(jp,dict(v)) for jp,v in jp2ko.items() if len(v)>1]
rep=dict(unique_strings=len(uniq),coverage=dict(cat),by_area={a:dict(v) for a,v in area_c.items()},
  issues={n:len(v) for n,v in issues.items()},short_term_inconsistencies=len(incons))
print(json.dumps(rep,ensure_ascii=False,indent=1))
with open(out+'/qa_issues.csv','w',encoding='utf-8-sig',newline='') as fh:
  w=csv.writer(fh); w.writerow(['issue','row_key','gmd','jp','en','ko','detail'])
  for n,v in issues.items():
    for x in v:
      r,d=(x[0],f'en={x[1]} ko={x[2]}') if isinstance(x,tuple) else (x,'')
      w.writerow([n,r[1] or r[0],r[4],r[2],enm[k(r)][3],r[3],d])
with open(out+'/qa_term_inconsistency.csv','w',encoding='utf-8-sig',newline='') as fh:
  w=csv.writer(fh); w.writerow(['jp','variants(count)'])
  for jp,v in sorted(incons,key=lambda x:-sum(x[1].values())): w.writerow([jp,' | '.join(f'{a}({b})' for a,b in sorted(v.items(),key=lambda y:-y[1]))])
json.dump(rep,open(out+'/qa_summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
random.seed(7)
smp=[r for r in uniq if HAN.search(r[3]) and ('\\quest\\' in r[4].lower() or '\\npc\\' in r[4].lower()) and len(r[3])>25]
for r in random.sample(smp,25): print('EN:',enm[k(r)][3].replace('\n',' / ')[:160]); print('KO:',r[3].replace('\n',' / ')[:160]); print()
for jp,v in sorted(incons,key=lambda x:-sum(x[1].values()))[:25]: print(jp,v)
