"""把 Wiki（Markdown + [[連結]]）轉成可在 GitHub Pages 點擊瀏覽的 HTML 網站。
GitHub 不支援 Obsidian 的 [[頁面]] 寫法，所以另外產生 wiki-site/。
用法：python3 tools/build_wiki_site.py <專案根目錄> <GitHub repo 網址>
"""
import os, re, sys, html, shutil, yaml, markdown

R = sys.argv[1]
REPO = sys.argv[2].rstrip('/')          # 例：https://github.com/yucihl/tea-llm-wiki
W = os.path.join(R, 'wiki'); OUT = os.path.join(R, 'wiki-site')
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)

def split_fm(s):
    m = re.match(r'---\n(.*?)\n---\n', s, re.S)
    return (yaml.safe_load(m.group(1)) or {}, s[m.end():]) if m else ({}, s)

# 收集頁面：key = Wiki 連結用的路徑（不含 .md）
pages = {}
for d, _, fs in os.walk(W):
    for f in fs:
        if f.endswith('.md'):
            key = os.path.relpath(os.path.join(d, f), W)[:-3]
            pages[key] = open(os.path.join(d, f), encoding='utf-8').read()
pages['index'] = open(os.path.join(R, 'index.md'), encoding='utf-8').read()
pages['AGENTS'] = open(os.path.join(R, 'AGENTS.md'), encoding='utf-8').read()
pages['log'] = open(os.path.join(R, 'log.md'), encoding='utf-8').read()
titles = {k: (split_fm(v)[0].get('title') or k) for k, v in pages.items()}
titles.update({'index': 'Wiki 目錄', 'AGENTS': '規則書 AGENTS.md', 'log': '操作紀錄 log.md'})

def rel(frm, to):
    depth = frm.count('/')
    return '../' * depth + to + '.html'

def convert_links(text, here):
    def sub(m):
        target, _, label = m.group(1).partition('|')
        target = target.strip()
        if target not in pages:
            return html.escape(m.group(0))
        return f'[{label or titles[target]}]({rel(here, target)})'
    return re.sub(r'\[\[([^\]]+)\]\]', sub, text)

CSS = """
:root{--green-50:#F1F6EE;--green-100:#E4EFDF;--green-300:#A8C5A0;--green-700:#4E6B4F;--cream:#FAF6EE;--white:#FFFFFF;--yellow:#F6EBC4;--tan-200:#D9C3A5;--tan-700:#7A5C3E;--text:#3F3A33;--text-soft:#6B655C}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--text);font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;line-height:1.75;font-size:17px}
header{background:var(--green-100);border-bottom:1px solid var(--tan-200)}
header nav{max-width:960px;margin:0 auto;padding:12px 24px;display:flex;flex-wrap:wrap;gap:6px 20px;align-items:center}
header a{color:var(--green-700);text-decoration:none;font-weight:500}header a:hover{text-decoration:underline}
header .brand{font-family:"Noto Serif TC",serif;font-weight:700;font-size:19px;margin-right:auto}
main{max-width:960px;margin:0 auto;padding:28px 24px 64px}
h1,h2,h3{font-family:"Noto Serif TC","Songti TC",serif;color:var(--green-700);line-height:1.35}
h1{font-size:32px;margin:8px 0 12px}h2{font-size:24px;margin-top:36px;border-bottom:1px solid var(--tan-200);padding-bottom:6px}
a{color:var(--green-700)}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px;font-size:14px}
.meta span{background:var(--white);border:1px solid var(--tan-200);border-radius:999px;padding:2px 12px;color:var(--text-soft)}
.meta .conf-high{background:var(--green-100)}.meta .conf-low{background:var(--yellow)}
table{border-collapse:collapse;margin:12px 0;font-size:15px;display:block;overflow-x:auto;max-width:100%}
th,td{border:1px solid var(--tan-200);padding:8px 12px;text-align:left;vertical-align:top;background:var(--white)}
th{background:var(--green-100);color:var(--green-700)}
blockquote{margin:12px 0;padding:8px 16px;background:var(--yellow);border-radius:10px;border:none}
code{background:var(--green-50);padding:1px 5px;border-radius:4px;font-size:.92em}
pre{background:var(--white);border:1px solid var(--tan-200);border-radius:10px;padding:14px;overflow-x:auto}pre code{background:none;padding:0}
footer{max-width:960px;margin:0 auto;padding:0 24px 40px;color:var(--text-soft);font-size:14px}
"""

def page_html(key, body_md):
    fm, body = split_fm(body_md)
    md = markdown.markdown(convert_links(body, key), extensions=['tables', 'fenced_code', 'sane_lists'])
    meta = ''
    if fm:
        chips = []
        if fm.get('type'): chips.append(f'<span>類型：{html.escape(str(fm["type"]))}</span>')
        if fm.get('confidence'): chips.append(f'<span class="conf-{fm["confidence"]}">信心度：{fm["confidence"]}</span>')
        if fm.get('slide_block'): chips.append(f'<span>簡報區塊：{html.escape(str(fm["slide_block"]))}</span>')
        if fm.get('updated'): chips.append(f'<span>更新：{fm["updated"]}</span>')
        for s in fm.get('sources') or []:
            chips.append(f'<span><a href="{REPO}/blob/main/raw/{s}.md">原文 {html.escape(s)}</a></span>')
        meta = '<div class="meta">' + ''.join(chips) + '</div>'
    up = '../' * key.count('/')
    nav = (f'<header><nav><a class="brand" href="{up}../index.html">茶知識 LLM Wiki</a>'
           f'<a href="{up}index.html">Wiki 目錄</a><a href="{up}glossary.html">名詞表</a>'
           f'<a href="{up}AGENTS.html">規則書</a><a href="{up}log.html">操作紀錄</a>'
           f'<a href="{up}../output/slides/tea-intro.html">教學簡報</a><a href="{REPO}">GitHub</a></nav></header>')
    if md.lstrip().startswith('<h1'):
        i = md.index('</h1>') + 5; md = md[:i] + meta + md[i:]
    else:
        md = meta + md
    return (f'<!DOCTYPE html><html lang="zh-Hant-TW"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(str(titles[key]))}｜茶知識 LLM Wiki</title><style>{CSS}</style></head>'
            f'<body>{nav}<main>{md}</main><footer>由 <code>tools/build_wiki_site.py</code> 從 Wiki 的 Markdown 自動產生；'
            f'原始檔見 <a href="{REPO}">GitHub</a>。</footer></body></html>')

for key, src in pages.items():
    path = os.path.join(OUT, key + '.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(page_html(key, src))

# 檢查：所有產生的連結都要指到存在的檔案
bad = []
for d, _, fs in os.walk(OUT):
    for f in fs:
        p = os.path.join(d, f); s = open(p, encoding='utf-8').read()
        for href in re.findall(r'href="([^"#]+\.html)"', s):
            if href.startswith('http'): continue
            if not os.path.exists(os.path.normpath(os.path.join(d, href))): bad.append((os.path.relpath(p, OUT), href))
print(f'產生 {len(pages)} 頁 → {OUT}')
print('斷鏈：' + ('無' if not bad else '\n'.join(f'  {a} → {b}' for a, b in bad)))
