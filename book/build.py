#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 content/*.md 构建成多页 HTML 电子书。"""
import os, re, shutil, html, json
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"

BOOK_TITLE = "智能体运行时原理"
BOOK_SUB = "从 LangChain 到 LangGraph，及可迁移的 Agent 设计法则"

PARTS = [
    ("第一部分　问题空间", "框架为什么必然出现", ["01", "02", "03", "04"]),
    ("第二部分　LangChain 的抽象原理", "组件、协议与编排", ["05", "06", "07", "08", "09"]),
    ("第三部分　LangGraph：从链到图", "状态、执行与持久化", ["10", "11", "12", "13", "14", "15"]),
    ("第四部分　依赖族与生态", "契约、协议与观测", ["16", "17", "18", "19"]),
    ("第五部分　原理迁移", "超越具体框架", ["20", "21", "22", "23"]),
    ("附录", "速查与自检", ["A", "B"]),
]

CSS = r"""
:root{
  --bg:#fbfaf7; --panel:#ffffff; --ink:#1f2328; --ink-2:#4a5260; --ink-3:#7c8796;
  --line:#e4e6ea; --line-2:#eef0f3; --accent:#3d5fd9; --accent-soft:#eef2ff;
  --accent-2:#b8722c; --accent-2-soft:#fdf6ec; --radius:10px;
  --mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:16px; line-height:1.85; letter-spacing:.01em;
}
a{color:var(--accent); text-decoration:none}
a:hover{text-decoration:underline}
.layout{display:flex; align-items:flex-start; max-width:1460px; margin:0 auto}

/* ---------- 侧栏 ---------- */
.side{
  width:296px; flex:0 0 296px; position:sticky; top:0; height:100vh; overflow-y:auto;
  border-right:1px solid var(--line); background:var(--panel); padding:26px 20px 60px;
}
.side-brand{display:block; margin-bottom:22px; color:var(--ink)}
.side-brand b{display:block; font-size:17px; letter-spacing:.02em}
.side-brand span{display:block; font-size:11.5px; color:var(--ink-3); line-height:1.6; margin-top:5px}
.side-part{margin:18px 0 6px; font-size:11px; font-weight:700; letter-spacing:.14em; color:var(--ink-3); text-transform:uppercase}
.side-part em{display:block; font-style:normal; font-weight:400; letter-spacing:0; text-transform:none; font-size:11px; color:#a3abb7; margin-top:2px}
.side a.item{
  display:block; padding:5px 10px; border-radius:6px; font-size:13.5px; color:var(--ink-2);
  line-height:1.5; margin-bottom:1px; border-left:2px solid transparent;
}
.side a.item:hover{background:var(--line-2); text-decoration:none; color:var(--ink)}
.side a.item.on{background:var(--accent-soft); color:var(--accent); font-weight:600; border-left-color:var(--accent)}
.side a.item i{font-style:normal; color:var(--ink-3); font-family:var(--mono); font-size:11.5px; margin-right:7px}
.side a.item.on i{color:var(--accent)}
.side-sub{padding:4px 0 8px 14px}
.side-sub a{display:block; font-size:12.5px; color:var(--ink-3); padding:3px 8px; border-radius:5px; line-height:1.5}
.side-sub a:hover{color:var(--accent); background:var(--line-2); text-decoration:none}
.side-foot{margin-top:26px; padding-top:16px; border-top:1px solid var(--line); font-size:11.5px; color:var(--ink-3); line-height:1.7}

/* ---------- 主体 ---------- */
.main{flex:1 1 auto; min-width:0; padding:44px 56px 120px; max-width:940px}
.crumb{font-size:12.5px; color:var(--ink-3); margin-bottom:20px; letter-spacing:.02em}
.crumb a{color:var(--ink-3)}
.crumb a:hover{color:var(--accent)}
article h1{
  font-size:30px; line-height:1.35; margin:0 0 10px; letter-spacing:-.01em; font-weight:750;
  padding-bottom:18px;
}
article>blockquote:first-of-type{
  margin:0 0 34px; padding:16px 20px; background:var(--accent-soft); border-left:3px solid var(--accent);
  border-radius:0 var(--radius) var(--radius) 0; color:#2b3d7a; font-size:15px; line-height:1.8;
}
article>blockquote:first-of-type p{margin:0}
article h2{
  font-size:22px; margin:52px 0 16px; padding-top:16px; border-top:1px solid var(--line);
  font-weight:700; letter-spacing:-.005em;
}
article h2:first-of-type{border-top:none; padding-top:0; margin-top:34px}
article h3{font-size:17.5px; margin:32px 0 10px; font-weight:650; color:#2c333d}
article h4{font-size:15.5px; margin:24px 0 8px; font-weight:650; color:var(--ink-2)}
article p{margin:0 0 17px}
article strong{font-weight:680; color:#12161c}
article em{font-style:normal; color:var(--accent-2); font-weight:600}
article ul,article ol{margin:0 0 18px; padding-left:24px}
article li{margin-bottom:7px}
article li::marker{color:var(--ink-3)}
article hr{border:none; border-top:1px solid var(--line); margin:40px 0}
article blockquote{
  margin:0 0 20px; padding:14px 20px; background:#f5f6f8; border-left:3px solid #ccd2dc;
  border-radius:0 8px 8px 0; color:var(--ink-2); font-size:15px;
}
article blockquote p:last-child{margin-bottom:0}
article a{text-decoration:underline; text-underline-offset:3px; text-decoration-color:#c3cde8}
article pre{
  background:#f7f8fa; border:1px solid var(--line); border-radius:var(--radius);
  padding:16px 18px; overflow-x:auto; font-family:var(--mono); font-size:13px;
  line-height:1.75; color:#333b47; margin:0 0 22px;
}
article code{font-family:var(--mono); font-size:.89em; background:#f0f2f5; padding:2px 5px; border-radius:4px; color:#3c4553}
article pre code{background:none; padding:0; font-size:13px; color:inherit}
article table{
  width:100%; border-collapse:separate; border-spacing:0; margin:0 0 24px; font-size:14.5px;
  border:1px solid var(--line); border-radius:var(--radius); overflow:hidden;
}
article thead th{background:#f4f6f9; text-align:left; padding:11px 14px; font-weight:680; font-size:13.5px; color:#333b47; border-bottom:1px solid var(--line)}
article tbody td{padding:11px 14px; border-bottom:1px solid var(--line-2); vertical-align:top; line-height:1.7}
article tbody tr:last-child td{border-bottom:none}
article tbody tr:nth-child(even){background:#fcfcfd}

/* ---------- 图示套件 ---------- */
.dg{margin:26px 0; padding:22px 20px; background:#f8f9fb; border:1px solid var(--line); border-radius:var(--radius); overflow-x:auto}
.dg-flow,.dg-seq{display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:center}
.dg-col{display:flex; flex-direction:column; align-items:center; gap:8px}
.dg-box{padding:10px 16px; background:#fff; border:1px solid #d6dae0; border-radius:8px; font-size:14px; color:var(--ink); line-height:1.5; white-space:nowrap; text-align:center}
.dg-box small{display:block; font-size:12px; color:var(--ink-3); font-weight:400; margin-top:2px; white-space:nowrap}
.dg-box.dg-hl small{color:#4b63b8}
.dg-box.dg-alt small{color:#a1742f}
.dg-hl{background:var(--accent-soft); border-color:#9db4f0; color:#1b3a8f; font-weight:650}
.dg-alt{background:var(--accent-2-soft); border-color:#e8c88a; color:#8a5b12}
.dg-arw{color:#9aa4b2; font-size:16px; white-space:nowrap}
.dg-arw-h{font-size:12.5px; color:#667085; white-space:nowrap}
.dg-stack{display:flex; flex-direction:column; gap:10px}
.dg-layer{padding:12px 16px; background:#fff; border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:8px; font-size:14.5px; line-height:1.6}
.dg-layer:nth-child(2){border-left-color:#7b93e8}
.dg-layer:nth-child(3){border-left-color:#a8b7ef}
.dg-layer:nth-child(4){border-left-color:#c9d3f5}
.dg-tag{display:inline-block; min-width:76px; color:var(--accent); font-weight:700; margin-right:10px; font-size:12.5px; letter-spacing:.02em}
.dg-vs{display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--line); border:1px solid var(--line); border-radius:var(--radius); overflow:hidden}
.dg-col-head{background:var(--accent-soft); padding:10px 14px; font-weight:700; font-size:14px; color:#1b3a8f; line-height:1.5}
.dg-alt-head{background:var(--accent-2-soft); color:#8a5b12}
.dg-cell{background:#fff; padding:10px 14px; font-size:14px; line-height:1.65}
.dg-cell.dg-alt{background:#fffdf8}
.dg-act{padding:8px 14px; border-radius:999px; background:#fff; border:1px solid #d6dae0; font-size:13.5px; line-height:1.4; white-space:nowrap}

/* ---------- 章节内导航 ---------- */
.tocbox{margin:0 0 30px; padding:14px 18px; background:#f8f9fb; border:1px solid var(--line); border-radius:var(--radius); font-size:13.5px}
.tocbox b{display:block; font-size:11.5px; letter-spacing:.14em; color:var(--ink-3); text-transform:uppercase; margin-bottom:8px}
.tocbox ul{margin:0; padding:0; list-style:none; columns:2; column-gap:26px}
.tocbox li{margin-bottom:5px; break-inside:avoid}
.tocbox a{color:var(--ink-2)}
.tocbox a:hover{color:var(--accent)}

/* ---------- 上下页 ---------- */
.pager{display:flex; gap:14px; margin-top:64px; padding-top:26px; border-top:1px solid var(--line)}
.pager a{
  flex:1; padding:14px 18px; background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
  font-size:13.5px; color:var(--ink-2); line-height:1.6;
}
.pager a:hover{border-color:#b9c4e4; text-decoration:none; background:#fcfdff}
.pager a span{display:block; font-size:11px; letter-spacing:.14em; color:var(--ink-3); text-transform:uppercase; margin-bottom:3px}
.pager a b{color:var(--ink); font-weight:650}
.pager a.next{text-align:right}

/* ---------- 封面 ---------- */
.cover{padding:0}
.cover .hero{padding:80px 0 40px; border-bottom:1px solid var(--line); margin-bottom:44px}
.cover .kicker{font-size:12px; letter-spacing:.2em; color:var(--accent); font-weight:700; text-transform:uppercase; margin-bottom:16px}
.cover h1{font-size:44px; line-height:1.25; margin:0 0 18px; letter-spacing:-.02em; font-weight:800}
.cover .sub{font-size:18px; color:var(--ink-2); line-height:1.7; max-width:620px}
.cover .meta{margin-top:30px; display:flex; gap:26px; flex-wrap:wrap; font-size:13px; color:var(--ink-3)}
.cover .meta b{display:block; color:var(--ink); font-size:20px; font-weight:700; margin-bottom:2px}
.readme{margin:0 0 44px; display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--line); border:1px solid var(--line); border-radius:var(--radius); overflow:hidden}
.readme>div{background:var(--panel); padding:20px 22px}
.readme h3{margin:0 0 10px; font-size:15px; font-weight:700}
.readme ul{margin:0; padding-left:18px; font-size:14px; color:var(--ink-2); line-height:1.75}
.readme li{margin-bottom:6px}
.partblock{margin-bottom:34px}
.partblock h2{font-size:19px; margin:0 0 4px; font-weight:700}
.partblock .pd{font-size:13px; color:var(--ink-3); margin-bottom:14px}
.chlist{display:grid; grid-template-columns:1fr 1fr; gap:10px}
.chlist a{
  display:block; padding:14px 16px; background:var(--panel); border:1px solid var(--line);
  border-radius:var(--radius); font-size:14.5px; color:var(--ink); line-height:1.6;
}
.chlist a:hover{border-color:#b9c4e4; background:#fcfdff; text-decoration:none}
.chlist a i{font-style:normal; font-family:var(--mono); font-size:11.5px; color:var(--accent); display:block; margin-bottom:3px}
.chlist a small{display:block; color:var(--ink-3); font-size:12.5px; margin-top:3px}

@media (max-width:1080px){
  .layout{display:block}
  .side{position:static; width:auto; flex:none; height:auto; border-right:none; border-bottom:1px solid var(--line); padding:20px 22px 24px}
  .main{padding:30px 22px 90px}
  .cover h1{font-size:32px}
  .readme,.chlist{grid-template-columns:1fr}
  .tocbox ul{columns:1}
  .dg-vs{grid-template-columns:1fr}
}
"""


