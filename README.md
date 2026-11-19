# 茶知識 LLM Wiki 與教學簡報

先用 [Karpathy 的 LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 做法建立「茶」的知識庫，再**只從知識庫**產生一份給新手看的教學 HTML 簡報。

## 連結

| 內容 | 網址 |
| --- | --- |
| 專案首頁 | https://yucihl.github.io/tea-llm-wiki/ |
| 教學簡報 | https://yucihl.github.io/tea-llm-wiki/output/slides/tea-intro.html |
| LLM Wiki（可點擊瀏覽） | https://yucihl.github.io/tea-llm-wiki/wiki-site/index.html |
| Wiki 原始 Markdown | [`wiki/`](wiki/)、目錄 [`index.md`](index.md) |
| 規則書 | [`AGENTS.md`](AGENTS.md) |
| 操作紀錄 | [`log.md`](log.md) |

> Wiki 頁面之間用 Obsidian 的 `[[頁面]]` 連結，GitHub 上無法直接點擊，所以另外產生了可瀏覽的 `wiki-site/`。也可以把整個資料夾用 Obsidian 開啟，點連結並看關係圖。

## 成果

- 原始資料 `raw/`：10 篇（茶改場 4、維基百科 2、品牌網站 4）
- Wiki `wiki/`：35 頁（來源摘要 10、概念 12、茶種 10、比較 2、名詞表 1）
- 教學簡報：5 個區塊共 31 頁，加上封面、目錄、總結、參考資料，共 35 張

## 流程

1. 取得資料，原文存入 `raw/`（只讀不改），先做 raw 完整性檢查
2. 先討論、後生成：列出 3–5 個重點與 1–2 個疑問，確認後才寫入 Wiki
3. 寫入後檢查，記錄到 `log.md`；每 3 篇做一次 Lint
4. 查詢 Wiki 寫大綱（`output/slides/outline-*.md`），大綱檢查
5. 由大綱產生 HTML，逐頁截圖檢查；修改一律先改大綱或 Wiki，再重新產生

## 目錄結構

```
├── AGENTS.md / CLAUDE.md   規則書
├── index.md                Wiki 目錄
├── log.md                  操作紀錄
├── raw/                    原始資料
├── wiki/                   Wiki 知識頁（Markdown）
├── wiki-site/              Wiki 的 HTML 版（自動產生）
├── output/slides/          簡報大綱與 tea-intro.html
└── tools/                  檢查與產生工具
```

## 工具

```bash
python3 tools/check_wiki.py .        # Wiki 寫入後檢查
python3 tools/check_outline.py .     # 大綱檢查
python3 tools/build_html.py .        # 由大綱產生簡報
python3 tools/check_html.py .        # 簡報逐頁截圖檢查（需要 Chrome 與 playwright）
python3 tools/build_wiki_site.py . https://github.com/yucihl/tea-llm-wiki   # 產生 wiki-site/
```

## 資料來源

各篇原始資料的網址與取得日期寫在 `raw/` 每個檔案開頭；簡報最後一頁也列出參考資料。地圖資料：Natural Earth（公眾領域）、內政部縣市界開放資料（透過 world-atlas、taiwan-atlas 套件）。
