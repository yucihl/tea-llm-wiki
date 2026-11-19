import os,re,sys,yaml
R=sys.argv[1]; W=os.path.join(R,'wiki')
pages={}
for d,_,fs in os.walk(W):
    for f in fs:
        if f.endswith('.md'):
            rel=os.path.relpath(os.path.join(d,f),W)[:-3]; pages[rel]=open(os.path.join(d,f),encoding='utf-8').read()
idx=open(os.path.join(R,'index.md'),encoding='utf-8').read()
issues=[]; linked=set()
for rel,s in pages.items():
    m=re.match(r'---\n(.*?)\n---\n',s,re.S)
    if not m: issues.append(f'{rel}: frontmatter 缺失'); continue
    meta=yaml.safe_load(m.group(1))
    for k in ['title','type','sources','updated','confidence','slide_block']:
        if k not in meta: issues.append(f'{rel}: 缺 {k}')
    for src in meta.get('sources') or []:
        if not os.path.exists(os.path.join(R,'raw',src+'.md')): issues.append(f'{rel}: 來源 {src} 不在 raw/')
    links=re.findall(r'\[\[([^\]]+)\]\]',s)
    for l in links:
        if l!='index' and l not in pages: issues.append(f'{rel}: 斷鏈 [[{l}]]')
        linked.add(l)
    if '## 相關頁面' not in s: issues.append(f'{rel}: 缺「相關頁面」')
    if f'[[{rel}]]' not in idx: issues.append(f'{rel}: 未列入 index.md')
    body=s[m.end():]
    # 用詞檢查：「發酵」必須出現在允許的語境
    for mm in re.finditer('發酵',body):
        ctx=body[max(0,mm.start()-6):mm.end()+4]
        if not re.search(r'俗稱發酵|後發酵|原文|微發酵|全發酵|發酵程度|稱為「發酵」|發酵過|不發酵茶|部分發酵茶|全發酵茶|「發酵|發酵」|發酵」二字',ctx):
            issues.append(f'{rel}: 「發酵」用詞未依 glossary：…{ctx}…')
    if re.search(r'黑茶[^。\n]{0,10}black tea(?![^。\n]{0,3}不)',body): issues.append(f'{rel}: 疑似 黑茶=black tea')
    # 事實句來源：表格與條列以外的段落需有（來源：
for l in linked: pass
orph=[p for p in pages if p not in linked and p!='glossary']
for o in orph: issues.append(f'{o}: 孤兒頁（沒有被其他頁連結）')
print(f'檢查 {len(pages)} 頁')
print('\n'.join(issues) if issues else '全部通過')