def slug_num(num):
    return f"ch{num}" if num.isdigit() else f"ap{num.lower()}"


def read_chapters():
    chapters = []
    for f in sorted(CONTENT.glob("*.md")):
        m = re.match(r"^([0-9]{2}|[A-Za-z])[-_](.+)\.md$", f.name)
        if not m:
            continue
        raw_num, slug = m.group(1), m.group(2)
        num = raw_num if raw_num.isdigit() else raw_num.upper()
        text = f.read_text(encoding="utf-8")
        title = None
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if not title:
            raise ValueError(f"{f.name}：缺少一级标题（`# 标题`），无法生成目录。")
        chapters.append({"num": num, "slug": slug, "file": f, "title": title, "raw": text, "out": f"{slug_num(num)}-{slug}.html"})
    chapters.sort(key=lambda c: (0, int(c["num"])) if c["num"].isdigit() else (1, c["num"]))
    return chapters


def split_chapters(chapters):
    """把正文章与附录分开计数——封面/侧栏的'共 N 章'不应把附录算进去。"""
    body = [c for c in chapters if c["num"].isdigit()]
    appendix = [c for c in chapters if not c["num"].isdigit()]
    return body, appendix


def build_nav(chapters, current=None):
    by_num = {c["num"]: c for c in chapters}
    parts_html = []
    for pname, pdesc, nums in PARTS:
        items = []
        for n in nums:
            c = by_num.get(n)
            if not c:
                continue
            on = " on" if current and c["num"] == current["num"] else ""
            short = re.sub(r"^第\s*\d+\s*章\s*", "", c["title"])
            short = re.sub(r"^附录\s*[AB]?\s*", "", short).strip() or c["title"]
            label = f"附录 {c['num']}　{short}" if not c["num"].isdigit() else short
            items.append(f'<a class="item{on}" href="{c["out"]}"><i>{c["num"]}</i>{html.escape(label)}</a>')
        if items:
            parts_html.append(
                f'<div class="side-part">{html.escape(pname)}<em>{html.escape(pdesc)}</em></div>' + "".join(items)
            )
    return "".join(parts_html)


