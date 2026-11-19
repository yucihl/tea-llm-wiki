"""HTML 檢查（AGENTS.md 4.4）：實際開啟簡報，逐頁截圖並檢查版面。
用法：python3 tools/check_html.py <wiki根目錄> [截圖輸出資料夾]
"""
import os, re, sys, asyncio
from playwright.async_api import async_playwright

R = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/slide-shots'
HTML = os.path.join(R, 'output', 'slides', 'tea-intro.html')
os.makedirs(OUT, exist_ok=True)

PROBE = r"""
() => {
  const s = document.querySelector('.slide.active');
  const sr = s.getBoundingClientRect();
  const body = s.querySelector('.body');
  const foot = s.querySelector('footer');
  const out = {id: s.dataset.id || s.className, issues: []};
  // 1. 內容區是否被撐爆
  if (body && body.scrollHeight > body.clientHeight + 2)
    out.issues.push(`內容高度溢出 ${body.scrollHeight - body.clientHeight}px`);
  const ft = foot ? foot.getBoundingClientRect().top : sr.bottom;
  s.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    // SVG 會裁切超出畫框的內容：只檢查 <svg> 本身的外框，不量裡面的路徑與文字
    if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') {
      if (el.tagName.toLowerCase() === 'text') {   // 圖中文字仍要檢查字級（依實際縮放後的大小）
        const sv = el.closest('svg'), vb = sv.viewBox.baseVal;
        const k = vb && vb.width ? sv.getBoundingClientRect().width / vb.width : 1;
        const fs = parseFloat(getComputedStyle(el).fontSize) * k;
        if (fs < 17.5) out.issues.push(`圖中文字太小 ${fs.toFixed(1)}px：${el.textContent.trim().slice(0,10)}`);
      }
      return;
    }
    // 2. 超出投影片邊界
    if (r.right > sr.right + 1 || r.bottom > sr.bottom + 1 || r.left < sr.left - 1)
      out.issues.push(`超出邊界：<${el.tagName.toLowerCase()} class="${el.className}">`);
    // 3. 內容壓到頁尾
    if (body && body.contains(el) && r.bottom > ft + 1)
      out.issues.push(`壓到頁尾：<${el.tagName.toLowerCase()}> ${(el.textContent||'').trim().slice(0,16)}`);
    // 4. 單一元素內文字被截斷（水平溢出）
    if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflow !== 'visible')
      out.issues.push(`水平截斷：<${el.tagName.toLowerCase()}>`);
    // 4b. 被有 overflow:hidden 的父層裁切（2026-11-18 視覺檢查發現 B4 表格被截斷，程式原本漏抓）
    if (body && body.contains(el) && el.children.length === 0 && (el.textContent||'').trim()) {
      let p = el.parentElement;
      while (p && p !== s) {
        const ov = getComputedStyle(p).overflow;
        if (ov !== 'visible') {
          const pr = p.getBoundingClientRect();
          if (r.right > pr.right + 1 || r.bottom > pr.bottom + 1)
            out.issues.push(`被父層裁切：${(el.textContent||'').trim().slice(0,16)}`);
          break;
        }
        p = p.parentElement;
      }
      // 單行不換行的格子：文字實際寬度超過格子
      if (getComputedStyle(el).whiteSpace === 'nowrap' && el.scrollWidth > el.clientWidth + 1)
        out.issues.push(`文字超出格子：${(el.textContent||'').trim().slice(0,16)}`);
    }
    // 4c. 並排的區塊互相重疊（B4 的實際原因：左表過寬，被右表蓋住）
    const d = getComputedStyle(el).display;
    if (body && body.contains(el) && (d === 'grid' || d === 'flex')) {
      const kids = [...el.children].map(k => k.getBoundingClientRect()).filter(k => k.width && k.height);
      for (let a = 0; a < kids.length; a++) for (let b2 = a + 1; b2 < kids.length; b2++) {
        const A = kids[a], B = kids[b2];
        const ox = Math.min(A.right, B.right) - Math.max(A.left, B.left);
        const oy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
        if (ox > 2 && oy > 2) out.issues.push(`區塊重疊：<${el.tagName.toLowerCase()} class="${el.className}"> 第 ${a+1} 與 ${b2+1} 個子元素`);
      }
    }
    // 5. 內文字級（第 8.3 節：不小於 20px；註解與說明允許 18px）
    if (body && body.contains(el) && el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
      const fs = parseFloat(getComputedStyle(el).fontSize);
      const small = el.closest('.caveat, .axis');
      if (fs < (small ? 18 : 20) - 0.1) out.issues.push(`字太小 ${fs}px：${el.textContent.trim().slice(0,12)}`);
    }
  });
  out.issues = [...new Set(out.issues)];
  return out;
}
"""

async def main():
    css = open(os.path.join(R, 'tools', 'slides.css'), encoding='utf-8').read()
    root_end = css.index('}') + 1
    stray = re.findall(r'#[0-9A-Fa-f]{3,8}\b', css[root_end:])
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 1280, 'height': 776})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.goto('file://' + os.path.abspath(HTML))
        await pg.wait_for_timeout(800)
        n = await pg.evaluate('document.querySelectorAll(".slide").length')
        report = []
        for i in range(n):
            await pg.evaluate(f'window.__show({i})')
            await pg.wait_for_timeout(330)
            res = await pg.evaluate(PROBE)
            await pg.locator('.stage').screenshot(path=os.path.join(OUT, f'{i+1:02d}.png'))
            report.append((i + 1, res['id'], res['issues']))
        # 鍵盤換頁是否正常
        await pg.evaluate('window.__show(0)'); await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(100)
        kb = await pg.evaluate('location.hash')
        await b.close()
    bad = [r for r in report if r[2]]
    print(f'HTML 檢查：{n} 張投影片')
    print(f'  JavaScript 錯誤：{errors or "無"}')
    print(f'  鍵盤換頁：{"正常" if kb == "#slide-2" else "異常 " + kb}')
    print(f'  :root 以外的寫死色碼：{stray or "無"}')
    print(f'  版面問題：{len(bad)} 張' if bad else '  版面問題：無')
    for i, sid, iss in bad:
        print(f'    第 {i} 張（{sid}）：' + '；'.join(iss[:5]))
    print(f'  截圖：{OUT}')
    sys.exit(1 if (bad or errors or stray) else 0)

asyncio.run(main())
