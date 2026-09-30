#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""书稿规范自动校验 —— 把 SPEC/style-guide.md 的强制项变成可执行检查。

用法：
    python check.py          # 检查，退出码 0=通过 / 1=有 ERROR

设计意图：书稿规范里有多条"每章必须…"的硬性要求（字数、表格、图示、固定结构、
零真实代码）。靠人眼审阅一定会漏——缺表格、少收尾小节、声明条数与实际不符、
跨章口径打架，都是同一类问题。把这些规则写成脚本，改完内容跑一次即可。

换项目时只改下面的 CONFIG，其余逻辑不用动。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"


# ============================ 按项目修改这里 ============================
CONFIG = {
    # ---------- 篇幅 ----------
    "min_chars": 3500,            # 正文章节汉字下限
    "max_chars_warn": 5200,       # 超过则提醒（规范上限 5000）
    "appendix_min_chars": 1500,   # 附录是工具页，只做下限保护

    # ---------- 固定结构 ----------
    "required_sections": ["引子", "常见误区与排查", "本章要点", "迁移视角：如果不用这个框架"],
    # 已登记的结构变体：章号 → 允许缺失的小节（缺失不报错；出现多余项会提醒）
    "structure_variants": {
        "23": {"allow_missing": ["迁移视角：如果不用这个框架"]},
    },
    "appendix_skips_structure": True,    # 附录不适用"每章固定结构"
    "appendix_requires_diagram": False,  # 附录可能天然不需要配图（如纯术语表）
    "require_table": True,               # 每章至少 1 个 Markdown 表格
    "require_diagram": True,             # 每章至少 1 个图示块

    # ---------- 图示套件白名单（与 style-guide 三 保持一致）----------
    "allowed_dg_classes": [
        "dg", "dg-flow", "dg-seq", "dg-col", "dg-box", "dg-hl", "dg-alt",
        "dg-arw", "dg-arw-h", "dg-stack", "dg-layer", "dg-tag",
        "dg-vs", "dg-col-head", "dg-alt-head", "dg-cell", "dg-act",
    ],

    # ---------- 零真实代码 ----------
    # 只匹配"能直接跑"的痕迹。概念签名如 `invoke(input: I) -> O` 是允许的，
    # 所以只匹配带点的方法调用，不匹配裸函数名。
    "code_smells": [
        (r"\bimport\s+[\w.]+", "出现 import 语句"),
        (r"\bfrom\s+[\w.]+\s+import\b", "出现 from ... import"),
        (r"^\s*def\s+\w+\s*\(", "出现函数定义"),
        (r"^\s*class\s+\w+\s*[:(]", "出现类定义"),
        (r"\.invoke\s*\(", "出现 .invoke() 调用"),
        (r"\.stream\s*\(", "出现 .stream() 调用"),
        (r"\.batch\s*\(", "出现 .batch() 调用"),
        (r"\bpip install\b", "出现 pip install"),
        (r"^\s*\w+\s*=\s*\w+\(.*\)\s*$", "出现赋值式实例化"),
    ],
    "allowed_code_langs": ("", "text"),   # 代码块语言标记白名单

    # ---------- 跨章口径一致性 ----------
    # 新增任何跨章节的统一说法（数字、命名、定义）都在这里登记一条。
    "bad_phrases": [
        (r"五[个条]\s*约束", "与'四个约束'的口径冲突"),
        # 后面紧跟"信号/要素/模式"等名词时是合法用法（如"这五条信号"），不算冲突
        (r"这五条(?![^，。；\n]{0,8}(信号|动机|要素|模式|压缩|变量|归约|埋点|策略|类|项|步))",
         "把成本误列为独立的第五约束，与第 2 章的四约束口径冲突"),
    ],

    # ---------- 小节声明条数 vs 实际条目数（可选）----------
    "count_checks": [
        {
            "file": "B-checklist.md",
            "header_pattern": r"^###\s+(.+?)（(\d+)\s*条）\s*$",
            "item_pattern": r"^\d+\.\s",
            "declared_total": 30,   # 各小节声明条数之和应等于它
        },
    ],

    "appendix_ids": ["A", "B"],   # 必须存在的附录
}
# ======================================================================


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []
        self.rows = []

    def err(self, where, msg):
        self.errors.append(f"[ERROR] {where}：{msg}")

    def warn(self, where, msg):
        self.warns.append(f"[WARN ] {where}：{msg}")


def cn_chars(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def has_table(text):
    """Markdown 表格：表头下一行是 |---| 形式的分隔行。"""
    return bool(re.search(r"^\|.*\|[ \t]*\n\|[\s:|-]+\|[ \t]*$", text, flags=re.M))


def has_diagram(text):
    return '<div class="dg">' in text


def sections(text):
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.M)]