NAV_HEAD = f'<a class="side-brand" href="index.html"><b>{BOOK_TITLE}</b><span>{BOOK_SUB}</span></a>'


def page(title, body, chapters, current=None, extra_head=""):
    nav = build_nav(chapters, current)
    n_body, n_appendix = (len(x) for x in split_chapters(chapters))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
{extra_head}
</head>
<body>
<div class="layout">
  <aside class="side">{NAV_HEAD}{nav}
    <div class="side-foot">共 {n_body} 章 + {n_appendix} 个附录 · 原理优先<br>零真实代码，只用结构示意与图示</div>
  </aside>
  <main class="main">
{body}
  </main>
</div>
</body>
</html>
"""


def main():
    chapters = read_chapters()
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "assets").mkdir(parents=True, exist_ok=True)
    # 拷贝任务过程中可能在 assets 里的东西
    if ASSETS.exists():
        for f in ASSETS.iterdir():
            if f.is_file():
                shutil.copy2(f, DIST / "assets" / f.name)

    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "md_in_html", "attr_list", "toc"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}},
    )

    for i, c in enumerate(chapters):
        md.reset()
        body_html = md.convert(c["raw"])
        # 移除正文首个 h1
        body_html = re.sub(r"<h1[^>]*>.*?</h1>", "", body_html, count=1, flags=re.S)
        try:
            toc_html = md.toc
        except Exception:
            toc_html = ""
        if toc_html:
            toc_html = toc_html.replace('<div class="toc">', '<div class="tocbox"><b>本章小节</b>')
        prev_c = chapters[i - 1] if i > 0 else None
        next_c = chapters[i + 1] if i + 1 < len(chapters) else None
        pager = '<div class="pager">'
        if prev_c:
            pager += f'<a class="prev" href="{prev_c["out"]}"><span>上一章</span><b>{html.escape(prev_c["title"])}</b></a>'
        else:
            pager += f'<a class="prev" href="index.html"><span>目录</span><b>返回全书目录</b></a>'
        if next_c:
            pager += f'<a class="next" href="{next_c["out"]}"><span>下一章</span><b>{html.escape(next_c["title"])}</b></a>'
        pager += "</div>"
        crumb = f'<div class="crumb"><a href="index.html">目录</a> ／ 第 {"附录 " if not c["num"].isdigit() else ""}{c["num"]} {"章" if c["num"].isdigit() else ""}</div>'
        body = f'<article>\n<h1>{html.escape(c["title"])}</h1>\n{toc_html}\n{body_html}\n{pager}\n</article>'
        (DIST / c["out"]).write_text(page(c["title"], body, chapters, c), encoding="utf-8")

    # ---------- 封面 / 目录 ----------
    by_num = {c["num"]: c for c in chapters}
    blocks = []
    for pname, pdesc, nums in PARTS:
        cards = []
        for n in nums:
            c = by_num.get(n)
            if not c:
                continue
            short = re.sub(r"^第\s*\d+\s*章\s*", "", c["title"])
            label = f"附录 {c['num']}" if not c["num"].isdigit() else f"第 {c['num']} 章"
            cards.append(f'<a href="{c["out"]}"><i>{label}</i>{html.escape(short)}</a>')
        if cards:
            blocks.append(
                f'<div class="partblock"><h2>{html.escape(pname)}</h2><div class="pd">{html.escape(pdesc)}</div>'
                f'<div class="chlist">{"".join(cards)}</div></div>'
            )

    words = sum(len(re.findall(r"[\u4e00-\u9fff]", c["raw"])) for c in chapters)
    n_body, n_appendix = (len(x) for x in split_chapters(chapters))
    cover = f"""<article class="cover">
