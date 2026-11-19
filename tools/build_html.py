"""由大綱產生 HTML 簡報（AGENTS.md 4.3：簡報內容只來自大綱，大綱只來自 Wiki）。
用法：python3 tools/build_html.py <wiki根目錄>  → output/slides/tea-intro.html
"""
import os, re, sys, html, yaml
sys.path.insert(0, os.path.dirname(__file__))
from outline_lib import load

R = sys.argv[1]
W = os.path.join(R, 'wiki'); RAW = os.path.join(R, 'raw')
meta, blocks, closing = load(os.path.join(R, 'output', 'slides'))
BLOCK_NAMES = {b: n for b, n in meta['blocks']}
e = lambda t: html.escape(t or '')

# ---------- 來源：wiki 頁 → raw 檔 → 顯示名稱 ----------
def frontmatter(path):
    s = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n', s, re.S)
    return yaml.safe_load(m.group(1)) if m else {}
RAWMETA = {f[:-3]: frontmatter(os.path.join(RAW, f)) for f in os.listdir(RAW) if f.endswith('.md')}
def short_name(raw_id):
    m = RAWMETA[raw_id]; t = m['title']; site = m.get('site', '')
    if '維基' in site: return '維基百科「' + t.split(' - ')[0] + '」'
    if '茶改場' in site:
        if 'specialty' in raw_id: return '茶改場〈臺灣特色茶〉'
        return '茶改場〈' + t + '〉'
    if 'BESTEA' in site: return 'BESTEA〈' + re.split(r'[：｜]', t)[0] + '〉'
    return re.sub(r'\.(tw|com)$', '', site) + '〈' + re.split(r'[：？｜]', t)[0] + '〉'
def sources_for(slide):
    ids = []
    for p in slide['wiki']:
        if p == 'glossary': continue   # 名詞表只統一用詞，不算內容來源
        fm = frontmatter(os.path.join(W, p + '.md'))
        for s in fm.get('sources') or []:
            if s not in ids: ids.append(s)
    return [short_name(i) for i in ids]
USED = []

# ---------- 各版型 ----------
def ul(items, cls='pts'):
    return f'<ul class="{cls}">' + ''.join(f'<li>{e(i)}</li>' for i in items) + '</ul>'
def lead(s): return f'<p class="lead">{e(s["lead"])}</p>' if s.get('lead') else ''
def note(s):
    if not s.get('note'): return ''
    parts = s['note'].split('｜')
    return '<p class="note">' + e(parts[0]) + (f'<span class="caveat">{e(parts[1])}</span>' if len(parts) > 1 else '') + '</p>'
def callout(s):
    if not s.get('callout'): return ''
    h, b = (s['callout'] + [''])[:2]
    return f'<aside class="callout"><strong>{e(h)}</strong><span>{e(b)}</span></aside>'

def r_cards(s):
    n = len(s['cards'])
    cards = ''.join(
        f'<div class="card"><h3>{e(c[0])}</h3><p>{e(c[1])}</p>' + (f'<p class="tag">{e(c[2])}</p>' if len(c) > 2 and c[2] else '') + '</div>'
        for c in s['cards'])
    return lead(s) + f'<div class="cards n{n}">{cards}</div>' + callout(s) + note(s)
def r_compare(s):
    col = lambda side: f'<div class="col"><h3>{e(s[side]["head"])}</h3>{ul(s[side]["items"])}</div>'
    return lead(s) + f'<div class="compare">{col("left")}{col("right")}</div>' + callout(s) + note(s)
def r_table(s):
    rows = s['table']; head, body = rows[0], rows[1:]
    def one(rs, dense=False):
        th = ''.join(f'<th>{e(c)}</th>' for c in head)
        tb = ''.join('<tr>' + ''.join((f'<th scope="row">{e(c)}</th>' if i == 0 else f'<td>{e(c)}</td>') for i, c in enumerate(r)) + '</tr>' for r in rs)
        return f'<table class="tbl{" dense" if dense else ""}"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>'
    short = max(len(c) for r in body for c in r) <= 14
    if len(body) > 5 and len(head) == 2 and short:   # 長而短字的兩欄表：左右並排
        k = (len(body) + 1) // 2
        t = f'<div class="tbl-split">{one(body[:k])}{one(body[k:])}</div>'
    else:
        t = one(body, len(body) > 5)
    if s.get('callout'):                            # 表格＋右側提示框
        t = f'<div class="tbl-aside">{t}{callout(s)}</div>'
    return lead(s) + t + note(s)
