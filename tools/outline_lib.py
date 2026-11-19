"""解析 output/slides/outline-*.md。大綱是簡報的唯一內容來源。"""
import os,re,glob
LIST_KEYS={'cards','steps','items','regions','facts','bullets','table','blocks','groups','pins'}
def parse_file(path):
    txt=open(path,encoding='utf-8').read()
    meta={}; slides=[]; cur=None; key=None
    for raw in txt.split('\n'):
        line=raw.rstrip()
        m=re.match(r'^## (\w+) \| (.+)$',line)
        if m:
            cur={'id':m.group(1),'title':m.group(2).strip(),'file':os.path.basename(path)}; slides.append(cur); key=None; continue
        tgt=cur if cur is not None else meta
        if not line.strip() or line.startswith('# ') or line.startswith('>'): continue
        if line.startswith('|'):
            tgt.setdefault('table',[]).append(line); key='table'; continue
        m=re.match(r'^(\w+):\s*(.*)$',line)
        if m and not line.startswith('- '):
            k,v=m.group(1),m.group(2).strip()
            if k in ('left','right','story'):
                tgt[k]={'head':v,'items':[]}; key=k
            elif k in LIST_KEYS and not v:
                tgt[k]=[]; key=k
            else:
                tgt[k]=v; key=None
            continue
        if line.startswith('- ') and key:
            item=line[2:].strip()
            if key in ('left','right','story'): tgt[key]['items'].append(item)
            else: tgt[key].append(item)
    for s in slides:
        s['wiki']=[w.strip() for w in s.get('wiki','').split(',') if w.strip()]
        if 'table' in s:
            rows=[[c.strip() for c in r.strip('|').split('|')] for r in s['table']]
            s['table']=[r for r in rows if not all(re.fullmatch(r':?-{2,}:?',c) or c=='' for c in r) or any(c for c in r if not re.fullmatch(r':?-{2,}:?',c))]
            s['table']=[r for r in s['table'] if not all(re.fullmatch(r':?-{2,}:?',c) for c in r if c)]
        for k in ('cards','steps','items','regions','facts','groups','pins'):
            if k in s: s[k]=[[p.strip() for p in it.split('|')] for it in s[k]]
        for k in ('callout',):
            if k in s: s[k]=[p.strip() for p in s[k].split('|',1)]
    return meta,slides
def load(slides_dir):
    meta,_=parse_file(os.path.join(slides_dir,'outline-00-meta.md'))
    blocks={}
    for b in ['A','B','C','D','E']:
        _,sl=parse_file(os.path.join(slides_dir,f'outline-{b}.md')); blocks[b]=sl
    _,closing=parse_file(os.path.join(slides_dir,'outline-00-meta.md'))
    meta['blocks']=[[p.strip() for p in x.split('|')] for x in meta.get('blocks',[])]
    return meta,blocks,closing
def slide_text(s):
    parts=[s['title'],s.get('lead',''),s.get('note',''),s.get('big','')]
    for k in ('bullets',): parts+=s.get(k,[])
    for k in ('cards','steps','items','regions','facts','groups','pins'): parts+=[' '.join(x) for x in s.get(k,[])]
    parts+=[s.get('origin',''),s.get('center','')]
    for k in ('left','right','story'):
        if k in s: parts+=[s[k]['head']]+s[k]['items']
    if 'table' in s: parts+=[' '.join(r) for r in s['table']]
    if 'callout' in s: parts+=s['callout']
    return '\n'.join(p for p in parts if p)