def check_file(path, rep):
    text = path.read_text(encoding="utf-8")
    name = path.name
    num = name.split("-")[0]
    is_appendix = not num.isdigit()
    n = cn_chars(text)
    rep.rows.append((num, n, name))

    # 1. 首行一级标题格式
    if not re.match(r"^#\s+(第\s*\d+\s*章|附录\s*[A-Z])\s*[\u3000\s]\s*\S", text.splitlines()[0].strip()):
        rep.err(name, "首行必须是一级标题，格式为 `# 第 N 章　标题` 或 `# 附录 A　标题`")

    # 2. 章首主旨 blockquote
    if not re.search(r"^>\s*\S", text, flags=re.M):
        rep.err(name, "缺少章首 blockquote 主旨句")

    # 3. 篇幅
    floor = CONFIG["appendix_min_chars"] if is_appendix else CONFIG["min_chars"]
    if n < floor:
        rep.err(name, f"汉字数 {n} 低于下限 {floor}，需扩写")
    elif not is_appendix and n > CONFIG["max_chars_warn"]:
        rep.warn(name, f"汉字数 {n} 超出规范上限，考虑拆分或压缩")

    # 4. 表格 + 图示（两项独立强制，图示不能替代表格）
    if CONFIG["require_table"] and not has_table(text):
        rep.err(name, "缺少 Markdown 表格（图示不能替代表格要求）")
    if CONFIG["require_diagram"] and not is_appendix and not has_diagram(text):
        rep.err(name, '缺少图示块 <div class="dg">')
    if is_appendix and CONFIG["appendix_requires_diagram"] and not has_diagram(text):
        rep.err(name, '缺少图示块 <div class="dg">')

    # 5. 固定结构（含已登记的变体）
    if not (is_appendix and CONFIG["appendix_skips_structure"]):
        secs = sections(text)
        allowed_missing = CONFIG["structure_variants"].get(num, {}).get("allow_missing", [])
        for need in CONFIG["required_sections"]:
            if need in secs:
                if need in allowed_missing:
                    rep.warn(name, f"结构变体声明 `{need}` 可缺省，此处出现了多余小节")
            elif need not in allowed_missing:
                rep.err(name, f"缺少 `## {need}` 小节")

    # 6. 零真实代码
    for pattern, desc in CONFIG["code_smells"]:
        for mm in re.finditer(pattern, text, flags=re.M):
            line_no = text[: mm.start()].count("\n") + 1
            rep.err(name, f"第 {line_no} 行疑似可运行代码（{desc}）：{mm.group(0).strip()}")

    # 7. 代码块语言标记白名单
    for mm in re.finditer(r"^```([^\s`]*)\s*$", text, flags=re.M):
        lang = mm.group(1)
        if lang not in CONFIG["allowed_code_langs"]:
            line_no = text[: mm.start()].count("\n") + 1
            rep.err(name, f"第 {line_no} 行代码块语言为 `{lang}`，只允许 {CONFIG['allowed_code_langs']}")

    # 8. 无内联样式 + 图示类名白名单
    for mm in re.finditer(r'style\s*=\s*"', text):
        line_no = text[: mm.start()].count("\n") + 1
        rep.err(name, f"第 {line_no} 行出现内联 style，图示必须用预定义类名")
    for mm in re.finditer(r'class="([^"]+)"', text):
        for cls in mm.group(1).split():
            if cls.startswith("dg") and cls not in CONFIG["allowed_dg_classes"]:
                rep.err(name, f"使用了未定义的图示类名 `{cls}`")

    # 9. 跨章口径
    for pattern, why in CONFIG["bad_phrases"]:
        mm = re.search(pattern, text)
        if mm:
            rep.err(name, f"出现 `{mm.group(0)}`（{why}）")

    return text


def check_counts(rep):
    """`### 名称（N 条）` 声明的条数必须与紧随其后的编号条目数一致。"""
    for spec in CONFIG["count_checks"]:
        path = CONTENT / spec["file"]
        if not path.exists():
            rep.err(spec["file"], "文件不存在")
            continue
        text = path.read_text(encoding="utf-8")
        total = declared_blocks = 0
        for m in re.finditer(spec["header_pattern"], text, flags=re.M):
            title, declared = m.group(1), int(m.group(2))
            rest = text[m.end():]
            nxt = re.search(r"^###\s", rest, flags=re.M)
            block = rest[: nxt.start()] if nxt else rest
            actual = len(re.findall(spec["item_pattern"], block, flags=re.M))
            total += declared
            declared_blocks += 1
            if actual != declared:
                rep.err(spec["file"], f"小节「{title}」标注 {declared} 条，实际列出 {actual} 条")
        if declared_blocks == 0:
            rep.err(spec["file"], "未找到任何带条数声明的小节")
        elif "declared_total" in spec and total != spec["declared_total"]:
            rep.err(spec["file"], f"各小节条数之和为 {total}，与声明的 {spec['declared_total']} 条不符")


def check_sequence(rep):
    """章节编号必须连续，且声明的附录都要有对应文件。"""
    nums = sorted(p.name.split("-")[0] for p in CONTENT.glob("*.md"))
    body = [n for n in nums if n.isdigit()]
    expect = [f"{i:02d}" for i in range(1, len(body) + 1)]
    if body != expect:
        rep.err("content/", f"正文章节编号不连续：实际 {body}")
    for ap in CONFIG["appendix_ids"]:
        if ap not in nums:
            rep.err("content/", f"缺少附录 {ap}")


def main():
    rep = Report()
    files = sorted(CONTENT.glob("*.md"))
    if not files:
        print("content/ 下没有 Markdown 文件")
        return 1

    total = 0
    for f in files:
        check_file(f, rep)
        if f.name.split("-")[0].isdigit():
            total += cn_chars(f.read_text(encoding="utf-8"))

    check_counts(rep)
    check_sequence(rep)

    body = [r for r in rep.rows if r[0].isdigit()]
    body_nums = {b[0] for b in body}
    print("=" * 62)
    print(f"章节 {len(rep.rows)} 个（正文 {len(body)} + 附录 {len(rep.rows) - len(body)}）"
          f"　正文合计 {total} 汉字　平均 {total // max(len(body), 1)} 字/章")
    print("=" * 62)
    for num, n, name in sorted(rep.rows):
        short = num in body_nums and n < CONFIG["min_chars"]
        print(f"  {num:>3}  {n:>6} 字  {name}{'  ← 偏短' if short else ''}")

    for line in rep.warns:
        print(line)
    if rep.errors:
        print()
        for line in rep.errors:
            print(line)
        print(f"\n结果：{len(rep.errors)} 项不合格，{len(rep.warns)} 项提醒")
        return 1

    print(f"\n结果：全部通过（{len(rep.warns)} 项提醒）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