def r_steps(s):
    st = ''.join(f'<li><span class="num">{i+1}</span><h3>{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(s['steps']))
    return lead(s) + f'<ol class="steps n{len(s["steps"])}">{st}</ol>' + note(s)
def r_statement(s):
    return f'<p class="big">{e(s["big"])}</p>' + ul(s.get('bullets', []), 'pts wide') + note(s)
SWATCH = {'green': 'var(--green-300)', 'white': 'var(--white)', 'yellow': 'var(--yellow)',
          'oolong': 'var(--green-100)', 'red': 'var(--tan-200)', 'dark': 'var(--tan-700)'}
def r_spectrum(s):
    items = ''.join(
        f'<li><span class="cup" style="--liquor:{SWATCH[c[3]]}"></span><h3>{e(c[0])}</h3><p class="ox">{e(c[1])}</p><p class="eg">{e(c[2])}</p></li>'
        for c in s['items'])
    return lead(s) + f'<div class="spectrum-wrap"><div class="axis"><span>不氧化</span><span>完全氧化</span><span class="post">後發酵</span></div><ol class="spectrum">{items}</ol></div>' + note(s)
def r_profile(s):
    facts = ''.join(f'<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>' for a, b in s['facts'])
    st = s['story']
    return lead(s) + f'<div class="profile"><dl class="facts">{facts}</dl><div class="story"><h3>{e(st["head"])}</h3>{ul(st["items"])}</div></div>' + note(s)
def r_timeline(s):
    it = ''.join(f'<li><span class="when">{e(a)}</span><p>{e(b)}</p></li>' for a, b in s['items'])
    return lead(s) + f'<ol class="timeline">{it}</ol>' + note(s)
def r_regions(s):
    it = ''.join(f'<div class="region r{i}"><h3>{e(a)}</h3><p>{e(b)}</p></div>' for i, (a, b) in enumerate(s['regions']))
    return lead(s) + f'<div class="regions">{it}</div>' + note(s)
def r_checklist(s):
    it = ''.join(f'<li><h3>{e(a)}</h3><p>{e(b)}</p></li>' for a, b in s['items'])
    return lead(s) + f'<ul class="checklist">{it}</ul>' + note(s)

# ---------- 圖像版型：地圖與風味輪 ----------
import json, math
MAPS = json.load(open(os.path.join(os.path.dirname(__file__), 'maps', 'maps.json'), encoding='utf-8'))
ZH_EN = {'中國': 'China', '日本': 'Japan', '韓國': ['South Korea', 'North Korea'], '葡萄牙': 'Portugal',
         '俄羅斯': 'Russia', '土耳其': 'Turkey', '伊朗': 'Iran', '印度': 'India', '荷蘭': 'Netherlands',
         '英國': 'United Kingdom', '法國': 'France', '西班牙': 'Spain', '德國': 'Germany'}
GROUP_FILL = {'cha': 'var(--yellow)', 'chai': 'var(--tan-200)', 'tea': 'var(--green-300)'}
def en(zh):
    v = ZH_EN[zh]; return v if isinstance(v, list) else [v]

def r_worldmap(s):
    w = MAPS['world']; W, H = w['viewBox']
    fill = {}
    for g in s['groups']:
        for c in g[2].split('、'): 
            for n in en(c): fill[n] = GROUP_FILL[g[0]]
    for n in en(s['origin']): fill[n] = 'var(--green-700)'
    paths = ''.join(f'<path d="{c["d"]}" fill="{fill.get(c["name"], "var(--white)")}"/>' for c in w['countries'])
    ox, oy = w['points'][s['origin']]
    routes = (f'<path class="route land" d="{w["routes"]["land"]}"/>'
              f'<path class="route sea" d="{w["routes"]["sea"]}"/>')
    lx, ly = w['points']['伊朗']; sx, sy = MAPS['world']['points']['印度']
    labels = (f'<text class="maplabel strong" x="{ox}" y="{oy+6}" text-anchor="middle">{e(s["origin"])}</text>'
              f'<text class="maplabel" x="{lx+38}" y="{ly-44}">陸路</text>'
              f'<text class="maplabel" x="{sx-36}" y="{sy+92}">海路</text>')
    svg = (f'<svg class="fig world" viewBox="0 0 {W} {H}" role="img" aria-label="茶的三種讀音分布地圖">'
           f'<rect width="{W}" height="{H}" rx="14" fill="var(--green-50)"/>'
           f'<g class="land">{paths}</g>{routes}{labels}</svg>')
    legend = ''.join(
        f'<div class="lg"><span class="sw" style="background:{GROUP_FILL[g[0]]}"></span>'
        f'<div><h3>{e(g[0])}</h3><p>{e(g[1])}</p><p class="eg">{e(g[3])}</p></div></div>' for g in s['groups'])
    legend += f'<div class="lg origin"><span class="sw" style="background:var(--green-700)"></span><div><p>{e(s["origin"])}：茶的起點</p></div></div>'
    return lead(s) + f'<div class="mapwrap">{svg}<div class="legend">{legend}</div></div>' + note(s)

WHEEL_FILL = {'green': 'var(--green-300)', 'mint': 'var(--green-100)', 'honey': 'var(--yellow)',
              'roast': 'var(--tan-200)', 'amber': 'var(--tan-700)', 'dark': 'var(--text)'}
DARK_FILLS = {'amber', 'dark'}
def r_wheel(s):
    items = s['items']; n = len(items); C = 220; R1, R0 = 196, 92
    def pt(r, a): return (round(C + r * math.sin(a), 1), round(C - r * math.cos(a), 1))
    segs = ''
    for i, it in enumerate(items):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p1, p2, p3, p4 = pt(R1, a0), pt(R1, a1), pt(R0, a1), pt(R0, a0)
        d = f'M{p1[0]},{p1[1]} A{R1},{R1} 0 0 1 {p2[0]},{p2[1]} L{p3[0]},{p3[1]} A{R0},{R0} 0 0 0 {p4[0]},{p4[1]} Z'
        tx, ty = pt((R1 + R0) / 2, (a0 + a1) / 2)
        cls = ' light' if it[5] in DARK_FILLS else ''
        segs += (f'<path d="{d}" fill="{WHEEL_FILL[it[5]]}" stroke="var(--cream)" stroke-width="4"/>'
                 f'<text class="seg{cls}" x="{tx}" y="{ty+8}" text-anchor="middle">{e(it[1])}</text>')
    # 外圈箭頭：順時針＝氧化由輕到重
    a0, a1 = 0.12, 2 * math.pi - 0.35
    q0, q1 = pt(212, a0), pt(212, a1)
    arc = f'<path class="dir" d="M{q0[0]},{q0[1]} A212,212 0 1 1 {q1[0]},{q1[1]}" marker-end="url(#ah)"/>'
    defs = '<defs><marker id="ah" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--tan-700)"/></marker></defs>'
    center = f'<text class="ctr" x="{C}" y="{C+10}" text-anchor="middle">{e(s["center"])}</text>'
    svg = f'<svg class="fig wheel" viewBox="0 0 440 440" role="img" aria-label="臺茶風味輪六大類示意圖">{defs}{arc}{segs}{center}</svg>'
    def card(i):
        it = items[i]
        return (f'<div class="wc"><span class="sw" style="background:{WHEEL_FILL[it[5]]}"></span>'
                f'<div><h3>{e(it[0])}</h3><p>{e(it[2])}｜{e(it[3])}</p><p class="fl">風味：{e(it[4])}</p></div></div>')
    right = ''.join(card(i) for i in range(0, n // 2))
    left = ''.join(card(i) for i in range(n - 1, n // 2 - 1, -1))
    return lead(s) + f'<div class="wheelwrap"><div class="wcol">{left}</div>{svg}<div class="wcol">{right}</div></div>' + note(s)

REGION_FILL = {'北部': 'var(--green-100)', '中部': 'var(--green-300)', '南部': 'var(--yellow)', '東部': 'var(--tan-200)'}
def r_twmap(s):
    t = MAPS['taiwan']; W, H = t['viewBox']; M = 185
    fill = {}
    norm = lambda n: n.replace('臺', '台')        # 地圖資料用「台」，Wiki 用「臺」
    for rg in s['regions']:
        for c in rg[1].split('、'): fill[norm(c)] = REGION_FILL[rg[0]]
    missing = [c for rg in s['regions'] for c in rg[1].split('、') if norm(c) not in {x['name'] for x in t['counties']}]
    if missing: raise SystemExit(f'D3 地圖找不到縣市：{missing}')
    paths = ''.join(f'<path d="{c["d"]}" fill="{fill.get(c["name"], "var(--white)")}"/>' for c in t['counties'])
    # 標籤自動排版：依經度分左右兩欄，依緯度排序，避免重疊
    pins = [(name, place, *t['points'][place]) for name, place in s['pins']]
    LEFT = {'三峽', '北埔', '名間', '鹿谷', '阿里山', '魚池'}   # 標籤放左側的地點，避免引線交叉
    out = ''
    for side in ('L', 'R'):
        grp = sorted([p for p in pins if (p[1] in LEFT) == (side == 'L')], key=lambda p: p[3])
        lasty = -1e9
        for name, place, x, y in grp:
            ly = max(y, lasty + 36); lasty = ly
            lx = -18 if side == 'L' else W + 18
            anchor = 'end' if side == 'L' else 'start'
            out += (f'<polyline class="lead-line" points="{x},{y} {lx + (8 if side=="L" else -8)},{ly} {lx},{ly}"/>'
                    f'<circle class="pin" cx="{x}" cy="{y}" r="5.5"/>'
                    f'<text class="maplabel" x="{lx + (-4 if side=="L" else 4)}" y="{ly+7}" text-anchor="{anchor}">{e(name)}</text>')
    svg = (f'<svg class="fig tw" viewBox="{-M} 0 {W + 2*M} {H}" role="img" aria-label="台灣茶產區地圖">'
           f'<g class="land">{paths}</g>{out}</svg>')
    legend = ''.join(
        f'<div class="lg"><span class="sw" style="background:{REGION_FILL[rg[0]]}"></span><div><h3>{e(rg[0])}</h3><p>{e(rg[2])}</p></div></div>'
        for rg in s['regions'])
    return lead(s) + f'<div class="mapwrap tw">{svg}<div class="legend">{legend}</div></div>' + note(s)

RENDER = dict(cards=r_cards, compare=r_compare, table=r_table, steps=r_steps, statement=r_statement,
              spectrum=r_spectrum, profile=r_profile, timeline=r_timeline, regions=r_regions, checklist=r_checklist,
              worldmap=r_worldmap, wheel=r_wheel, twmap=r_twmap)

# ---------- 組頁 ----------
slides = []
LEAF = '''<svg class="leaf" viewBox="0 0 400 400" aria-hidden="true"><path d="M60 340 C 60 180, 170 60, 340 60 C 340 230, 230 340, 60 340 Z" fill="var(--green-100)" stroke="var(--green-300)" stroke-width="3"/><path d="M60 340 C 140 260, 230 170, 330 70" fill="none" stroke="var(--green-300)" stroke-width="3"/><path d="M120 280 C 120 240, 130 210, 150 190 M170 232 C 175 190, 190 160, 215 140 M220 180 C 230 145, 250 120, 270 105 M150 252 C 190 252, 220 245, 245 230 M200 205 C 240 205, 265 195, 285 180" fill="none" stroke="var(--green-300)" stroke-width="2" stroke-linecap="round"/></svg>'''
slides.append(('cover', f'''<section class="slide cover" data-block="">{LEAF}<div class="cover-text"><h1>{e(meta["title"])}</h1><p class="sub">{e(meta["subtitle"])}</p><p class="hint">用 ← → 鍵或下方按鈕換頁</p></div></section>'''))
toc = ''.join(f'<li><span class="b">{b}</span><span class="n">{e(n)}</span><span class="c">{len(blocks[b])} 頁</span></li>' for b, n in meta['blocks'])
slides.append(('toc', f'<section class="slide toc" data-block=""><header><h2>這堂課會走過五站</h2></header><ol class="toc-list">{toc}</ol><p class="note">從「茶是什麼」開始，走到台灣的特色茶，最後學會泡一杯。</p></section>'))
for b, sl in list(blocks.items()) + [('Z', closing)]:
    for s in sl:
        src = sources_for(s); USED.extend(x for x in src if x not in USED)
        chip = f'<span class="chip">{b}　{e(BLOCK_NAMES[b])}</span>' if b != 'Z' else '<span class="chip">總結</span>'
        body = RENDER[s['layout']](s)
        slides.append((s['id'], f'''<section class="slide l-{s["layout"]}" data-block="{b}" data-id="{s["id"]}"><header>{chip}<h2>{e(s["title"])}</h2></header><div class="body">{body}</div><footer><span class="src">資料來源：{e("、".join(src))}</span><span class="pg"></span></footer></section>'''))
# 參考資料頁
refs = []
for rid, m in sorted(RAWMETA.items()):
    if short_name(rid) in USED:
        refs.append(f'<li><span class="rt">{e(short_name(rid))}</span><a href="{e(m["url"])}">{e(m["url"])}</a></li>')
slides.append(('refs', f'<section class="slide refs" data-block=""><header><h2>參考資料</h2></header><ol class="ref-list">{"".join(refs)}</ol><p class="note">本簡報內容皆整理自上列資料建立的茶知識 Wiki；取用日期 2026-11-18。</p></section>'))

CSS = open(os.path.join(os.path.dirname(__file__), 'slides.css'), encoding='utf-8').read()
JS = open(os.path.join(os.path.dirname(__file__), 'slides.js'), encoding='utf-8').read()
doc = f'''<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>一片葉子的旅程：茶的入門課</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<main class="deck" aria-live="polite">
<div class="stage">
{"".join(s for _, s in slides)}
</div>
</main>
<nav class="controls" aria-label="換頁">
<button type="button" class="prev" aria-label="上一頁">‹</button>
<span class="count"></span>
<button type="button" class="next" aria-label="下一頁">›</button>
</nav>
<div class="progress"><span></span></div>
<script>{JS}</script>
</body>
</html>'''
out = os.path.join(R, 'output', 'slides', 'tea-intro.html')
open(out, 'w', encoding='utf-8').write(doc)
print(f'產生 {len(slides)} 張投影片 → {out}')