<div class="hero">
  <div class="kicker">Agent Runtime Principles</div>
  <h1>{BOOK_TITLE}</h1>
  <div class="sub">{BOOK_SUB}</div>
  <div class="meta">
    <div><b>{n_body}</b>章 + {n_appendix} 个附录</div>
    <div><b>{words // 10000} 万+</b>字</div>
    <div><b>0 行</b>可直接运行的代码</div>
    <div><b>5 部分</b>认知阶梯</div>
  </div>
</div>
<div class="readme">
  <div><h3>这本书在讲什么</h3><ul>
    <li>LangChain / LangGraph 只是某一时刻的一组实现</li>
    <li>真正的资产是它们背后的运行时原理</li>
    <li>每一章都回答：为什么必须这样，不这样会怎样</li>
    <li>结尾都会落到「离开这套框架，你自己怎么造」</li>
  </ul></div>
  <div><h3>怎么读</h3><ul>
    <li>被某个行为搞懵了 → 查<b>附录 B</b> 的故障排查表</li>
    <li>在选型 → 直接读<b>第 22 章</b></li>
    <li>第一次系统学 → 按顺序读第一部分</li>
    <li>术语不确定 → 查<b>附录 A</b></li>
  </ul></div>
</div>
{"".join(blocks)}
</article>"""
    (DIST / "index.html").write_text(page(BOOK_TITLE, cover, chapters), encoding="utf-8")

    print(f"OK  chapters={len(chapters)}  chinese_chars={words}")


if __name__ == "__main__":
    main()
