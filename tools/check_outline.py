"""大綱檢查（AGENTS.md 4.4）。用法：python3 tools/check_outline.py <wiki根目錄>"""
import os,re,sys
sys.path.insert(0,os.path.dirname(__file__))
from outline_lib import load,slide_text
R=sys.argv[1]; W=os.path.join(R,'wiki')
meta,blocks,closing=load(os.path.join(R,'output','slides'))
def wiki_page(p):
    f=os.path.join(W,p+'.md'); return open(f,encoding='utf-8').read() if os.path.exists(f) else None
def norm(t): return t.replace('–','-').replace('～','-').replace('~','-').replace('，',',')
errs=[]; warns=[]
for b,sl in list(blocks.items())+[('Z',closing)]:
    if b!='Z' and len(sl)>8: errs.append(f'區塊 {b}: {len(sl)} 頁，超過 8 頁')
    for s in sl:
        sid=s['id']; txt=slide_text(s)
        if not s['wiki']: errs.append(f'{sid}: 沒有列出 wiki 來源'); continue
        src=''
        for p in s['wiki']:
            c=wiki_page(p)
            if c is None: errs.append(f'{sid}: wiki 頁不存在 {p}'); continue
            src+=c
            m=re.search(r'slide_block: (.*)',c)
            if b!='Z' and m and b not in m.group(1) and not p.startswith('glossary'): warns.append(f'{sid}: {p} 的 slide_block 未含 {b}')
        ns=norm(src)
        for num in set(re.findall(r'\d+(?:[.,:]\d+)*',norm(txt))):
            if num not in ns and num.replace(',','') not in ns.replace(',',''): errs.append(f'{sid}: 數字「{num}」在引用的 Wiki 頁中找不到')
        if '%' in txt or '％' in txt: errs.append(f'{sid}: 出現百分比（使用者決定簡報不寫百分比）')
        for mm in re.finditer('發酵',txt):
            ctx=txt[max(0,mm.start()-6):mm.end()+4]
            if not re.search(r'俗稱發酵|後發酵|部分發酵茶|「發酵|發酵」',ctx): errs.append(f'{sid}: 「發酵」用詞未依 glossary：…{ctx.strip()}…')
        if re.search(r'黑茶[^。\n]{0,6}black tea',txt) and 'dark tea' not in txt: errs.append(f'{sid}: 疑似 黑茶=black tea')
        if '殺青' in txt: errs.append(f'{sid}: 用「殺青」，glossary 統一為「殺菁」')
        for k in ('bullets',):
            if len(s.get(k,[]))>4: errs.append(f'{sid}: 重點超過 4 個')
        for k in ('left','right','story'):
            if k in s and len(s[k]['items'])>4: errs.append(f'{sid}: {k} 超過 4 點')
        if '待查證' in txt or '🔍' in txt: errs.append(f'{sid}: 含待查證內容')
total=sum(len(v) for v in blocks.values())
print(f'大綱檢查：{total} 頁（' + '、'.join(f'{b} {len(v)}' for b,v in blocks.items()) + '）＋結尾 1 頁')
print('錯誤：' if errs else '錯誤：無'); [print('  ❌',e) for e in errs]
print('提醒：' if warns else '提醒：無'); [print('  ⚠️',w) for w in warns]
sys.exit(1 if errs else 0)
